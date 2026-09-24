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


app = FastAPI()


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


async def _register_in_catalogue(payload: dict) -> None:
    """POST a NodeDatasetInfo payload to the data catalogue (forwarding a token)."""
    headers = {}
    if CATALOGUE_TOKEN:
        headers["Authorization"] = f"Bearer {CATALOGUE_TOKEN}"
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(CATALOGUE_ENDPOINT, json=payload, headers=headers, timeout=30)
        if response.status_code not in (200, 201):
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Catalogue registration failed for {payload.get('path')}: {response.text}",
            )


@app.post("/dataset/partitioned", tags=["data-ingestion"])
async def upload_dataset_partitioned(
    use_case: str = Form(...),
    metadata: str = Form(...),
    dataset_meta: str = Form(...),
    file: UploadFile = File(...),
    node: str = Form(None),
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
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    # Validate the two JSON payloads up front.
    try:
        dcat_metadata = DatasetMetadata(**json.loads(metadata)).model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid DCAT-AP metadata: {e}")
    try:
        dataset_meta_dict = json.loads(dataset_meta)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid dataset_meta JSON: {e}")

    # Prod: one ingestor per org → node from env. Dev: optional `node` form field
    # lets a single ingestor register several nodes (e.g. ICH and UMCU).
    node = node or NODE_NAME
    raw = await file.read()
    dataframe = _read_csv_autodetect(raw)
    if dataframe.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV has no rows")

    partitions = _split_train_val_test(dataframe)

    # 1. Upload the DatasetMeta schema JSON so the FL client can hydrate it.
    meta_object = f"{use_case}_{node}_meta.json"
    save_bytes_to_minio(
        json.dumps(dataset_meta_dict).encode("utf-8"), meta_object, "application/json"
    )

    # 2. Upload each partition CSV and register it in the catalogue.
    uploaded = {}
    for part_name, part_df in partitions.items():
        object_name = f"{use_case}_{node}_{part_name}.csv"
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
            }
        )

    # 3. Register the schema JSON too, so its URL travels in the node's dataset list.
    await _register_in_catalogue(
        {
            "node": node,
            "path": meta_object,
            "use_case": use_case,
            "num_records": 0,
            "num_features": 0,
            "dataset_metadata": dcat_metadata,
        }
    )

    return {
        "message": "Dataset partitioned, uploaded and registered successfully",
        "node": node,
        "use_case": use_case,
        "partitions": uploaded,
        "dataset_meta": meta_object,
        "num_records": int(len(dataframe)),
    }

