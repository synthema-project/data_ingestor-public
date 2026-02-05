import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
file_path = "tests/example_data/AML_DATA_ES.csv"
def test_upload_dataset():
    with open(file_path, "rb") as f:
        response = client.post(
            "/dataset",
            files={"file": ("sample.csv", f, "text/csv")},
            data={
                "use_case": "aml1",
                "metadata": "{}"
            }
        )
    assert response.status_code == 200
    #assert response.json() == {"name": "bar", "description": "A new item"}
