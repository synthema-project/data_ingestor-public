from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request
from pydantic import BaseModel
from typing import Dict, List, Union
from models import DatasetSchema, NewDataset, RemoveDatasetObject, NodeDatasetInfo
from database import create_db_and_tables, get_session
from utils import save_dataframe_as_csv, save_dataset_to_database, get_schema_from_database, remove_dataset_from_db, validate_data, csv_to_json_dict, replace_none_with_nan,save_node_dataset_info#,convert_np_to_native, 
#check_schema_dataset,
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
ANNOTATION_ENDPOINT =  "https://data-annotation.k8s.synthema.rid-intrasoft.eu/schema"
CATALOGUE_ENDPOINT =  "https://data-catalogue.k8s.synthema.rid-intrasoft.eu/metadata"
#CATALOGUE_ENDPOINT = "http://data-catalogue-service.synthema-dev:83/metadata" 

LOCAL_DATASETS_DIR = "/app/datasets"
local_datasets = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/dataset", tags=["data-ingestion"])
#async def upload_dataset(node: str = Form(...), disease: str = Form(...),local_datasets_dir: str = Form(default="/app/datasets"), file: UploadFile = File(...), session: Session = Depends(get_session)): #local_datasets_dir: str = Form(default="/app/datasets")
async def upload_dataset(node: str, disease: str,local_datasets_dir: str = Form(default="/app/datasets"), file: UploadFile = File(...), session: Session = Depends(get_session)):    
    if file.filename.endswith(".csv"):
        print('CSV CONTENT')
        csv_content = await file.read()
        print('DATAFRAME')
        dataframe = pd.read_csv(io.StringIO(csv_content.decode("latin1")), sep=';')
        print('CSV FILEPATH')
        csv_file_path = f"{local_datasets_dir}/{uuid.uuid4()}.csv"
        print('TOCSV')
        dataframe.to_csv(csv_file_path, index=False)
        print('CSVFILEPATH', csv_file_path)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{ANNOTATION_ENDPOINT}/{disease}")
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
                data_dict = csv_to_json_dict(csv_file_path=csv_file_path, schema=schema)
                print('DATADICT')
                validate_data(data_dict=data_dict, schema=schema)
                print('VALIDATE')
                iid = str(uuid.uuid4()) #int(uuid.uuid4())#str(uuid.uuid4())
                print('IID')
                filename = f"{disease}_{node}_{iid}.csv"
                print('FILENAME')
                filepath = save_dataframe_as_csv(dataframe, filename, node, savepath=local_datasets_dir)
                print('FILEPATH')
                local_datasets[filename] = filepath
                print(filepath)
                print(filename)
                os.remove(csv_file_path)
                print('REMOVE')
                #node_dataset = NodeDatasetInfo(id=iid, node=node, path=filepath, disease=disease)
                node_dataset = NodeDatasetInfo(id=iid, node=node, path=filepath, disease=disease)
                print('nodedatasetinfo')
                print(NodeDatasetInfo)
                #save_node_dataset_info(session, node_dataset)
                print('NODEDATASET')

                logger.info(f"Sending POST request to: {CATALOGUE_ENDPOINT}")
                logger.info(f"Payload: {node_dataset.model_dump()}")  # Log payload data
                
                try:
                    response = await client.post(CATALOGUE_ENDPOINT, json=node_dataset.model_dump()) #node_dataset.dict() .model_dump()
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

                return {"message": "Dataset uploaded and validated successfully"}
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail="Error processing file")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

#@app.delete("/dataset/all", tags=["data-ingestion"])
#async def remove_dataset_vecchia(removedatasetobject: RemoveDatasetObject, request: Request, session: Session = Depends(get_session)):
#    logging.info(f"Received request: {await request.json()}")
#    async with httpx.AsyncClient() as client:
#        try:
#    #        if remove_dataset_from_db(session, node=removedatasetobject.node, disease=removedatasetobject.disease, path=removedatasetobject.path):
#    #            #print('IF REMOVE DATASET FROM DB IS TRUE')
#            os.remove(removedatasetobject.path)
#    #            #return {"message": "Dataset removed successfully"}
#            print("message: Dataset removed successfully")
#    #        else:
#    #            #print('IF REMOVE DATASET FROM DB IS FALSE')
#    #            raise HTTPException(status_code=404, detail="Dataset not found in local storage")#

