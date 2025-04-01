import os
import io
import pytest
import pandas as pd
from pathlib import Path 
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.orm import Session
from minio import Minio
from minio.error import S3Error
from models import NodeDatasetInfo
from sqlmodel import SQLModel, create_engine, Session as TestSession
from tempfile import TemporaryDirectory
from storage import minio_client

# Configurazione per il test
TEST_BUCKET = "data-annotation"
TEST_FILENAME = "DATA.csv"
TEST_NODE = "test-node"

current_dir = Path(__file__).resolve().parent

TEST_DATA_PATH = schema_path = current_dir / "example_data" / "AML_DATA_ES.csv"


def test_bucket_exists():
    print('BUCKET EXISTS')
    assert minio_client.bucket_exists("data-annotation") is True


def test_put_object_success():#(minio_client, example_dataframe):
    """Testa la chiamata a put_object di MinIO con successo."""
    #csv_buffer = io.BytesIO()
    #example_dataframe.to_csv(csv_buffer, index=False)
    #csv_buffer.seek(0)
    
    #with patch("minio.Minio", return_value=minio_client_mock):
    minio_client.fput_object(
            TEST_BUCKET,
            "test-dataframe",
            TEST_DATA_PATH, #f"{TEST_NODE}/{TEST_FILENAME}",
            content_type='text/csv'
    )
    
    found = minio_client.stat_object(TEST_BUCKET, "test-dataframe")
    assert found

def test_put_object_failure():
#    """Testa il fallimento della chiamata a put_object di MinIO."""
    
    minio_client.fput_object.side_effect = S3Error("Error", "MockedError", "ReqID", "HostID", "BucketName")
    
#    with patch("minio.Minio", return_value=minio_client_mock):
    #with pytest.raises(S3Error):
    #        minio_client.fput_object(
    #        TEST_BUCKET,
    #        "test-dataframe",
    #        TEST_DATA_PATH, #f"{TEST_NODE}/{TEST_FILENAME}",
    #        content_type='text/csv'
    #        )
    with patch.object(minio_client, "fput_object", side_effect=S3Error("AccessDenied", "MockedError", "ReqID", "HostID", "BucketName", MagicMock())):
        with pytest.raises(S3Error):
            minio_client.fput_object(
                TEST_BUCKET,
                "test-dataframe",
                TEST_DATA_PATH,
                content_type='text/csv'
            )

def test_remove_object_success():
    """Test successful deletion of an object from MinIO."""
    minio_client.remove_object(TEST_BUCKET, "test-dataframe")

    # Check if object exists (it should not)
    with pytest.raises(S3Error):
        minio_client.stat_object(TEST_BUCKET, "test-dataframe")

def test_remove_object_failure():
    """Test failure when trying to delete a non-existent object from MinIO."""
    with patch.object(minio_client, "remove_object", side_effect=S3Error("NoSuchKey", "MockedError", "ReqID", "HostID", "BucketName", MagicMock())):
        with pytest.raises(S3Error):
            minio_client.remove_object(TEST_BUCKET, "nonexistent-file.csv")
