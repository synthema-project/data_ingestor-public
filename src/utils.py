import csv
import jsonschema
from jsonschema import validate
import numpy as np
import pandas as pd
import os
import io
from sqlmodel import Session, select
from models import DatasetSchema, NodeDatasetInfo
import json
import math
from fastapi import HTTPException
from pathlib import Path
from minio.error import S3Error
from storage import minio_client, upload_file, download_file
from config import settings

#LOCAL_DATASETS_DIR = "/mnt/c/users/lenovo/desktop/data-ingestion/local_datasets"

current_dir = Path(__file__).resolve().parent

#LOCAL_DATASETS_DIR = current_dir / "tests" / "example_data"
#LOCAL_DATASETS_DIR = "/app/datasets"
#LOCAL_DATASETS_DIR = "/app/data/dataset/local_datasets"

def read_csv(csv_file_path):
    data = []
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(row)
    return data

def replace_none_with_nan(data_dict):
    if data_dict is None:
        return None

    if isinstance(data_dict, dict):
        for key, value in data_dict.items():
            if value is None:
                data_dict[key] = math.nan
            else:
                data_dict[key] = replace_none_with_nan(value)
    elif isinstance(data_dict, list):
        return [replace_none_with_nan(item) for item in data_dict]

    return data_dict


#def csv_to_json_dict(csv_file_path, schema):
#    dataframe = pd.read_csv(csv_file_path)
#    data = dataframe.where(pd.notnull(dataframe), None)  # Replace NaNs with None

#    json_dict = {"data": {"clinical": []}}

#    for _, row in data.iterrows():
#        clinical_entry = {}
#        for key in schema["properties"]["data"]:#["properties"]["clinical"]["properties"]:
#            value = row[key]
#            clinical_entry[key] = None if pd.isna(value) else value
#        json_dict["data"]["clinical"].append(clinical_entry)

#    return json_dict


#def validate_data(data_dict, schema):
#    print(data_dict)
#    for key, value in data_dict["data"].items():
#        for sub_key, sub_value in value.items():
#            for item in sub_value:
#                instance = {sub_key: item}
#                sub_schema = {"type": "object", "properties": {sub_key: schema["properties"]["data"]["properties"][key]["properties"][sub_key]}}
#                print(instance)
#                try:
#                    validate(instance=instance, schema=sub_schema)
#                except jsonschema.exceptions.ValidationError as err:
#                    print("Data dictionary is invalid according to the schema:", err.message)
#                    raise HTTPException(status_code=400, detail=f"Validation error: {err.message}")
#    print("Data dictionary is valid according to the schema.")

def csv_to_json_dict(csv_file_path, schema):
    ##df = pd.read_csv(csv_file_path)
    df = csv_file_path
    df = df.replace({np.nan: None})
    data = df.to_dict(orient='records')
    return data

#def validate_data(data_dict, schema):
#    for record in data_dict:
#        clinical_data = {key: record[key] for key in record.keys() if
#                         key in schema['properties']['data']['properties']['clinical']['properties']}
#        karyotype_data = {key: record[key] for key in record.keys() if
#                          key in schema['properties']['data']['properties']['karyotype']['properties']}

#        data_to_validate = {
#            "data": {
#                "clinical": clinical_data,
#                "karyotype": karyotype_data
#            }
#        }
#        try:
#            validate(instance=data_to_validate, schema=schema)
#            print("Data dictionary is valid according to the schema.")
#        except jsonschema.ValidationError as err:
#            print("Data dictionary is invalid according to the schema:", err.message)
#            raise ValueError(f"Validation error: {err.message}")
"""
def validate_data(data_dict, schema):
    if isinstance(data_dict, dict):
        data_dict = [data_dict]
    errors = []
    #print(data_dict)
    for idx, record in enumerate(data_dict):
        clinical_data = {key: record[key] for key in record.keys() if
                         key in schema['data']['clinical']} #key in schema['properties']['data']['properties']['clinical']['properties']}
        karyotype_data = {key: record[key] for key in record.keys() if
                          key in schema['data']['karyotype']}
        mutations_data = {key: record[key] for key in record.keys() if
                          key in schema['data']['mutations']}

        data_to_validate = {
            "data": {
                "clinical": clinical_data,
                "karyotype": karyotype_data,
                "mutations": mutations_data
            }
        }
        try:
            validate(instance=data_to_validate, schema=schema)
            print(f"Row {idx + 1}: Data dictionary is valid according to the schema.")
        except jsonschema.ValidationError as err:
            error_detail = {
                "row": idx + 1,
                "message": err.message,
                "path": list(err.path),
                "value": err.instance
            }
            errors.append(error_detail)
            print(f"Row {idx + 1}: Data dictionary is invalid according to the schema: {err.message}")
            print(f"Error details: Path - {list(err.path)}, Value - {err.instance}")

    if errors:
        raise ValueError({"errors": errors})
"""
def validate_data(data_dict, schema):
    if isinstance(data_dict, dict):
        data_dict = [data_dict]

    for idx, record in enumerate(data_dict):
        for key, expected_type in schema.items():
            if key not in record:
                raise ValueError(f"Missing field {key} in record {idx}")

            value = record[key]

            if expected_type == "int" and not isinstance(value, int):
                raise ValueError(f"{key} must be int")

            if expected_type == "float" and not isinstance(value, float):
                raise ValueError(f"{key} must be float")

            if expected_type == "str" and not isinstance(value, str):
                raise ValueError(f"{key} must be str")


