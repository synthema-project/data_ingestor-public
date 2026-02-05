'''
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# upload an example csv data
file_path = "tests/example_data/AML_DATA_ES.csv"

async def test_upload_dataset_success():
    with open(file_path, "rb") as f:
        response = client.post(
            "/dataset",
            files={"file": ("sample.csv", f, "text/csv")},
            data={
                "use_case": "aml1", #related to schema
                "metadata": "{}" #metadata
            }
        )
    assert response.status_code == 200
'''
import pytest
from fastapi.testclient import TestClient
from fastapi.responses import StreamingResponse
from main import app
import io
import os

client = TestClient(app)

# Path to example CSV
CSV_FILE = "tests/example_data/AML_DATA_ES.csv"
BAD_CSV_FILE = "tests/example_data/AML_DATA_BAD.csv"  # intentionally invalid

# -----------------------------
# 1. Test upload success
# -----------------------------
def test_upload_dataset_success():
    with open(CSV_FILE, "rb") as f:
        response = client.post(
            "/dataset",
            files={"file": ("sample.csv", f, "text/csv")},
            data={"use_case": "aml1", "metadata": "{}"}
        )
    assert response.status_code == 200
    json_resp = response.json()
    assert "message" in json_resp
    assert "filename" in json_resp
    # Save filename for next tests
    global uploaded_filename
    uploaded_filename = json_resp["filename"]


# -----------------------------
# 2. Test upload failure (wrong file type)
# -----------------------------
def test_upload_dataset_wrong_file():
    file_bytes = io.BytesIO(b"not,a,csv")
    response = client.post(
        "/dataset",
        files={"file": ("sample.txt", file_bytes, "text/plain")},
        data={"use_case": "aml1", "metadata": "{}"}
    )
    assert response.status_code == 400
    assert "Only CSV files" in response.json()["detail"]


# -----------------------------
# 3. Test download success
# -----------------------------
def test_get_dataset_success():
    # must have uploaded a file first
    global uploaded_filename
    response = client.get("/dataset", params={"filename": uploaded_filename})
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == f"attachment; filename={uploaded_filename}"
    content = response.content.decode("utf-8")
    assert "ID" in content  # simple check that CSV header exists


# -----------------------------
# 4. Test download failure (file not found)
# -----------------------------
def test_get_dataset_not_found():
    response = client.get("/dataset", params={"filename": "non_existent.csv"})
    assert response.status_code == 500  # your main.py returns 500 if MinIO missing


# -----------------------------
# 5. Test delete success
# -----------------------------
def test_delete_dataset_success(monkeypatch):
    global uploaded_filename

    # monkeypatch remove_dataset_from_minio to simulate deletion
    def fake_remove_dataset_from_minio(filename):
        assert filename == uploaded_filename
        return True

    monkeypatch.setattr("main.remove_dataset_from_minio", fake_remove_dataset_from_minio)

    # monkeypatch httpx.AsyncClient.delete to simulate catalogue removal
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

    response = client.delete("/dataset", params={"filename": uploaded_filename})
    assert response.status_code == 200
    assert response.json()["message"].startswith("Dataset removed")


# -----------------------------
# 6. Test delete failure (file not found)
# -----------------------------
def test_delete_dataset_not_found(monkeypatch):
    def fake_remove_dataset_from_minio(filename):
        return False  # simulate missing file

    monkeypatch.setattr("main.remove_dataset_from_minio", fake_remove_dataset_from_minio)

    response = client.delete("/dataset", params={"filename": "non_existent.csv"})
    assert response.status_code == 404
    assert "Dataset not found" in response.json()["detail"]
