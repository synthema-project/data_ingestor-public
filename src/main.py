from fastapi import FastAPI

app = FastAPI()

from fastapi import HTTPException
from pydantic import BaseModel
from typing import Dict, List, Union
from data_ingestion_utils import save_schema_to_database, get_schema_from_database, update_schema_in_database
from data_ingestion_utils import save_dataset_info_to_database, get_dataset_info_from_database, remove_dataset_info_from_database
from data_ingestion_utils import DATABASE_URL, check_schema_dataset, save_dataframe_as_csv, LOCAL_DATASETS_DIR, NodeDatasetInfo, DatasetSchema, NewDataset
from fastapi import UploadFile, File
import pandas as pd
import numpy as np
import io
import csv
import os
import uuid
import json

#DATABASE_URL = "postgresql://cesco20:abc123@localhost:5432/central_node"

central_node_datasets = {}

# dict to save datasets in the central node
local_datasets = {}
# dict to save schemas in the central node
central_node_schemas = {}

############################
# SCHEMA FASTAPI FUNCTIONS #
############################
@app.get("/healthcheck", tags=["healthcheck"])
async def healthcheck():
    return {"status": "ok"}

# save schema in the postgres database
@app.post("/schemas/{disease}", tags=["schemas"])
async def create_schema(disease: str,  file: UploadFile = File(...)): #schema: DatasetSchema,
    #carico lo schema come file json
    if file.filename.endswith(".json"):
        dataframe = await file.read()
        data = json.loads(dataframe)

        # save schema in central node
        central_node_schemas[disease] = data#schema
        print(central_node_schemas)

        # save the schema in SQL database table
        save_schema_to_database(disease, data)

    else:
        raise HTTPException(status_code=400, detail="Only json files are accepted")
    return {"message": f"Schema for {disease} created successfully"}, central_node_schemas

# retrieve schema from the postgres database
@app.get("/schemas/{disease}", tags=["schemas"])
async def retrieve_schema(disease: str):
    try:
        schema = get_schema_from_database(disease)
        if schema is None:
            raise HTTPException(status_code=404, detail=f"No schema found in the database for the disease: {disease}")

        return {"disease": disease, "schema": schema}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving schema: {str(e)}")

# update schema in the postgres database
@app.put("/schemas/{disease}", tags=["schemas"])
async def update_schema(disease: str, file: UploadFile = File(...)):
    if file.filename.endswith(".json"):
        try:
            # read the uploaded JSON file
            schema_data = await file.read()
            updated_schema = json.loads(schema_data)

            # update the schema in the database
            update_schema_in_database(disease, updated_schema)

            return {"message": f"Schema for {disease} updated successfully"}

        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal Server Error")
    else:
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")

#############################
# DATASET FASTAPI FUNCTIONS #
#############################

# create new dataset on database
@app.post("/datasets/{node}", tags=["datasets"])
async def upload_dataset(node: str, disease: str,  file: UploadFile = File(...)): #dataset: NewDataset,
    # upload csv file
    if file.filename.endswith(".csv"):
        #dataset = await file.read()
        csv_content = await file.read()
        dataframe = pd.read_csv(io.StringIO(csv_content.decode("latin1")), sep=';')
        try:
    # retrieve schema from database
            schema = get_schema_from_database(disease)
            if schema is None:
                raise HTTPException(status_code=404,detail=f"No schema found in the database for the disease: {disease}")

            errors = list(check_schema_dataset(schema, dataframe))
            #print('ERRORS: ', errors[0])
            if errors[0]:
                raise HTTPException(status_code=404,detail=errors)

            # Save dataset as CSV file on local node
            #iid = str(len(local_datasets) + 1)
            #filename = f"{disease}_{node}_{iid}.csv" #dataset.disease
            iid = str(uuid.uuid4())
            filename = f"{disease}_{node}_{iid}.csv"
            filepath = save_dataframe_as_csv(dataframe, filename, node)  # dataset.data

            local_datasets[filename] = filepath

            # record path on central node
            node_dataset = NodeDatasetInfo(node=node, path=filepath, disease=disease, iid=iid)  # dataset.disease
            central_node_datasets.setdefault(disease, []).append(node_dataset)  # Memorizza il percorso nel nodo centrale #dataset.disease
            print(node_dataset)

            # record path + disease in SQL database
            #dataset_id = str(uuid.uuid4())
            #dataset_id = iid
            save_dataset_info_to_database(node_dataset)#, dataset_id)

            return {"message": "Dataset created and registered successfully"}, local_datasets

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing json file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Only csv files are accepted")

# retrieve dataset info from database
@app.get("/datasets/{node}/{disease}", tags=["datasets"])
async def retrieve_dataset_info(node: str, disease: str):
    try:
        # Retrieve dataset information from the database
        dataset_info = get_dataset_info_from_database(node, disease)

        if dataset_info is None:
            raise HTTPException(status_code=404, detail=f"No dataset found in the database for node: {node} and disease: {disease}")

        # Return the dataset information
        return {
            "node": dataset_info[0],
            "path": dataset_info[1],
            "disease": dataset_info[2]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dataset info: {str(e)}")

# remove a dataset from local node and from database
@app.delete("/datasets/{node}/{disease}", tags=["datasets"])
async def remove_dataset(node: str, disease: str, path:str):
    try:
        # remove dataset from database
        remove_dataset_info_from_database(node, disease, path)

        # remove dataset from local node
        for filename, filepath in local_datasets.copy().items():
            if f"{disease}_{node}" in filename and filepath == path:
                os.remove(filepath)
                del local_datasets[filename]
        print(local_datasets)
        # remove dataset from list in central node
        if disease in central_node_datasets:
            central_node_datasets[disease] = [dataset for dataset in central_node_datasets[disease] if dataset.node != node]

        return {"message": "Dataset removed successfully"}, local_datasets

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing dataset: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=80)