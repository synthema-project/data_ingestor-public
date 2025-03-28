import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from minio import Minio
from minio.error import S3Error
from main import app
from sqlalchemy.orm import Session
from models import NodeDatasetInfo
from sqlmodel import SQLModel, create_engine, Session as TestSession
from tempfile import TemporaryDirectory

from storage import minio_client

def test_bucket_exists():
    print('BUCKET EXISTS')
    assert minio_client.bucket_exists("data-annotation") is True


 Test Client for the FastAPI app
client = TestClient(app)

# MinIO Mock Setup
#MOCK_MINIO_BUCKET = "test-bucket"

#@pytest.fixture
#def mock_minio():
#    """Mock MinIO client."""
#    with patch("data_ingestor.Minio") as mock:
#        mock_client = MagicMock()
#        mock.return_value = mock_client
#        yield mock_client

#@pytest.mark.asyncio
#class TestDataIngestor:
    
#    @pytest.fixture
#    def setup_database(self, mock_db):
#        """Set up a sample database entry for testing."""
#        dataset = NodeDatasetInfo(node="test_node", disease="test_disease", path="test-bucket/test.csv")
#        mock_db.add(dataset)
#        mock_db.commit()
#        return dataset

#    @patch("data_ingestor.Minio.remove_object")
#    async def test_remove_dataset_success(self, mock_remove_object, mock_minio, mock_db, setup_database):
#        """
#        Test successful dataset removal from MinIO and database.
#        """
#        mock_remove_object.return_value = None  # Simulate successful removal##

#        response = client.delete(
#            "/dataset",
#            params={"node": setup_database.node, "disease": setup_database.disease, "path": setup_database.path},
#        )

#        assert response.status_code == 200
#        assert response.json() == {"message": "Dataset removed successfully from both database and MinIO storage."}

#        # Verify MinIO deletion
#        mock_remove_object.assert_called_once_with(MOCK_MINIO_BUCKET, "test.csv")

#    @pytest.mark.asyncio
#    @patch("data_ingestor.Minio.put_object")
#    async def test_upload_dataset_success(self, mock_put_object, mock_minio, mock_db, temp_dir):
#        """
#        Test successful dataset upload to MinIO.
#        """
#        mock_put_object.return_value = None  # Simulate a successful upload

#        file_path = os.path.join(temp_dir, "test.csv")
#        with open(file_path, "w") as file:
#            file.write("column1,column2\nvalue1,value2")

#        with open(file_path, "rb") as file:
#            response = client.post(
#                "/dataset",
#                files={"file": ("test.csv", file, "text/csv")},
#                data={"node": "test_node", "disease": "test_disease"},
#            )

#        assert response.status_code == 200
#        assert "Dataset uploaded and validated successfully" in response.json()["message"]

#        # Verify MinIO upload
#        mock_put_object.assert_called_once()
