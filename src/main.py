from fastapi import FastAPI, HTTPException, Body, File, UploadFile, Form, Request
from pydantic import BaseModel
from typing import Dict, List, Union
from data_ingestion_utils import check_schema_dataset, save_dataframe_as_csv, NodeDatasetInfo, type_keys, create_connection, DatasetSchema, NewDataset, RemoveDatasetObject, local_datasets
import uvicorn
import sqlite3
import os
import json
import csv
import io
import uuid
import logging
import httpx
import pandas as pd
import numpy as np
#import requests

app = FastAPI()

ANNOTATION_ENDPOINT =  "http://49.13.149.57:30892/schema" #"http://data-annotation:80/schema"
CATALOGUE_ENDPOINT = "http://49.13.149.57:31591/metadata" #"http://data-catalogue:83/metadata"

# create new dataset on database
@app.post("/dataset", tags=["data-ingestion"])
async def upload_dataset(node: str=Form(...), disease: str=Form(...),  file: UploadFile = File(...)): #dataset: NewDataset,
    # upload csv file
    if file.filename.endswith(".csv"):
        #dataset = await file.read()
        csv_content = await file.read()
        dataframe = pd.read_csv(io.StringIO(csv_content.decode("latin1")), sep=';')
        async with httpx.AsyncClient() as client:
            try:
                # Fetch schema from data-annotation
                print('before response get schema')
                response = await client.get(f"{ANNOTATION_ENDPOINT}/{disease}")
                print(response.json())
                if response.status_code != 200:
                    raise HTTPException(status_code=404, detail="Schema not found")
                schema = response.json()["schema"]

                errors = list(check_schema_dataset(schema, dataframe))
                print('check dataset and schema')
                if errors[0]:
                    raise HTTPException(status_code=404, detail=errors)

                # Save dataset as CSV file on local node
                iid = str(uuid.uuid4())
                filename = f"{disease}_{node}_{iid}.csv"
                filepath = save_dataframe_as_csv(dataframe, filename, node)
                local_datasets[filename] = filepath

                # Record path on central node
                node_dataset = NodeDatasetInfo(node=node, path=filepath, disease=disease)
                try:
                    response = await client.post(f"{CATALOGUE_ENDPOINT}", json=node_dataset.dict())
                    print('save metadata')
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    raise HTTPException(status_code=e.response.status_code,
                                        detail=f"Error saving metadata: {e.response.text}")
                except httpx.RequestError as e:
                    raise HTTPException(status_code=500, detail=f"Error connecting to data-catalogue: {str(e)}")

                return {"message": "Dataset uploaded and validated successfully"}

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing json file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Only csv files are accepted")

# remove a dataset from local node and from database
@app.delete("/dataset", tags=["data-ingestion"])
#async def remove_dataset(node: str=Form(...), disease:str=Form(...), path:str=Form(...)):
async def remove_dataset(removedatasetobject : RemoveDatasetObject, request:Request):
#async def remove_dataset(node: str, disease: str, path:str):
    logging.info(f"Received request: {await request.json()}")
    async with httpx.AsyncClient() as client:
        try:
        # remove dataset from database
            #print(removedatasetobject.node, removedatasetobject.disease, removedatasetobject.path)
            #response = await client.delete(CATALOGUE_ENDPOINT, json={"node": removedatasetobject.node, "disease": removedatasetobject.disease, "path": removedatasetobject.path})#remove_dataset_info_from_database(node, disease, path)
            response = await client.delete(
                CATALOGUE_ENDPOINT,
                json=json.dumps({
                    'node': removedatasetobject.node,
                    'disease': removedatasetobject.disease,
                    'path': removedatasetobject.path
                }),
                headers={"Content-Type": "application/json"}
            )
            #response = await client.delete(CATALOGUE_ENDPOINT, params={'node':node, 'disease':disease, 'path':path})
            response.raise_for_status()
#        # remove dataset from local node
            for filename, filepath in local_datasets.copy().items():
                print(filename)
                print(filepath)
                if f"{disease}_{node}" in filename and filepath == removedatasetobject.path:
                    os.remove(filepath)
                    del local_datasets[filename]
        #print(local_datasets)

        # remove dataset from list in central node
        #if disease in central_node_datasets:
        #    central_node_datasets[disease] = [dataset for dataset in central_node_datasets[disease] if dataset.node != node]

            return {"message": "Dataset removed successfully"}, local_datasets

        #except httpx.HTTPStatusError as e:
        #    raise HTTPException(status_code=e.response.status_code, detail=f"Error removing dataset: {e.response.text}")
        #except Exception as e:
        #    raise HTTPException(status_code=500, detail=f"Error removing dataset: {str(e)}")
        
        except httpx.HTTPStatusError as exc:
            logging.error(f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}")
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json())
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthcheck")
async def healthcheck():
    #dummy health check
    #return Response(content="OK", status_code=200)
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=82)
