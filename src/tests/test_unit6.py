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
#from storage import minio_client

# Configurazione per il test
TEST_BUCKET = "data-annotation"
#TEST_FILENAME = "DATA.csv"
#TEST_NODE = "test-node"
#TEST_DATA_PATH = "/app/tests/example_data/DATA.csv"

#@pytest.fixture#
#def minio_client():
#    """Real MinIO client."""
minio_client = Minio(
        "obstorageapi.k8s.synthema.rid-intrasoft.eu",  # Update with your MinIO endpoint
        access_key="mqcqwECvoga6pkDRhOUz",
        secret_key="EN6t1TWZELRhn1LyGoi6ubtApmXoUJfsny9tRYz9",
        secure=True  # Change to True if using HTTPS
    )

#    if not client.bucket_exists(TEST_BUCKET):
#        client.make_bucket(TEST_BUCKET)
    
#return client

def test_bucket_exists():
    print('BUCKET EXISTS')
    assert minio_client.bucket_exists("data-annotation") is True

#@pytest.fixture
#def example_dataframe():
#    """Crea un dataframe di esempio."""
#    data = {
#        "id": [1, 2, 3],
#        "name": ["Alice", "Bob", "Charlie"],
#        "age": [25, 30, 35]
#    }
#    return pd.DataFrame(data)

example_dataframe = pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35]
    })

def test_put_object_success():#(minio_client, example_dataframe):
    """Testa la chiamata a put_object di MinIO con successo."""
    csv_buffer = io.BytesIO()
    example_dataframe.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    #with patch("minio.Minio", return_value=minio_client_mock):
    minio_client.fput_object(
            TEST_BUCKET,
            f"{TEST_NODE}/{TEST_FILENAME}",
            data=csv_buffer,
            length=csv_buffer.getbuffer().nbytes,
            content_type='text/csv'
    )
    
    #minio_client_mock.put_object.assert_called_once()
    found = minio_client.stat_object(TEST_BUCKET, f"{TEST_NODE}/{TEST_FILENAME}")
    assert found

#def test_put_object_failure(minio_client_mock, example_dataframe):
#    """Testa il fallimento della chiamata a put_object di MinIO."""
#    csv_buffer = io.BytesIO()
#    example_dataframe.to_csv(csv_buffer, index=False)
#    csv_buffer.seek(0)
    
#    minio_client_mock.put_object.side_effect = S3Error("Error", "MockedError", "ReqID", "HostID", "BucketName")
    
#    with patch("minio.Minio", return_value=minio_client_mock):
#        with pytest.raises(S3Error):
#            minio_client_mock.put_object(
#                TEST_BUCKET,
#                f"{TEST_NODE}/{TEST_FILENAME}",
#                data=csv_buffer,
#                length=csv_buffer.getbuffer().nbytes,
#                content_type='text/csv'
#            )
