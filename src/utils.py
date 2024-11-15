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
    df = pd.read_csv(csv_file_path)
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

def validate_data(data_dict, schema):
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
