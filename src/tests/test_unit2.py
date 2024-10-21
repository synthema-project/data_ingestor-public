import os
import json
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from main import app
from database import get_session
from models import DatasetSchema, NodeDatasetInfo

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

def test_upload_dataset():
    create_test_db_and_tables()  # Ensure the database is set up before running the test
    csv_path = current_dir / "example_data" / "AML_DATA_ES.csv"
    with open(csv_path, "rb") as csv_file:
        response = client.post(
            "/dataset",
            data={"node": "node1", "disease": "AML"},
            files={"file": ("AML_DATA_ES.csv", csv_file, "text/csv")},
        )
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert "Dataset uploaded and validated successfully" in response.json().get("message", "")

def test_remove_dataset():
    create_test_db_and_tables()
    remove_data = {
        "node": "node1",
        "disease": "AML",
        "path": "/app/data/dataset/local_datasets/node1/AML_node1_xxx.csv"
    }
    response = client.delete("/dataset", json=remove_data)
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert response.json() == {"message": "Dataset removed successfully from both database and local storage"}

def test_schema_insertion():
    session = Session(engine)
    dataset = DatasetSchema(disease="AML", data='{"schema": "test"}')
    session.add(dataset)
    session.commit()
    saved_dataset = session.query(DatasetSchema).filter(DatasetSchema.disease == "AML").first()
    assert saved_dataset is not None
    assert saved_dataset.disease == "AML"

if __name__ == "__main__":
    test_healthcheck()
    test_upload_dataset()
    test_remove_dataset()
    test_schema_insertion()

