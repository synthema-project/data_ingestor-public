from fastapi import FastAPI, HTTPException, Body, File, UploadFile
from pydantic import BaseModel
from typing import Dict, List, Union
import sqlite3
import os
import json
import csv
import io
import uuid
import pandas as pd
import numpy as np

# Path al database SQLite
DATABASE_FILE = "./central_node.db"
# directory dove salvare i dataset locali
LOCAL_DATASETS_DIR = "./local_datasets"

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
    iid: str

type_keys = {
    'int': int,
    'float': float,
    'string': str,
    'bool': bool,
    'category': int
}

##################################################
# CHECK COMPATIBILITY BETWEEN DATASET AND SCHEMA #
##################################################

def check_schema_dataset(DS:dict, DD):
    """
        Check compatibility between dataset and schema, returns the list of incompatibilities
    """
    key_checks = DS['data'].keys()
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

###########################################
# CONNECTION BETWEEN FASTAPI AND SQLITE #
###########################################

# Funzione per creare la connessione al database SQLite
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        print(f"Connected to SQLite database '{DATABASE_FILE}'")
        return conn
    except Error as e:
        print(e)

##################
# DISEASE SCHEMA #
##################

# Save the schema in a SQL database table
def save_schema_to_database(disease: str, schemas: dict):
    try:
        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()

        # create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schemas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disease TEXT NOT NULL,
                schema TEXT NOT NULL
            )
        """)
        conn.commit()

        # Insert schema into database
        cursor.execute("""
            INSERT INTO schemas (disease, schema)
            VALUES (?, ?)
        """, (disease, json.dumps(schemas)))

        print('SCHEMA successfully saved into the database')

        # Commit and close connection
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("Error saving schema to database:", e)

# Update a schema in the database
def update_schema_in_database(disease: str, updated_schema: dict):
    try:
        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()

        # Update the schema in the database
        cursor.execute("""
            UPDATE schemas
            SET schema = ?
            WHERE disease = ?
        """, (json.dumps(updated_schema), disease))

        # Commit the transaction and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("Error updating schema in database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Retrieve a schema from the database
def get_schema_from_database(disease: str):
    try:
        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()

        # Query to retrieve the schema
        cursor.execute("""
            SELECT schema FROM schemas WHERE disease = ?
        """, (disease,))

        # Fetching the result
        schema = cursor.fetchone()
        cursor.close()
        conn.close()

        # If schema is found, return it
        if schema:
            print("Schema found in the database:")
            return schema[0]
        else:
            print(f"No schema found in the database for the given {disease}.")
            return None

    except Exception as e:
        print("Error retrieving schema from database:", e)
        return None

######################
# DATASET MANAGEMENT #
######################

# Save dataset info (disease, node, path) into the database
def save_dataset_info_to_database(node_dataset: NodeDatasetInfo):
    try:
        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node TEXT NOT NULL,
                path TEXT NOT NULL,
                disease TEXT NOT NULL
            )
        """)
        # Insert dataset information into the database
        cursor.execute("""
            INSERT INTO datasets (node, path, disease)
            VALUES (?, ?, ?)
        """, (node_dataset.node, node_dataset.path, node_dataset.disease))

        # Commit the transaction and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("Error saving dataset info to database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Retrieve dataset info from node and disease
def get_dataset_info_from_database(node: str, disease: str):
    try:
        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()

        # Execute the SQL query to retrieve dataset information
        cursor.execute("""
            SELECT node, path, disease
            FROM datasets
            WHERE node = ? AND disease = ?
        """, (node, disease))

        # Fetch the result
        dataset_info = cursor.fetchone()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return dataset_info

    except Exception as e:
        print("Error retrieving dataset info from database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Remove the dataset info from the database
def remove_dataset_info_from_database(node: str, disease: str, path:str):
    try:
        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()

        # Delete the dataset entry from the database
        cursor.execute("""
            DELETE FROM datasets
            WHERE node = ? AND disease = ? AND path = ?
        """, (node, disease, path))

        # Commit the transaction and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("Error removing dataset info from database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
