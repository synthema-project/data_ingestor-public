import os
import pytest
import pandas as pd
from pathlib import Path 
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.orm import Session
from minio import Minio
from models import NodeDatasetInfo
from sqlmodel import SQLModel, create_engine, Session as TestSession
from tempfile import TemporaryDirectory
from storage import minio_client

# Configurazione per il test
TEST_BUCKET = "test-bucket"
TEST_FILENAME = "DATA.csv"
TEST_NODE = "test-node"
TEST_DATA_PATH = "/app/tests/example_data/DATA.csv"

@pytest.fixture
def minio_client_mock():
    """Real MinIO client."""
    client = Minio(
        "obstorageapi.k8s.synthema.rid-intrasoft.eu",  # Update with your MinIO endpoint
        access_key="mqcqwECvoga6pkDRhOUz",
        secret_key="EN6t1TWZELRhn1LyGoi6ubtApmXoUJfsny9tRYz9",
        secure=True  # Change to True if using HTTPS
    )
    return client

def test_save_dataframe_to_minio_success(minio_client_mock):
    """Testa il salvataggio del dataframe su MinIO con successo usando DATA.csv."""
    df = pd.read_csv(TEST_DATA_PATH, sep=';')
    
    with patch("src.utils.minio_client", minio_client_mock):
        minio_path = save_dataframe_to_minio(df, TEST_FILENAME, TEST_NODE)
    
    expected_path = f"{TEST_NODE}/{TEST_FILENAME}"
    minio_client_mock.put_object.assert_called_once()
    assert minio_path == expected_path

def test_save_dataframe_to_minio_failure(minio_client_mock):
    """Testa il fallimento dell'upload su MinIO usando DATA.csv."""
    df = pd.read_csv(TEST_DATA_PATH, sep=';')
    
    minio_client_mock.put_object.side_effect = S3Error("Error", "MockedError", "ReqID", "HostID", "BucketName")
    
    with patch("src.utils.minio_client", minio_client_mock):
        with pytest.raises(Exception, match="Failed to upload dataset to MinIO"):
            save_dataframe_to_minio(df, TEST_FILENAME, TEST_NODE)

