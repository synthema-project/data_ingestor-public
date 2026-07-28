import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.orm import Session
from models import NodeDatasetInfo
from sqlmodel import SQLModel, create_engine, Session as TestSession
from tempfile import TemporaryDirectory

# Test Client for the FastAPI app
client = TestClient(app)

# Mock database engine for unit tests
@pytest.fixture
def mock_db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with TestSession(engine) as session:
        yield session

# Temporary directory for local dataset files
@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as temp:
        yield temp

# Unit tests for the data-ingestor
@pytest.mark.asyncio
class TestDataIngestor:

    @pytest.fixture
    def setup_database(self, mock_db):
        """Set up a sample database entry for testing."""
        dataset = NodeDatasetInfo(node="test_node", disease="test_disease", path="/mock/path/test.csv")
        mock_db.add(dataset)
        mock_db.commit()
        return dataset

    @patch("data_ingestor.os.remove")
    @patch("data_ingestor.httpx.AsyncClient.delete", new_callable=AsyncMock)
    async def test_remove_dataset_success(
        self, mock_http_delete, mock_os_remove, mock_db, setup_database
    ):
        """
        Test the successful removal of a dataset and metadata from the catalogue.
        """
        # Mocking HTTP DELETE response for the catalogue
        mock_http_delete.return_value.status_code = 200

        # Simulate calling the DELETE endpoint
        response = client.delete(
            "/dataset",
            params={"node": setup_database.node, "disease": setup_database.disease, "path": setup_database.path},
        )

        # Verify response
        assert response.status_code == 200
        assert response.json() == {"message": "Dataset removed successfully from both database and local storage."}

        # Verify local file removal
        mock_os_remove.assert_called_once_with(setup_database.path)

        # Verify metadata removal via HTTP DELETE
        mock_http_delete.assert_awaited_once_with(
            f"{CATALOGUE_ENDPOINT}/metadata",
            params={"node": setup_database.node, "disease": setup_database.disease, "path": setup_database.path},
            headers={"Content-Type": "application/json"},
        )

        # Verify metadata is removed from the mock database
        statement = mock_db.query(NodeDatasetInfo).filter_by(path=setup_database.path).first()
        assert statement is None

    @pytest.mark.asyncio
    @patch("data_ingestor.os.remove")
    @patch("data_ingestor.httpx.AsyncClient.delete", new_callable=AsyncMock)
    async def test_remove_dataset_metadata_not_found(
        self, mock_http_delete, mock_os_remove, mock_db, setup_database
    ):
        """
        Test removing a dataset when metadata is not found in the data-catalogue.
        """
        # Mock HTTP DELETE failure
        mock_http_delete.side_effect = Exception("Metadata not found in catalogue.")

        # Simulate calling the DELETE endpoint
        response = client.delete(
            "/dataset",
            params={"node": setup_database.node, "disease": setup_database.disease, "path": setup_database.path},
        )

        # Verify response
        assert response.status_code == 500
        assert "Metadata not found in catalogue." in response.json()["detail"]

        # Verify local file removal was attempted
        mock_os_remove.assert_called_once_with(setup_database.path)

    @pytest.mark.asyncio
    @patch("data_ingestor.httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_upload_dataset_success(self, mock_http_post, mock_db, temp_dir):
        """
        Test successful upload of a dataset.
        """
        # Mock response from annotation service
        mock_http_post.return_value.status_code = 200
        mock_http_post.return_value.json.return_value = {"schema": {"type": "object", "properties": {}}}

        # Create a dummy CSV file
        file_path = os.path.join(temp_dir, "test.csv")
        with open(file_path, "w") as file:
            file.write("column1,column2\nvalue1,value2")

        with open(file_path, "rb") as file:
            response = client.post(
                "/dataset",
                files={"file": ("test.csv", file, "text/csv")},
                data={"node": "test_node", "disease": "test_disease"},
            )

        # Verify response
        assert response.status_code == 200
        assert "Dataset uploaded and validated successfully" in response.json()["message"]

        # Verify metadata upload to the data-catalogue
        mock_http_post.assert_awaited_once_with(
            CATALOGUE_ENDPOINT,
            json={"node": "test_node", "disease": "test_disease", "path": ANY},  # Path will be dynamic
        )

    @pytest.mark.asyncio
    @patch("data_ingestor.os.remove")
    async def test_remove_nonexistent_dataset(self, mock_os_remove, mock_db):
        """
        Test removing a dataset that does not exist in the local storage.
        """
        # Simulate calling the DELETE endpoint with a nonexistent file
        response = client.delete(
            "/dataset",
            params={"node": "nonexistent_node", "disease": "nonexistent_disease", "path": "/mock/path/nonexistent.csv"},
        )

        # Verify response
        assert response.status_code == 404
        assert response.json()["detail"] == "File not found in local storage."

        # Verify file removal was not called
        mock_os_remove.assert_not_called()
