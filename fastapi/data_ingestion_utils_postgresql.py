from fastapi import FastAPI, HTTPException, Body, File, UploadFile
from pydantic import BaseModel
from typing import Dict, List, Union
import psycopg2
import psycopg2.extras
import os
import json
import csv
import io
import uuid
import pandas as pd
import numpy as np

DATABASE_URL = "postgresql://cesco20:abc123@localhost:5432/central_node"
# directory where to save local datasets
LOCAL_DATASETS_DIR = "./local_datasets"

class DatasetSchema(BaseModel):
    #columns: Dict[str, str]  # {nome_colonna: tipo_dato}
    disease: str
    data: Dict[str, Dict[str, List[Union[str, int, float, bool]]]] #{gruppi di variabili: variabili: specifiche (tipo, range, etc)


class NewDataset(BaseModel):
    disease: str
    data: Dict[str, Dict[str, List[Union[str, int, float, bool]]]]
    #data: Dict[str, str]  # {nome_colonna: valore}


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
        check compatibilty between dataset and schema, returns the list of incompatibilities
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
                #print('fv',field_value.values)
                tipo = type_keys[DS['data'][tab][key][0]]#[field_value[0]]
                #print('type',tipo)
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
    yield errors#json.dumps(errors)



def save_dataframe_as_csv(dataset, filename, node):
    """
    save the dataframe as a csv and returns the file path
    """
    if not os.path.exists(LOCAL_DATASETS_DIR+'/'+ str(node)):
        os.makedirs(LOCAL_DATASETS_DIR+'/'+ str(node))

    filepath = os.path.join(LOCAL_DATASETS_DIR+'/'+ str(node), filename)

    # Write the DataFrame to a CSV file
    dataset.to_csv(filepath, index=False)

    return filepath

###########################################
# CONNECTION BETWEEN FASTAPI AND POSTGRES #
###########################################

##################
# DISEASE SCHEMA #
##################

# save the schema in a SQL database table
def save_schema_to_database(disease: str, schemas: dict):
    try:
        # Connect to database
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        # create table if does not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schemas (
                id SERIAL PRIMARY KEY,
                disease VARCHAR NOT NULL,
                schema JSONB NOT NULL
            )
        """)
        connection.commit()
        #print(psycopg2.extras.Json(schemas))

        # insert schema into database
        cursor.execute("""
            INSERT INTO schemas (disease, schema)
            VALUES (%s, %s)
        """, (disease, psycopg2.extras.Json(schemas)))

        print('SCHEMA successfully saved into the database')

        # commit and close connection
        connection.commit()
        cursor.close()
        connection.close()

    except Exception as e:
        print("Error saving schema to database:", e)

# update a schema in the database
def update_schema_in_database(disease: str, updated_schema: dict):
    try:
        # Connect to the database
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        # Update the schema in the database
        cursor.execute("""
            UPDATE schemas
            SET schema = %s
            WHERE disease = %s
        """, (psycopg2.extras.Json(updated_schema), disease))

        # Commit the transaction and close the connection
        connection.commit()
        cursor.close()
        connection.close()

    except Exception as e:
        print("Error updating schema in database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# retrieve a schema from the database
def get_schema_from_database(disease: str):
    try:
        # database connection
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        # query to retrieve the schema
        cursor.execute("""
            SELECT schema FROM schemas WHERE disease = %s;
        """, (disease,))

        # Fetching the result
        schema = cursor.fetchone()
        cursor.close()
        connection.close()

        # If schema is found, return it
        if schema:
            print("Schema found in the database:")
            #print(schema[0])  # schema is stored in the first column of the result tuple
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

# save dataset info (disease, node, path) into the postgres database
def save_dataset_info_to_database(node_dataset: NodeDatasetInfo):#, dataset_id: str):
    try:
        # connect to the database
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS datasets (
                        id SERIAL PRIMARY KEY,
                        node VARCHAR NOT NULL,
                        path VARCHAR NOT NULL,
                        disease VARCHAR NOT NULL
                    )
                """)
        # insert dataset information into the database
        cursor.execute("""
            INSERT INTO datasets (node, path, disease)
            VALUES (%s, %s, %s)
        """, (node_dataset.node, node_dataset.path, node_dataset.disease))


        # commit the transaction and close the connection
        connection.commit()
        cursor.close()
        connection.close()


    except Exception as e:
        print("Error saving dataset info to database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


# retrieve dataset info from node and disease
def get_dataset_info_from_database(node: str, disease: str):
    try:
        # connect to the database
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        # execute the SQL query to retrieve dataset information
        cursor.execute("""
            SELECT node, path, disease
            FROM datasets
            WHERE node = %s AND disease = %s
        """, (node, disease))

        # fetch the result
        dataset_info = cursor.fetchone()

        # close the cursor and connection
        cursor.close()
        connection.close()

        return dataset_info

    except Exception as e:
        print("Error retrieving dataset info from database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# remove the dataset info from the database
def remove_dataset_info_from_database(node: str, disease: str, path:str):
    try:
        # connect to the database
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        # delete the dataset entry from the database
        cursor.execute("""
            DELETE FROM datasets
            WHERE node = %s AND disease = %s AND path = %s
        """, (node, disease, path))

        # commit the transaction and close the connection
        connection.commit()
        cursor.close()
        connection.close()

    except Exception as e:
        print("Error removing dataset info from database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