#            response = await client.request("DELETE",
#                                            CATALOGUE_ENDPOINT,
#                                            json=removedatasetobject.dict(),
#                                            headers={"Content-Type": "application/json"})
#            response.raise_for_status()

#            return {"message": "Dataset removed successfully from both database and local storage"}
#            #print('RESPONSE:', response.raise_for_status())
#            #print('metadata removed')
#            #print(removedatasetobject)
#            #print(removedatasetobject.path)

#            #if remove_dataset_from_db(session, node=removedatasetobject.node, disease=removedatasetobject.disease, path=removedatasetobject.path):
#            #    print('IF REMOVE DATASET FROM DB IS TRUE')
#            #    os.remove(removedatasetobject.path)
#            #    return {"message": "Dataset removed successfully"}
#            ##else:
#            #    print('IF REMOVE DATASET FROM DB IS FALSE')
#            #    raise HTTPException(status_code=404, detail="Dataset not found in local storage")

#        except httpx.HTTPStatusError as exc:
#            print('EXCEPT 1')
#            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json())
#        except Exception as e:
#            print('EXCEPT 2')
#            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/dataset/a", tags=["data-ingestion"])
async def remove_dataset_2(
    node:str, disease:str, path:str,
    #removedatasetobject: RemoveDatasetObject,
    request: Request,
    session: Session = Depends(get_session)
):
    logging.info(f"Received request: {await request.json()}")
    removdatasetobject = RemoveDatasetObject(node, disease, path)
    #print(removedatasetobject.disease)
    #print(removedatasetobject.node)
    #print(removedatasetobject.path)
    try:
        # Remove the file from local storage
        if os.path.exists(removedatasetobject.path):
            os.remove(removedatasetobject.path)
            logging.info(f"File {removedatasetobject.path} successfully removed.")
        else:
            logging.warning(f"File {removedatasetobject.path} not found.")
            raise HTTPException(status_code=404, detail="File not found in local storage")

        # Notify external service
        print('ORA RIMUOVO IL FILE DAL DATABASE DEI METADATA')
        async with httpx.AsyncClient() as client:
            #response = await client.delete(
            #    CATALOGUE_ENDPOINT,
            #    json=removedatasetobject.dict(),
            #    headers={"Content-Type": "application/json"}
            #)
            URL = f"{CATALOGUE_ENDPOINT}/metadata"
            response = await client.request("DELETE", URL, json=removedatasetobject.model_dump()) #.dict()
            
            response.raise_for_status()
            logging.info("External service notified successfully.")

        # Return success response
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

@app.delete("/dataset", tags=["data-ingestion"])
async def remove_dataset(
    node: str,
    disease: str,
    path: str,
    request: Request,
    session: Session = Depends(get_session)
):
    print('ENTER DELETE')
    #logging.info(f"Received request: {await request.json()}")
    logging.info(f"Received query parameters: node={node}, disease={disease}, path={path}")
    removedatasetobject = RemoveDatasetObject(node=node, disease=disease, path=path)
    print('REMOVEDATASETOBJECT')
    try:
        # Remove the file from local storage
        if os.path.exists(removedatasetobject.path):
            print('REMOVE')
            os.remove(removedatasetobject.path)
            logging.info(f"File {removedatasetobject.path} successfully removed.")
        else:
            logging.warning(f"File {removedatasetobject.path} not found.")
            raise HTTPException(status_code=404, detail="File not found in local storage")

        # Notify external service
        logging.info("Notifying external service to remove metadata.")
        print('REMOVE METADATA')
        async with httpx.AsyncClient() as client:
            url = f"{CATALOGUE_ENDPOINT}/metadata"
            response = await client.delete(
                CATALOGUE_ENDPOINT,#url,
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

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=82)
