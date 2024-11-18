import os
import json
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from main import app
from database import get_session

# Set up an SQLite in-memory database for testing
TEST_DATABASE_URL = "sqlite:///./test.db"  # Use SQLite for testing
engine = create_engine(TEST_DATABASE_URL, echo=True)

# Path for example data
current_dir = Path(__file__).resolve().parent
example_data_dir = current_dir / "example_data"

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

# Base URL for the API (assuming external API endpoints)
ANNOTATION_ENDPOINT = "http://data-annotation-service.synthema-dev/schema" 
CATALOGUE_ENDPOINT = "http://data-catalogue-service.synthema-dev:83/metadata" 

def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_dataset():
    create_test_db_and_tables()
    csv_path = example_data_dir / "AML_DATA_ES.csv"
    with open(csv_path, "rb") as csv_file:
        response = client.post(
            "/dataset",
            data={"node": "node1", "disease": "AML"},
            files={"file": ("sample_dataset.csv", csv_file, "text/csv")},
        )
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert "Dataset uploaded and validated successfully" in response.json().get("message", "")

def test_remove_dataset():
    create_test_db_and_tables()
    remove_data = {
        "node": "node1",
        "disease": "AML",
        "path": "/app/datasets/node1/AML_node1_xxx.csv"
    }
    response = client.delete("/dataset", params=remove_data)#data=json.dumps(remove_data))#json=remove_data)
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert response.json() == {"message": "Dataset removed successfully from both database and local storage"}

if __name__ == "__main__":
    test_healthcheck()
    test_upload_dataset()
    test_remove_dataset()

