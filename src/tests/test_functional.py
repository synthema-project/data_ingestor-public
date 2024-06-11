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
    with open('tests/example_data/AML_DATA_ES.csv', 'r') as file:
        csv_content = file.read()
    
    # Prepare the files parameter for the upload
    files = {'file': ('AML_DATA_ES.csv', csv_content, 'text/csv')}
    
    # Prepare the payload data for the upload
    payload = {"node": "node1", "disease": "AML"}
    
    # Send the request to the endpoint
    response = client.post("/dataset", data=payload, files=files)
    
    # Check if the response status code is 200
    assert response.status_code == 200
    
    # Check if the response message contains "Dataset uploaded and validated successfully"
    assert "Dataset uploaded and validated successfully" in response.json().get("message")

def test_remove_dataset():
    response = client.delete("/dataset", params={"node": "node1", "disease": "AML", "path": "/app/data/dataset/local_datasets/node1/AML_ES.csv"})
    assert response.status_code == 200
    assert "Dataset removed successfully" in response.json().get("message")
