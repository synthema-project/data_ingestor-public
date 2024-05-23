from fastapi import FastAPI, HTTPException, Body, File, UploadFile
from pydantic import BaseModel
from typing import Dict, List, Union
import sqlite3
import os
import json
import csv
import io
import uuid
import httpx
import pandas as pd
import numpy as np

# directory dove salvare i dataset locali
#LOCAL_DATASETS_DIR = "/mnt/c/users/lenovo/desktop/fastapi/SYNTHEMA/local_datasets"
LOCAL_DATASETS_DIR = "/app/data/dataset/local_datasets"
# dict to save datasets in the central node
local_datasets = {}

class DatasetSchema(BaseModel):
    disease: str
    data: Dict[str, Dict[str, List[Union[str, int, float, bool]]]]


class NewDataset(BaseModel):
    disease: str
    data: Dict[str, Dict[str, List[Union[str, int, float, bool]]]]


class NodeDatasetInfo(BaseModel):
    node: str
    path: str
    disease: str
    #nrows: int
    #ncols: int
    #provider: str
    #iid: str

type_keys = {
    'int': int,
    'float': float,
    'string': str,
    'bool': bool,
    'category': int
}

# Funzione per creare la connessione al database SQLite
#def create_connection():
#    conn = None
#    try:
#        conn = sqlite3.connect(DATABASE_FILE)
#        print(f"Connected to SQLite database '{DATABASE_FILE}'")
#        return conn
#    except Exception as e:
#        print(e)

def create_connection():
    try:
        if not os.path.exists(DATABASE_FILE):
            print(f"Database file {DATABASE_FILE} does not exist.")

        conn = sqlite3.connect(DATABASE_FILE)
        print(f"Connected to SQLite database '{DATABASE_FILE}'")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

##################################################
# CHECK COMPATIBILITY BETWEEN DATASET AND SCHEMA #
##################################################

def check_schema_dataset(DS:dict, DD):
    """
        Check compatibility between dataset and schema, returns the list of incompatibilities
    """
    print(DS)
    #print(DD)
    #print('OK')
    #print(DS["data"].keys())
    key_checks = DS["data"].keys()
    columns = DD.columns.tolist()
    errors = []
    for tab in key_checks:
        for feature in DS['data'][tab].keys():
            if feature not in columns:
                errors.append(f"Error: '{feature}' table is missing")
                yield f"Error: '{feature}' table is missing"
                continue
            else:
                key = feature
                field_value = DD[key]
                tipo = type_keys[DS['data'][tab][key][0]]
                valori = field_value.values
                valori = [x for x in valori if str(x) != 'nan']
                for k in valori:
                    if isinstance(k, np.int64) or isinstance(k, np.uint32) or isinstance(k, np.int16) or isinstance(k, np.float64) or isinstance(k, np.float32):
                        if not isinstance(k.item(), tipo):
                            errors.append(f"Error: '{key}' must be of type {tipo}")
                            yield f"Error: '{key}' must be of type {tipo}"
                    else:
                        if not isinstance(k, tipo):
                            errors.append(f"Error: '{key}' must be of type {tipo}")
                            yield f"Error: '{key}' must be of type {tipo}"
    yield errors


def save_dataframe_as_csv(dataset, filename, node):
    """
    Save the dataframe as a csv and returns the file path
    """
    if not os.path.exists(LOCAL_DATASETS_DIR+'/'+ str(node)):
        os.makedirs(LOCAL_DATASETS_DIR+'/'+ str(node))

    filepath = os.path.join(LOCAL_DATASETS_DIR+'/'+ str(node), filename)

    # Write the DataFrame to a CSV file
    dataset.to_csv(filepath, index=False)

    return filepath
