from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Union
from models import DatasetSchema, NewDataset, RemoveDatasetObject, NodeDatasetInfo, DatasetMetadata
from database import create_db_and_tables, get_session
from utils import save_dataframe_as_csv, save_dataset_to_database, get_schema_from_database, remove_dataset_from_db, validate_data, csv_to_json_dict, replace_none_with_nan,save_node_dataset_info#,convert_np_to_native,
#check_schema_dataset,
from utils import save_dataframe_to_minio, remove_dataset_from_minio, get_dataset_from_minio, flatten_schema, save_bytes_to_minio
from auth import UserClaims, require_authentication
from pathlib import Path
import uvicorn
import os
import json
import uuid
import httpx
import ssl
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
import io
import logging
import requests


app = FastAPI(dependencies=[Depends(require_authentication)])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

#ANNOTATION_ENDPOINT =  "http://data-annotation-service.synthema-dev/schema"
#CATALOGUE_ENDPOINT = "http://data-catalogue-service.synthema-dev:83/metadata"

from config import settings

NODE_NAME = settings.NODE_NAME  # this ingestor instance's node/org name
ANNOTATION_ENDPOINT = settings.ANNOTATION_ENDPOINT
CATALOGUE_ENDPOINT = settings.CATALOGUE_ENDPOINT
CAT_ENDPOINT = CATALOGUE_ENDPOINT.replace("/metadata", "/")
MINIO_ENDPOINT = settings.MINIO_ENDPOINT
# Optional bearer token forwarded to the (Keycloak-protected) data catalogue.
CATALOGUE_TOKEN = settings.CATALOGUE_TOKEN or None

LOCAL_DATASETS_DIR = "/app/datasets"
local_datasets_dir = "/app/datasets"
local_datasets = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    from storage import ensure_bucket
    ensure_bucket()
    from database import migrate_dataset_partitions
    migrate_dataset_partitions()


from csv_input import read_csv_input as _read_csv_autodetect


def _split_train_val_test(df: pd.DataFrame, random_state: int = 42):
    """Shuffle and split 60/20/20 (train/val/test), matching the MSI simulation."""
    shuffled = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    n = len(shuffled)
    train_end = int(0.6 * n)
    val_end = train_end + int(0.2 * n)
    return {
        "train": shuffled.iloc[:train_end].reset_index(drop=True),
        "val": shuffled.iloc[train_end:val_end].reset_index(drop=True),
        "test": shuffled.iloc[val_end:].reset_index(drop=True),
    }


async def _register_in_catalogue(payload: dict, authorization: str = "") -> None:
    """POST a NodeDatasetInfo payload to the data catalogue (forwarding a token)."""
    headers = {"Authorization": authorization} if authorization else {}
    if not authorization and CATALOGUE_TOKEN:
        headers["Authorization"] = f"Bearer {CATALOGUE_TOKEN}"
    async with httpx.AsyncClient() as client:
        response = await client.post(CATALOGUE_ENDPOINT, json=payload, headers=headers, timeout=30)
        if response.status_code not in (200, 201):
            raise HTTPException(
                status_code=response.status_code,
                detail="Catalogue registration failed",
            )


@app.post("/dataset/partitioned", tags=["data-ingestion"])
async def upload_dataset_partitioned(
    request: Request,
    use_case: str = Form(...),
    metadata: str = Form(...),
    dataset_meta: str = Form(None),
    configuration_version: str = Form(None),
    file: UploadFile = File(...),
    node: str = Form(None),
    current_user: UserClaims = Depends(require_authentication),
):
    """Ingest a full CSV: split 60/20/20, upload the partitions + the DatasetMeta
    schema JSON to MinIO, and register every object in the data catalogue.

    Form fields:
      * ``use_case``     - catalogue use-case string (e.g. ``AML-1``).
      * ``metadata``     - DCAT-AP governance metadata (JSON) → catalogue ``dataset_metadata``.
      * ``dataset_meta`` - model DatasetMeta variable schema (JSON) → uploaded to MinIO
                           and consumed by the FL client for preprocessing.
      * ``file``         - the full dataset CSV.

    The node/org name is taken from this ingestor's ``NODE_NAME`` env.
    """
    if not current_user.has_role('Admin') and not any(
        role.rpartition(':')[0] == NODE_NAME for role in current_user.synthema_roles
    ):
        raise HTTPException(403, 'Your account does not belong to this ingestor node')
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    # Validate the two JSON payloads up front.
    try:
        dcat_metadata = DatasetMetadata(**json.loads(metadata)).model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid DCAT-AP metadata: {e}")
    # Resolve a centrally published, immutable metadata/evaluation pair.
    authorization = request.headers.get("Authorization", "")
    headers = {"Authorization": authorization} if authorization else ({"Authorization": f"Bearer {CATALOGUE_TOKEN}"} if CATALOGUE_TOKEN else {})
    async with httpx.AsyncClient() as client:
        response = await client.get(
            CATALOGUE_ENDPOINT.rsplit("/metadata", 1)[0] + f"/evaluation-configurations/{use_case}",
            params={"version": configuration_version} if configuration_version else {},
            headers=headers, timeout=30,
        )
        if response.status_code != 200:
            raise HTTPException(422, "Publish a valid central metadata/evaluation configuration before uploading data")
        configuration = response.json()
    dataset_meta_dict = configuration["documents"]["metadata"]
    evaluation_dict = configuration["documents"]["evaluation"]
    try:
        supplied_schema = json.loads(dataset_meta) if dataset_meta is not None else None
    except (ValueError, TypeError) as error:
        raise HTTPException(422, 'Invalid dataset_meta JSON') from error
    if supplied_schema is not None and supplied_schema != dataset_meta_dict:
        raise HTTPException(422, "Uploaded schema differs from the selected central configuration")
    if node and node != NODE_NAME:
        raise HTTPException(403, "Uploads must belong to this ingestor's configured node")
    node = NODE_NAME
    collection_id = str(uuid.uuid4())
    raw = await file.read()
    dataframe = _read_csv_autodetect(raw)
    if len(dataframe) < 5:
        raise HTTPException(422, "At least five rows are needed for nonempty train/val/test partitions")
    missing = {v["name"] for v in dataset_meta_dict["variables"]} - set(dataframe.columns)
    if missing:
        raise HTTPException(422, "Dataset is missing configured columns: " + ", ".join(sorted(missing)))

    partitions = _split_train_val_test(dataframe)

    # 1. Upload the DatasetMeta schema JSON so the FL client can hydrate it.
    meta_object = f"{use_case}_{node}_{collection_id}_meta.json"
    save_bytes_to_minio(
        json.dumps(dataset_meta_dict).encode("utf-8"), meta_object, "application/json"
    )

    # 2. Upload each partition CSV and register it in the catalogue.
    uploaded = {}
    for part_name, part_df in partitions.items():
        object_name = f"{use_case}_{node}_{collection_id}_{part_name}.csv"
        save_dataframe_to_minio(part_df, object_name)
        uploaded[part_name] = object_name
        await _register_in_catalogue(
            {
                "node": node,
                "path": object_name,
                "use_case": use_case,
                "num_records": int(len(part_df)),
                "num_features": int(len(part_df.columns)),
                "dataset_metadata": dcat_metadata,
                "dataset_role": part_name,
                "collection_id": collection_id,
                "configuration_version": configuration["version"],
                "dataset_meta": dataset_meta_dict,
                "evaluation_configuration": evaluation_dict,
            }, authorization
        )

    # 3. Register the schema JSON too, so its URL travels in the node's dataset list.
    await _register_in_catalogue(
        {
            "node": node,
            "path": meta_object,
            "use_case": use_case,
            "num_records": 0,
            "num_features": 0,
            "dataset_role": "schema",
            "collection_id": collection_id,
            "configuration_version": configuration["version"],
            "dataset_meta": dataset_meta_dict,
            "evaluation_configuration": evaluation_dict,
            "dataset_metadata": dcat_metadata,
        }, authorization
    )

    return {
        "message": "Dataset partitioned, uploaded and registered successfully",
        "node": node,
        "use_case": use_case,
        "partitions": uploaded,
        "collection_id": collection_id,
        "configuration_version": configuration["version"],
        "dataset_meta": meta_object,
        "num_records": int(len(dataframe)),
    }

