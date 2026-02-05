# tests/func.py
import json
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# -----------------------------
# Fixtures
# -----------------------------
'''
def test_upload_csv_from_file(monkeypatch):
    # Path to real CSV in repo
    file_path = "tests/example_data/AML_DATA_ES.csv"

    # Mock external calls
    async def fake_save(df, name):
        return f"{name}"

    monkeypatch.setattr("utils.save_dataframe_to_minio", fake_save)
    monkeypatch.setattr("utils.validate_data", lambda data, schema: None)
    monkeypatch.setattr("httpx.AsyncClient.post", lambda *a, **k: None)

    with open(file_path, "rb") as f:
        r = client.post(
            "/dataset",
            files={"file": ("sample.csv", f, "text/csv")},
            data={"use_case": "aml1", "metadata": "{}"}
        )

    assert r.status_code == 200
'''
def test_upload_csv_from_file(monkeypatch):
    file_path = "tests/example_data/AML_DATA_ES.csv"

    # ------------------------
    # Fake HTTP client
    # ------------------------
    class FakeSchemaResponse:
        status_code = 200
        def json(self):
            return {
                "schema": {
                    "data": {
                        "clinical": {"ID": ["string"]},
                        "karyotype": {},
                        "mutations": {}
                    }
                }
            }

    class FakePostResponse:
        status_code = 200
        text = "ok"

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, url):
            return FakeSchemaResponse()

        async def post(self, url, json):
            return FakePostResponse()

    # ------------------------
    # Fake minio save
    # ------------------------
    async def fake_save(df, name):
        return name

    monkeypatch.setattr("httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr("utils.save_dataframe_to_minio", fake_save)
    monkeypatch.setattr("utils.validate_data", lambda data, schema: None)

    with open(file_path, "rb") as f:
        r = client.post(
            "/dataset",
            files={"file": ("sample.csv", f, "text/csv")},
            data={
                "use_case": "aml1",
                "metadata": "{}"
            }
        )

    assert r.status_code == 200
