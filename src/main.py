from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request
from pydantic import BaseModel
from typing import Dict, List, Union
from models import DatasetSchema, NewDataset, RemoveDatasetObject, NodeDatasetInfo
from database import create_db_and_tables, get_session
from utils import save_dataframe_as_csv, save_dataset_to_database, get_schema_from_database, remove_dataset_from_db, validate_data, csv_to_json_dict, replace_none_with_nan#,convert_np_to_native
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

app = FastAPI()

ANNOTATION_ENDPOINT = "https://data-annotation.k8s.synthema.rid-intrasoft.eu:80/schema"#/schema" #"http://localhost:8001/schema"
#ANNOTATION_ENDPOINT = "https://data-annotation-service:80/schema"
CATALOGUE_ENDPOINT = "https://data-catalogue.k8s.synthema.rid-intrasoft.eu:83/metadata" #"http://localhost:8003/metadata"

# Create a secure SSL contex
ssl_context = ssl.create_default_context()
#ssl_context.set_ciphers('DEFAULT:@SECLEVEL=1')
#ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  # Disabling older versions

current_dir = Path(__file__).resolve().parent

LOCAL_DATASETS_DIR = current_dir / "tests" / "example_data" #"/app/data/dataset/local_datasets" #"/mnt/c/users/lenovo/desktop/data-ingestion/local_datasets"
#LOCAL_DATASETS_DIR = "/app/data/central_node.db"
local_datasets = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/dataset", tags=["data-ingestion"])
async def upload_dataset(node: str = Form(...), disease: str = Form(...), file: UploadFile = File(...), session: Session = Depends(get_session)):
    if file.filename.endswith(".csv"):
        print('CSV CONTENT')
        csv_content = await file.read()
        print('DATAFRAME')
        dataframe = pd.read_csv(io.StringIO(csv_content.decode("latin1")), sep=';')
        print('CSV FILEPATH')
        csv_file_path = f"{LOCAL_DATASETS_DIR}/{uuid.uuid4()}.csv"
        print('TOCSV')
        dataframe.to_csv(csv_file_path, index=False)
        print('CSVFILEPATH', csv_file_path)
        async with httpx.AsyncClient(http2=False, verify=ssl_context) as client:
            try:
                response = await client.get(f"{ANNOTATION_ENDPOINT}/{disease}")
                print(f"Annotation response: {response.status_code} - {response.text}")
                #response.raise_for_status()
                print('RESPONSE')
                if response.status_code == 308:
                    print(f"Redirected to: {response.headers.get('location')}")
                if response.status_code != 200:
                    raise HTTPException(status_code=404, detail="Schema not found")
                print('SCHEMA1')
                schema = response.json()["features"]#["schema"]
                print('SCHEMA')
                data_dict = csv_to_json_dict(csv_file_path=csv_file_path, schema=schema)
                print('DATADICT')
                validate_data(data_dict=data_dict, schema=schema)
                print('VALIDATE')
                iid = str(uuid.uuid4())
                filename = f"{disease}_{node}_{iid}.csv"
                filepath = save_dataframe_as_csv(dataframe, filename, node)
                local_datasets[filename] = filepath
                os.remove(csv_file_path)
                node_dataset = NodeDatasetInfo(node=node, path=filepath, disease=disease)
                try:
                    response = await client.post(CATALOGUE_ENDPOINT, json=node_dataset.dict())
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    raise HTTPException(status_code=e.response.status_code,
                                        detail=f"Error saving metadata: {e.response.text}")
                except httpx.RequestError as e:
                    raise HTTPException(status_code=500, detail=f"Error connecting to data-catalogue: {str(e)}")

                new_dataset = DatasetSchema(disease=disease, data=json.dumps(schema))
                save_dataset_to_database(session, new_dataset)

                return {"message": "Dataset uploaded and validated successfully"}
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail="Error processing file")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

@app.delete("/dataset", tags=["data-ingestion"])
async def remove_dataset(removedatasetobject: RemoveDatasetObject, request: Request, session: Session = Depends(get_session)):
    logging.info(f"Received request: {await request.json()}")
    async with httpx.AsyncClient() as client:
        try:
            if remove_dataset_from_db(session, node=removedatasetobject.node, disease=removedatasetobject.disease, path=removedatasetobject.path):
                #print('IF REMOVE DATASET FROM DB IS TRUE')
                os.remove(removedatasetobject.path)
                #return {"message": "Dataset removed successfully"}
                print("message: Dataset removed successfully")
            else:
                #print('IF REMOVE DATASET FROM DB IS FALSE')
                raise HTTPException(status_code=404, detail="Dataset not found in local storage")

            response = await client.request("DELETE",
                                            CATALOGUE_ENDPOINT,
                                            json=removedatasetobject.dict(),
                                            headers={"Content-Type": "application/json"})
            response.raise_for_status()

            return {"message": "Dataset removed successfully from both database and local storage"}
            #print('RESPONSE:', response.raise_for_status())
            #print('metadata removed')
            #print(removedatasetobject)
            #print(removedatasetobject.path)

            #if remove_dataset_from_db(session, node=removedatasetobject.node, disease=removedatasetobject.disease, path=removedatasetobject.path):
            #    print('IF REMOVE DATASET FROM DB IS TRUE')
            #    os.remove(removedatasetobject.path)
            #    return {"message": "Dataset removed successfully"}
            ##else:
            #    print('IF REMOVE DATASET FROM DB IS FALSE')
            #    raise HTTPException(status_code=404, detail="Dataset not found in local storage")

        except httpx.HTTPStatusError as exc:
            print('EXCEPT 1')
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json())
        except Exception as e:
            print('EXCEPT 2')
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=82)
