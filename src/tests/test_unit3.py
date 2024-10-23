import os
import json
import shutil
from pathlib import Path
from unittest import mock
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from main import app
from database import get_session
from models import DatasetSchema, NodeDatasetInfo
from httpx import WSGITransport
import tempfile  # To create temporary directories for mocking

# Set up an SQLite in-memory database for testing
TEST_DATABASE_URL = "sqlite:///./test.db"  # Use SQLite for testing
engine = create_engine(TEST_DATABASE_URL, echo=True)

# Path for example data
current_dir = Path(__file__).resolve().parent

# Override the session dependency to use the SQLite database instead of PostgreSQL
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

# Create database and tables for the test
def create_test_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Test client for FastAPI
client = TestClient(app)

def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

import tempfile

@mock.patch("main.os.makedirs")  # Mock directory creation
@mock.patch("main.os.path.exists", return_value=True)  # Mock that the directory already exists
@mock.patch("main.os.remove")
@mock.patch("main.save_dataframe_as_csv")  # Mock the CSV saving function
def test_upload_dataset(mock_save_csv, mock_os_remove, mock_exists, mock_makedirs):
    create_test_db_and_tables()

    # Use a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        mock_save_csv.return_value = f"{tmp_dir}/node1/AML_node1_mocked.csv"  # Mock the path
        
        # Test data file
        csv_path = current_dir / "example_data" / "AML_DATA_ES.csv"
        
        with open(csv_path, "rb") as csv_file:
            # Post the request with the temporary directory as 'local_datasets_dir'
            response = client.post(
                "/dataset",
                data={"node": "node1", "disease": "AML", "local_datasets_dir": tmp_dir},
                files={"file": ("AML_DATA_ES.csv", csv_file, "text/csv")},
            )

        # Assertions
        # Log or print the response content to inspect the error details
        print(f"Response Content: {response.content}")
        
        # Assertions
        assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
        mock_makedirs.assert_called_once_with(f"{tmp_dir}/node1", exist_ok=True)
        mock_save_csv.assert_called_once()

#@mock.patch("main.LOCAL_DATASETS_DIR", new="/mocked/local_datasets")
#@mock.patch("main.os.remove")
#@mock.patch("os.makedirs")  # Mock directory creation
#def test_remove_dataset(mock_makedirs, mock_os_remove):
#    create_test_db_and_tables()#
#
#    remove_data = {
#        "node": "node1",
#        "disease": "AML",
#        "path": "/mocked/local_datasets/node1/AML_node1_mocked.csv"
#    }

#    response = client.request("DELETE", "/dataset", json=remove_data)
    
#    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
#    assert response.json() == {"message": "Dataset removed successfully from both database and local storage"}
    
    # Ensure the mock os.remove was called with the expected path
#    mock_os_remove.assert_called_once_with("/mocked/local_datasets/node1/AML_node1_mocked.csv")

if __name__ == "__main__":
    test_healthcheck()
    test_upload_dataset()
#    test_remove_dataset()
