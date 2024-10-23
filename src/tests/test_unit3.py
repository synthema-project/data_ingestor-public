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
client = TestClient(app)#, transport=WSGITransport(app=app))

def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@mock.patch("main.LOCAL_DATASETS_DIR", new="/mocked/local_datasets")
@mock.patch("main.os.remove")
@mock.patch("main.save_dataframe_as_csv")
@mock.patch("os.makedirs")  # Mock directory creation
def test_upload_dataset(mock_makedirs, mock_save_csv, mock_os_remove):
    create_test_db_and_tables()  # Ensure the database is set up before running the test

    # Mock the save_dataframe_as_csv to simulate saving to a fake folder
    mock_save_csv.return_value = "/mocked/local_datasets/node1/AML_node1_mocked.csv"

    csv_path = current_dir / "example_data" / "AML_DATA_ES.csv"
    with open(csv_path, "rb") as csv_file:
        response = client.post(
            "/dataset",
            data={"node": "node1", "disease": "AML"},
            files={"file": ("dataset_uploaded.csv", csv_file, "text/csv")},
        )

    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert "Dataset uploaded and validated successfully" in response.json().get("message", "")

    # Check if the mock save method was called with the expected arguments
    mock_save_csv.assert_called_once()
    # Check if os.remove was called to clean up temporary CSV file
    mock_os_remove.assert_called_once()

@mock.patch("main.LOCAL_DATASETS_DIR", new="/mocked/local_datasets")
@mock.patch("main.os.remove")
@mock.patch("os.makedirs")  # Mock directory creation
def test_remove_dataset(mock_makedirs, mock_os_remove):
    create_test_db_and_tables()

    # Example payload to remove a dataset
    remove_data = {
        "node": "node1",
        "disease": "AML",
        "path": "/mocked/local_datasets/node1/AML_node1_mocked.csv"
    }

    response = client.request("DELETE", "/dataset", json=remove_data)
    
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert response.json() == {"message": "Dataset removed successfully from both database and local storage"}
    
    # Ensure the mock os.remove was called with the expected path
    mock_os_remove.assert_called_once_with("/mocked/local_datasets/node1/AML_node1_mocked.csv")

def test_schema_insertion():
    create_test_db_and_tables()
    session = Session(engine)
    dataset = DatasetSchema(disease="AML", data='{"schema": "test"}')
    session.add(dataset)
    session.commit()

    # Use session.exec instead of session.query
    saved_dataset = session.exec(
        "SELECT * FROM datasetschema WHERE disease = 'AML'"
    ).first()
    
    assert saved_dataset is not None
    assert saved_dataset.disease == "AML"

if __name__ == "__main__":
    test_healthcheck()
    test_upload_dataset()
    test_remove_dataset()
    test_schema_insertion()