#def validate_data(data_dict, schema):
#    try:
#        validate(instance=data_dict, schema=schema)
#        print("Data dictionary is valid according to the schema.")
#    except jsonschema.exceptions.ValidationError as err:
#        print("Data dictionary is invalid according to the schema:", err.message)
#        raise ValueError(f"Validation error: {err.message}")

def save_dataframe_as_csv(dataset, filename, node, savepath):
    """
    Save the dataframe as a csv and returns the file path
    """
    if not os.path.exists(savepath+'/'+ str(node)):
        os.makedirs(savepath+'/'+ str(node))

    filepath = os.path.join(savepath+'/'+ str(node), filename)

    # Write the DataFrame to a CSV file
    dataset.to_csv(filepath, index=False)

    return filepath

def save_dataset_to_database(session: Session, dataset: DatasetSchema):
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return dataset

def get_schema_from_database(session: Session, disease: str):
    statement = select(DatasetSchema).where(DatasetSchema.disease == disease)
    return session.exec(statement).first()

#def remove_dataset_from_db(session: Session, node: str, disease: str, path: str):
#    try:
#        statement = select(NodeDatasetInfo).where(NodeDatasetInfo.disease == disease, NodeDatasetInfo.node == node, NodeDatasetInfo.path == path)
#        print(statement)
#        dataset = session.exec(statement).first()
#        print(dataset)
#        if dataset:
#            #session.delete(dataset)
#            #session.commit()
#            return True
#        return False
#    except Exception as e:
#        print("Error removing dataset info from database:", e)
#        raise HTTPException(status_code=500, detail="Internal Server Error")

def remove_dataset_from_db(session: Session, node: str, disease: str, path: str):
    try:
        # Query the database for the dataset
        statement = select(NodeDatasetInfo).where(
            NodeDatasetInfo.disease == disease,
            NodeDatasetInfo.node == node,
            NodeDatasetInfo.path == path
        )
        dataset = session.exec(statement).first()

        if dataset:
            # Check if the file exists
            if os.path.exists(path):
                os.remove(path)
            else:
                print(f"File not found on disk: {path}")
                raise HTTPException(status_code=404, detail=f"Dataset '{path}' not found on disk.")

            # Remove from database
            session.delete(dataset)
            session.commit()
            return True
        else:
            raise HTTPException(status_code=404, detail=f"Dataset '{path}' not found in database.")
    except Exception as e:
        print("Error removing dataset info from database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

#def save_node_dataset_info(session: Session, info: NodeDatasetInfo):
#    session.add(info)
#    session.commit()
#    session.refresh(info)
#    return info

def save_node_dataset_info(session: Session, info: NodeDatasetInfo):
    """
    Save a NodeDatasetInfo object to the database.

    Args:
        session (Session): SQLModel session for database operations.
        info (NodeDatasetInfo): The NodeDatasetInfo object to save.

    Returns:
        NodeDatasetInfo: The saved object with any database-generated fields (e.g., ID) refreshed.
    """
    try:
        session.add(info)  # Add the object to the session
        session.commit()   # Commit the transaction to save to the database
        session.refresh(info)  # Refresh to get any autogenerated fields like ID
        return info
    except Exception as e:
        session.rollback()  # Rollback in case of any errors
        raise Exception(f"Error saving dataset info to the database: {str(e)}")

### MINIO INTEGRATION

#def save_dataframe_to_minio(dataset: pd.DataFrame, filename: str, node: str):
def save_dataframe_to_minio(dataset: pd.DataFrame, filename: str):
    """
    Save the dataframe as a CSV file to MinIO.
    """
    csv_buffer = io.BytesIO()
    dataset.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    minio_path = filename #f"{node}/{filename}"

    try:
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            minio_path,
            data=csv_buffer,
            length=csv_buffer.getbuffer().nbytes,
            content_type='text/csv'
        )
        print(f"Uploading to bucket: {settings.MINIO_BUCKET_NAME}, path: {minio_path}")
        return minio_path
    except S3Error as e:
        raise Exception(f"Failed to upload dataset to MinIO: {str(e)}")


#def remove_dataset_from_minio(node: str, filename: str):
def remove_dataset_from_minio(filename: str):
    """
    Remove a dataset file from MinIO storage.
    """
    minio_path = filename #f"{node}/{filename}"

    try:
        minio_client.remove_object(settings.MINIO_BUCKET_NAME, minio_path)
        return True
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset from MinIO: {str(e)}")

#def get_dataset_from_minio(node: str, filename: str) -> pd.DataFrame:
def get_dataset_from_minio(filename: str) -> pd.DataFrame:
    """
    Retrieve a dataset file from MinIO and return it as a pandas dataframe.
    """
    minio_path = filename  #f"{node}/{filename}"

    try:
        response = minio_client.get_object(settings.MINIO_BUCKET_NAME, minio_path)
        csv_content = response.read().decode("utf-8")
        response.close()
        response.release_conn()

        dataframe = pd.read_csv(io.StringIO(csv_content))
        return dataframe
    except S3Error as e:
        raise HTTPException(status_code=404, detail=f"Dataset not found in MinIO: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dataset: {str(e)}")






