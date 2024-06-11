import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_dataset():
    # Read the CSV file content
    with open('example_data/test.csv', 'r') as file:
        csv_content = file.read()
    
    # Prepare the files parameter for the upload
    files = {'file': ('test.csv', csv_content, 'text/csv')}
    response = client.post("/dataset", data={"node": "node1", "disease": "test_disease"}, files=files)
    assert response.status_code == 200
    assert "Dataset uploaded and validated successfully" in response.json().get("message")

def test_remove_dataset():
    response = client.delete("/dataset", params={"node": "node1", "disease": "test_disease", "path": "/app/data/dataset/local_datasets/node1/test.csv"})
    assert response.status_code == 200
    assert "Dataset removed successfully" in response.json().get("message")
