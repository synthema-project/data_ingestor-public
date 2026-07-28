import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from minio import Minio
import os
from main import app

MOCK_MINIO_BUCKET = "test-bucket"
MOCK_MINIO_URL = "http://minio.synthema-dev.svc.cluster.local:9000"

@pytest.fixture(scope="module")
def mock_minio():
    """Mock MinIO client."""
    #with patch("data_ingestor.Minio") as mock:
    with patch("storage.minio_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

@pytest.mark.asyncio
async def test_upload_dataset_success(mock_minio):
    """Test successful dataset upload to MinIO."""
    node = "test_node"
    disease = "test_disease"
    
    with patch("data_ingestor.Minio.put_object", new_callable=AsyncMock) as mock_put:
        mock_put.return_value = None  # Simulate successful upload

        async with AsyncClient(app=app, base_url="http://test") as ac:
            files = {"file": ("test.csv", "column1,column2\nvalue1,value2", "text/csv")}
            response = await ac.post("/dataset", data={"node": node, "disease": disease}, files=files)

        assert response.status_code == 200
        assert response.json() == {"message": "Dataset uploaded and validated successfully"}

        # Validate MinIO upload
        mock_put.assert_called_once()

@pytest.mark.asyncio
async def test_remove_dataset_success(mock_minio):
    """Test successful dataset removal from MinIO."""
    node = "test_node"
    disease = "test_disease"
    path = "test-bucket/test.csv"

    with patch("data_ingestor.Minio.remove_object", new_callable=AsyncMock) as mock_remove:
        mock_remove.return_value = None  # Simulate successful deletion

        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.delete("/dataset", params={"node": node, "disease": disease, "path": path})

        assert response.status_code == 200
        assert response.json() == {"message": "Dataset removed successfully from both database and MinIO storage"}

        # Validate MinIO deletion
        mock_remove.assert_called_once()