@app.post("/dataset", tags=["data-ingestion"])
async def upload_dataset(request: Request, use_case: str = Form(...), metadata: str = Form(...),
                         file: UploadFile = File(...), configuration_version: str = Form(None),
                         current_user: UserClaims = Depends(require_authentication)):
    return await upload_dataset_partitioned(request=request, current_user=current_user, use_case=use_case, metadata=metadata,
        dataset_meta=None, configuration_version=configuration_version, file=file, node=None)





@app.delete("/dataset", tags=["data-ingestion"])
async def delete_dataset(
    filename: str,
    ##current_user: UserClaims = Depends(require_authentication)
):
    """
    Remove a dataset from MinIO and notify data-catalogue to remove metadata.
    """

    # Remove from MinIO
    success = remove_dataset_from_minio(filename)
    print('DATA REMOVED FROM MINIO')
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found in MinIO")

    # Notify catalogue that metadata must be deleted
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{CATALOGUE_ENDPOINT}",
            params={"path": filename}
        )
        response.raise_for_status()
        print('DATA REMOVED FROM CATALOGUE')

    return {"message": "Dataset removed successfully"}

'''
@app.delete("/dataset", tags=["data-ingestion"])
async def delete_dataset(filename: str):

    success = remove_dataset_from_minio(filename)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found in MinIO")

    dataset_full_url = f"obstorageapi.k8s.synthema.rid-intrasoft.eu/{filename}"

    async with httpx.AsyncClient() as client:

        # 1) Remove from use-cases FIRST
        resp_uc = await client.delete(
            #f"{CAT_ENDPOINT.rstrip('/')}/usecases/dataset",
            "https://data-catalogue.k8s.synthema.rid-intrasoft.eu/usecases/dataset",
            params={"dataset_path": dataset_full_url}
        )
        resp_uc.raise_for_status()

        # 2) Now remove metadata
        resp_meta = await client.delete(
            f"{CATALOGUE_ENDPOINT}",
            params={"path": filename}
        )
        resp_meta.raise_for_status()

    return {"message": "Dataset removed successfully"}


@app.get("/dataset", tags=["data-ingestion"])
async def get_dataset(
    node: str,
    disease: str,
    filename: str,
    #as_file: bool = Query(default=False, description="Return as downloadable CSV if True"),
):
    """
    Retrieve a dataset from MinIO.
    - If `as_file=False` → returns JSON records.
    - If `as_file=True` → returns downloadable CSV file.
    """
    try:
        dataframe = get_dataset_from_minio(node, filename)

        #if as_file:
        csv_buffer = io.StringIO()
        dataframe.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        return StreamingResponse(
                iter([csv_buffer.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

        # Default: return JSON
        #return {"filename": filename, "data": dataframe.to_dict(orient="records")}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dataset: {str(e)}")
'''
@app.get("/dataset", tags=["data-ingestion"])
async def get_dataset(
    filename: str,
    ##current_user: UserClaims = Depends(require_authentication)
):
    """
    Retrieve a dataset from MinIO as CSV.
    """

    dataframe = get_dataset_from_minio(filename)

    csv_buffer = io.StringIO()
    dataframe.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)


















































