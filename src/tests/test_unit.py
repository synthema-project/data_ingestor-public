# test_utils.py
import pandas as pd
import numpy as np
import os
from data_ingestion_utils import check_schema_dataset, save_dataframe_as_csv, create_connection

def test_check_schema_dataset():
    schema = {
        "disease": "test_disease",
        "data": {
            "table1": {
                "feature1": ["int"],
                "feature2": ["string"]
            }
        }
    }
    data = {
        "feature1": [1, 2, 3],
        "feature2": ["a", "b", "c"]
    }
    df = pd.DataFrame(data)
    errors = list(check_schema_dataset(schema, df))
    assert len(errors) == 0

def test_save_dataframe_as_csv(tmp_path):
    data = {
        "feature1": [1, 2, 3],
        "feature2": ["a", "b", "c"]
    }
    df = pd.DataFrame(data)
    filename = "test.csv"
    node = "node1"
    filepath = save_dataframe_as_csv(df, filename, node)
    assert os.path.exists(filepath)

def test_create_connection():
    conn = create_connection()
    assert conn is not None
    conn.close()
