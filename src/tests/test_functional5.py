import pytest
import pandas as pd
import io
from httpx import AsyncClient
from main import app
import uuid
import os

@pytest.mark.asyncio
async def test_upload_dataset_to_minio(monkeypatch):
    # --- Setup CSV file in-memory
    df = pd.DataFrame({
        "age": [25, 30],
        "gender": ["male", "female"],
        "status": ["sick", "healthy"]
    })
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, sep=';')
    csv_buffer.seek(0)
    
    # --- Create a mock response for the schema endpoint
    schema_response = {
        "schema": {
            "type": "object",
            "properties": {
                "age": {"type": "integer"},
                "gender": {"type": "string"},
                "status": {"type": "string"}
            },
            "required": ["age", "gender", "status"]
        }
    }

    async def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            def json(self):
                return schema_response
        return MockResponse()

    async def mock_post(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

    # --- Use test client to upload
    node = "test-node"
    disease = "test-disease"
    csv_filename = f"{uuid.uuid4()}.csv"
    csv_bytes = csv_buffer.getvalue().encode("latin1")

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/dataset",
            data={"node": node, "disease": disease},
            files={"file": (csv_filename, csv_bytes, "text/csv")}
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Dataset uploaded and validated successfully"
