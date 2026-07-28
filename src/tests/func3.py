import pytest
import io
import pandas as pd
import json
import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

uploaded_filename = None  # global to share between tests

def test_upload_dataset_success(monkeypatch):
    global uploaded_filename

    # --- Setup CSV in-memory ---
    df = pd.DataFrame({
        "ID": ["PD8122a", "PD8577a"],
        "WHO 2016": [12, 12],
        "KARYOTYPE": ["46,XY", "46,XX"],
        "ASXL1": [0, 1]
    })
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, sep=';', index=False)
    csv_bytes = csv_buffer.getvalue().encode("latin1")

    # --- Mock MinIO save ---
    async def fake_save(df, filename):
        return filename

    monkeypatch.setattr("utils.save_dataframe_to_minio", fake_save)

    # --- Mock validate_data ---
    monkeypatch.setattr("utils.validate_data", lambda data, schema: None)

    # --- Mock HTTPX async client ---
    class FakeResponse:
        status_code = 200
        text = "ok"
        def json(self):
            return {"schema": {"data": {"clinical": {"ID": ["string"]}, "karyotype": {}, "mutations": {}}}}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        async def get(self, url):
            return FakeResponse()
        async def post(self, url, json):
            return FakeResponse()

    monkeypatch.setattr("main.httpx.AsyncClient", FakeAsyncClient)

    # --- Perform upload ---
    response = client.post(
        "/dataset",
        files={"file": ("sample.csv", csv_bytes, "text/csv")},
        data={"use_case": "aml1", "metadata": "{}"}
    )

    assert response.status_code == 200
    uploaded_filename = response.json()["filename"]  # store for next tests

def test_get_dataset_success():
    global uploaded_filename
    response = client.get("/dataset", params={"filename": uploaded_filename})
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

def test_delete_dataset_success(monkeypatch):
    global uploaded_filename

    # --- Mock remove_dataset_from_minio ---
    def fake_remove_dataset(filename):
        assert filename == uploaded_filename
        return True
    monkeypatch.setattr("main.remove_dataset_from_minio", fake_remove_dataset)

    # --- Mock HTTPX delete to catalogue ---
    class FakeDeleteResponse:
        status_code = 200
        def raise_for_status(self):
            pass

    class FakeAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        async def delete(self, url, params=None):
            return FakeDeleteResponse()

    monkeypatch.setattr("main.httpx.AsyncClient", FakeAsyncClient)

    # --- Perform delete ---
    response = client.delete("/dataset", params={"filename": uploaded_filename})
    assert response.status_code == 200
    assert response.json()["message"] == "Dataset removed successfully"

