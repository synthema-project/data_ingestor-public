import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from pathlib import Path
from main import app  # Import your FastAPI app
import os

# Set up temporary paths and constants for testing

current_dir = Path(__file__).resolve().parent
example_data_dir = current_dir / "example_data"
TEST_FILE_PATH = example_data_dir / "AML_DATA_ES.csv"

TEST_LOCAL_DATASETS_DIR = "/tmp/test_datasets"
#TEST_FILE_NAME = "test_dataset.csv"
#TEST_FILE_PATH = f"{TEST_LOCAL_DATASETS_DIR}/{TEST_FILE_NAME}"
CATALOGUE_ENDPOINT = "https://data-catalogue.k8s.synthema.rid-intrasoft.eu/metadata"

@pytest.fixture(scope="module")
def setup_test_env():
    """Create a test dataset directory and file."""
    os.makedirs(TEST_LOCAL_DATASETS_DIR, exist_ok=True)
    with open(TEST_FILE_PATH, "w") as f:
        f.write("col1;col2\nval1;val2\n")
    yield
    os.remove(TEST_FILE_PATH)
    os.rmdir(TEST_LOCAL_DATASETS_DIR)

@pytest.mark.asyncio
async def test_upload_dataset_success(setup_test_env):
    """Test successful dataset upload."""
    test_file_path = TEST_FILE_PATH
    node = "test_node"
    disease = "test_disease"

    # Mock Annotation Service
    annotation_mock_response = {"schema": {"col1": "string", "col2": "string"}}
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = annotation_mock_response

        # Mock Data Catalogue POST Request
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"message": "Metadata uploaded successfully"}

            # Use an AsyncClient to send the request
            async with AsyncClient(app=app, base_url="http://test") as ac:
                with open(test_file_path, "rb") as file:
                    response = await ac.post(
                        "/dataset",
                        data={"node": node, "disease": disease, "local_datasets_dir": TEST_LOCAL_DATASETS_DIR},
                        files={"file": (TEST_FILE_NAME, file, "text/csv")}
                    )

            # Assertions for the POST request
            assert response.status_code == 200
            assert response.json() == {"message": "Dataset uploaded and validated successfully"}

            # Validate the Catalogue POST Call
            mock_post.assert_awaited_once_with(
                CATALOGUE_ENDPOINT,
                json={"id": mock_post.call_args[1]["json"]["id"], "node": node, "path": mock_post.call_args[1]["json"]["path"], "disease": disease},
            )

@pytest.mark.asyncio
async def test_remove_dataset_success(setup_test_env):
    """Test successful dataset removal."""
    node = "test_node"
    disease = "test_disease"
    path = TEST_FILE_PATH

    # Mock Data Catalogue DELETE Request
    with patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.json.return_value = {"message": "Dataset deleted successfully"}

        # Use an AsyncClient to send the DELETE request
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.delete(
                "/dataset",
                params={"node": node, "disease": disease, "path": path}
            )

        # Assertions for the DELETE request
        assert response.status_code == 200
        assert response.json() == {"message": "Dataset removed successfully from both database and local storage"}
        assert not os.path.exists(path)  # Ensure file is deleted

        # Validate the Catalogue DELETE Call
        mock_delete.assert_awaited_once_with(
            CATALOGUE_ENDPOINT,
            params={"node": node, "disease": disease, "path": path},
            headers={"Content-Type": "application/json"},
        )

@pytest.mark.asyncio
async def test_remove_dataset_not_found(setup_test_env):
    """Test dataset removal with a non-existing file."""
    node = "test_node"
    disease = "test_disease"
    path = "/tmp/non_existing_dataset.csv"  # File does not exist

    # Mock Data Catalogue DELETE Request
    with patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_delete:
        # The external service should not be called because the file is missing
        mock_delete.return_value.status_code = 404

        # Use an AsyncClient to send the DELETE request
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.delete(
                "/dataset",
                params={"node": node, "disease": disease, "path": path}
            )

        # Assertions for the DELETE request
        assert response.status_code == 404
        assert response.json()["detail"] == "File not found in local storage"

        # Ensure the external service is not called
        mock_delete.assert_not_awaited()
