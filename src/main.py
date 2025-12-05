from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request
from pydantic import BaseModel
from typing import Dict, List, Union
from models import DatasetSchema, NewDataset, RemoveDatasetObject, NodeDatasetInfo
from database import create_db_and_tables, get_session
from utils import save_dataframe_as_csv, save_dataset_to_database, get_schema_from_database, remove_dataset_from_db, validate_data, csv_to_json_dict, replace_none_with_nan,save_node_dataset_info#,convert_np_to_native, 
#check_schema_dataset,
from utils import save_dataframe_to_minio, remove_dataset_from_minio, get_dataset_from_minio
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

#ANNOTATION_ENDPOINT =  "http://data-annotation-service.synthema-dev/schema" 
#CATALOGUE_ENDPOINT = "http://data-catalogue-service.synthema-dev:83/metadata" 

NODE_NAME = "NODE1" #os.getenv("NODE_NAME")  # NEW
ANNOTATION_ENDPOINT =  "https://data-annotation.k8s.synthema.rid-intrasoft.eu/schema"
CATALOGUE_ENDPOINT =  "https://data-catalogue.k8s.synthema.rid-intrasoft.eu/metadata"
MINIO_ENDPOINT = "obstorageapi.k8s.synthema.rid-intrasoft.eu/"

LOCAL_DATASETS_DIR = "/app/datasets"
local_datasets_dir = "/app/datasets"
local_datasets = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/dataset", tags=["data-ingestion"])
#async def upload_dataset(node: str = Form(...), disease: str = Form(...),local_datasets_dir: str = Form(default="/app/datasets"), file: UploadFile = File(...), session: Session = Depends(get_session)): #local_datasets_dir: str = Form(default="/app/datasets")
async def upload_dataset(
    #node: str, 
    #use_case: str, 
    use_case: str = Form(...),
    #disease: str,
    #local_datasets_dir: str = Form(default="/app/datasets"), 
    file: UploadFile = File(...), 
    session: Session = Depends(get_session),  
    #user = Depends(get_current_user)
    ##current_user: UserClaims = Depends(require_authentication)
    ):  

    node = NODE_NAME
        
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
        
    if file.filename.endswith(".csv"):
        
        print('CSV CONTENT')
        csv_content = await file.read()
        print('DATAFRAME')
        dataframe = pd.read_csv(io.StringIO(csv_content.decode("latin1")), sep=';')
        print(dataframe)
        print(len(dataframe))
        print('CSV FILEPATH')
        
        ##csv_file_path = f"{local_datasets_dir}/{uuid.uuid4()}.csv"
        ##print('TOCSV')
        ##dataframe.to_csv(csv_file_path, index=False)
        ##print('CSVFILEPATH', csv_file_path)
        
        async with httpx.AsyncClient() as client:
            try:
                #response = await client.get(f"{ANNOTATION_ENDPOINT}/{disease}")
                response = await client.get(f"{ANNOTATION_ENDPOINT}/{use_case}")
                #response = await requests.get(f"{ANNOTATION_ENDPOINT}/{disease}",allow_redirects=True)
                print(f"Annotation response: {response.status_code} - {response.text}")
                print('RESPONSE')
                #if response.status_code == 308:
                #    print(f"Redirected to: {response.headers.get('location')}")
                
                if response.status_code != 200:
                    raise Exception(f"Schema service error: {response.status_code}")
                    #raise HTTPException(status_code=404, detail="Schema not found")
                
                print('SCHEMA1')
                schema = response.json()["schema"]
                print(schema)
                print('SCHEMA')
                
                #data_dict = csv_to_json_dict(csv_file_path=csv_file_path, schema=schema)
                data_dict = csv_to_json_dict(csv_file_path=dataframe, schema=schema)
                print('DATADICT')
                validate_data(data_dict=data_dict, schema=schema)
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
                    schema=schema,
                )
                print('nodedatasetinfo')
                print(NodeDatasetInfo)
                #save_node_dataset_info(session, node_dataset)
                print('NODEDATASET')

                logger.info(f"Sending POST request to: {CATALOGUE_ENDPOINT}")
                logger.info(f"Payload: {node_dataset.model_dump()}")  # Log payload data
                
                try:
                    # Send metadata to catalogue
                    response = await client.post(CATALOGUE_ENDPOINT, 
                                                 json=node_dataset.model_dump()
                                                ) #node_dataset.dict() .model_dump()
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

@app.delete("/dataset", tags=["data-ingestion"])
async def delete_dataset(filename: str):
    """
    Remove a dataset from MinIO, notify data-catalogue to remove metadata
    and remove the dataset reference from use-cases.
    """

    # 1) Remove from MinIO
    success = remove_dataset_from_minio(filename)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found in MinIO")
    logging.info(f"Deleted {filename} from MinIO")

    # 2) Build the SAME PATH stored in UseCase.datasets (full minio url)
    # Use configured MINIO_ENDPOINT if present, otherwise just use filename
    if MINIO_ENDPOINT:
        dataset_full_url = f"{MINIO_ENDPOINT.rstrip('/')}/{filename.lstrip('/')}"
    else:
        dataset_full_url = filename

    # 3) Notify catalogue to remove metadata (existing endpoint expects "path")
    catalogue_metadata_url = CATALOGUE_ENDPOINT  # e.g. "https://.../metadata"
    # 4) Use-case removal endpoint expects query param named "dataset_path"
    catalogue_remove_usecase_url = f"{CATALOGUE_ENDPOINT.rstrip('/')}/usecases/dataset"

    async with httpx.AsyncClient() as client:
        # delete metadata entry (this removes NodeDatasetInfo row)
        try:
            resp_meta = await client.delete(catalogue_metadata_url, params={"path": filename})
            resp_meta.raise_for_status()
            logging.info("Metadata deleted from catalogue")
        except httpx.HTTPStatusError as exc:
            # metadata deletion failed — log and raise.
            logging.error(f"Failed deleting metadata: {exc.response.status_code} {exc.response.text}")
            raise HTTPException(status_code=500, detail="Failed to delete metadata from catalogue")
        except Exception as exc:
            logging.exception("Error contacting data-catalogue for metadata deletion")
            raise HTTPException(status_code=500, detail="Error contacting data-catalogue")

        # delete dataset reference from use-cases (pass dataset_path param)
        try:
            resp_uc = await client.delete(
                catalogue_remove_usecase_url,
                params={"dataset_path": dataset_full_url}   # <-- correct param name
            )
            # treat 404 as non-fatal (maybe entry already removed), but log it
            if resp_uc.status_code in (200, 204):
                logging.info("Dataset removed from use-cases")
            elif resp_uc.status_code == 404:
                logging.info("Dataset not found in use-cases (OK).")
            else:
                # unexpected response - warn and surface to caller
                logging.warning(f"Use-case removal returned {resp_uc.status_code}: {resp_uc.text}")
                # optionally raise to make caller aware:
                raise HTTPException(status_code=500, detail="Failed removing dataset from use-cases")
        except HTTPException:
            # re-raise HTTPExceptions we've created
            raise
        except Exception as exc:
            logging.exception("Error removing dataset from use-cases")
            raise HTTPException(status_code=500, detail="Error removing dataset from use-cases")

    return {"message": "Dataset removed successfully"}

'''
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
    uvicorn.run(app, host="0.0.0.0", port=82)



