@app.post("/dataset", tags=["data-ingestion"])
#async def upload_dataset(node: str = Form(...), disease: str = Form(...),local_datasets_dir: str = Form(default="/app/datasets"), file: UploadFile = File(...), session: Session = Depends(get_session)): #local_datasets_dir: str = Form(default="/app/datasets")
async def upload_dataset(
    #node: str, 
    #use_case: str, 
    use_case: str = Form(...),
    metadata: str = Form(...),
    #disease: str,
    #local_datasets_dir: str = Form(default="/app/datasets"), 
    file: UploadFile = File(...), 
    session: Session = Depends(get_session),  
    #user = Depends(get_current_user)
    ##current_user: UserClaims = Depends(require_authentication)
    ):  

    try:
        metadata_dict = json.loads(metadata)
        metadata_obj = DatasetMetadata(**metadata_dict)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metadata format: {str(e)}"
        )

    node = NODE_NAME
        
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
        
    if file.filename.endswith(".csv"):
        
        print('CSV CONTENT')
        csv_content = await file.read()
        print('DATAFRAME')
        dataframe = _read_csv_autodetect(csv_content)
        print(dataframe)
        print(len(dataframe))
        print('CSV FILEPATH')
        
        ##csv_file_path = f"{local_datasets_dir}/{uuid.uuid4()}.csv"
        ##print('TOCSV')
        ##dataframe.to_csv(csv_file_path, index=False)
        ##print('CSVFILEPATH', csv_file_path)
        
        async with httpx.AsyncClient() as client:
            try:
                ##response = await client.get(f"{ANNOTATION_ENDPOINT}/{use_case}")
                ##print(f"Annotation response: {response.status_code} - {response.text}")
                ##print('RESPONSE')
                
                ##if response.status_code != 200:
                ##    raise Exception(f"Schema service error: {response.status_code}")
                
                ##print('SCHEMA1')
                ##schema = response.json()["schema"]
                ##print(schema)
                ##print('SCHEMA')
                
                #data_dict = csv_to_json_dict(csv_file_path=csv_file_path, schema=schema)
                data_dict = csv_to_json_dict(csv_file_path=dataframe)#, schema=schema)
                print('DATADICT')
                ##flat_schema = flatten_schema(schema)
                ## commented for test purposes, then restore it
                ##########validate_data(data_dict, flat_schema)
                #validate_data(data_dict=data_dict, schema=schema)
                print('VALIDATE')
                
                iid = str(uuid.uuid4()) #int(uuid.uuid4())#str(uuid.uuid4())
                print('IID')
                #filename = f"{disease}_{node}_{iid}.csv"
                filename = f"{use_case}_{node}_{iid}.csv"
                print('FILENAME')
                ##filepath = save_dataframe_as_csv(dataframe, filename, node, savepath=local_datasets_dir)
                minio_filepath = save_dataframe_to_minio(dataframe, filename)#, node)
                #minio_filepath = save_dataframe_to_minio(dataframe, filename, NODE_NAME)
                print('FILEPATH')
                local_datasets[filename] = minio_filepath
                ##print(minio_filepath)
                print(filename)
                ##os.remove(csv_file_path)
                print('REMOVE')

                num_records = len(dataframe)
                num_features = len(dataframe.columns)
                
                #node_dataset = NodeDatasetInfo(id=iid, node=node, path=filepath, disease=disease)
                node_dataset = NodeDatasetInfo(
                    id=iid, 
                    node=node, #NODE_NAME, #node
                    path=minio_filepath, 
                    #disease=disease #
                    use_case=use_case,
                    num_records=num_records,
                    num_features=num_features,
                    ##data_schema=schema,
                    dataset_metadata=metadata_dict,
                )
                print('nodedatasetinfo')
                print(NodeDatasetInfo)
                #save_node_dataset_info(session, node_dataset)
                print('NODEDATASET')

                logger.info(f"Sending POST request to: {CATALOGUE_ENDPOINT}")
                #logger.info(f"Payload: {node_dataset.model_dump()}")  # Log payload data

                payload = node_dataset.model_dump()
                payload["dataset_metadata"] = metadata_obj.model_dump()
                
                
                try:
                    # Send metadata to catalogue
                    #response = await client.post(CATALOGUE_ENDPOINT, 
                    #                             json=node_dataset.model_dump()
                    #                            ) #node_dataset.dict() .model_dump()
                    response = await client.post(
                                                CATALOGUE_ENDPOINT,
                                                json=payload
                                                )
                    print('CATALOGUEENDPOINT')
                    print('CATALOGUEENDPOINT POST RESPONSE', response.status_code)
                    #response.raise_for_status()

                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error when communicating with {CATALOGUE_ENDPOINT}: {e.response.text}")
                    raise HTTPException(status_code=e.response.status_code, detail=f"Error saving metadata: {e.response.text}")

                except httpx.RequestError as e:
                    logger.error(f"Request error when connecting to {CATALOGUE_ENDPOINT}: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error connecting to data-catalogue: {str(e)}")

                except Exception as e:
                    logger.exception("Unexpected error during communication with data-catalogue")
                    raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

                #new_dataset = DatasetSchema(disease=disease, data=json.dumps(schema))
                #print('NEWDATASET')
                #save_dataset_to_database(session, new_dataset)
                #print('SAVETOCATALOGUE')

                return {"message": "Dataset uploaded and validated successfully", "filename": filename}
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail="Error processing file")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

'''
@app.delete("/dataset", tags=["data-ingestion"])
async def remove_dataset(
    node: str,
    disease: str,
    filename: str,
    #path: str,
    #request: Request,
    session: Session = Depends(get_session)
):
    print('ENTER DELETE')
    #logging.info(f"Received request: {await request.json()}")
    logging.info(f"Received query parameters: node={node}, disease={disease}, path={filename}")
    ##removedatasetobject = RemoveDatasetObject(node=node, disease=disease, path=path)
    removedatasetobject = RemoveDatasetObject(node=node, disease=disease, path=filename)
    print('REMOVEDATASETOBJECT')
    try:
        success = remove_dataset_from_minio(node, filename)

        if not success:
            raise HTTPException(status_code=404, detail='Dataset not found in MinIO')

        
        # Notify external service
        logging.info("Notifying external service to remove metadata.")
        print('REMOVE METADATA')
        async with httpx.AsyncClient() as client:
            url = f"{CATALOGUE_ENDPOINT}/metadata"
            response = await client.delete(
                CATALOGUE_ENDPOINT,#url,
                #json={"node": node, "disease": disease, "path": path},
                params=removedatasetobject.model_dump(),
                #content=json.dumps(removedatasetobject.model_dump()),
                #params={"node": node, "disease": disease, "path": path},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logging.info("External service notified successfully.")

        return {"message": "Dataset removed successfully from both database and local storage"}

    except httpx.HTTPStatusError as exc:
        logging.error(f"External service error: {exc.response.status_code} - {exc.response.text}")
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json())

    except FileNotFoundError:
        logging.error(f"File {removedatasetobject.path} not found.")
        raise HTTPException(status_code=404, detail="File not found in local storage")

    except Exception as e:
        logging.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An internal server error occurred")
'''


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


















































