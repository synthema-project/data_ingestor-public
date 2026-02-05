import pytest
import pandas as pd
import io
import json
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_upload_dataset_mocked_services(monkeypatch):

    # -----------------------
    # Build CSV in memory
    # -----------------------
    df = pd.DataFrame({
        "ID": ["P1", "P2"],
        "WHO 2016": ["AML", "AML"],
        "KARYOTYPE": ["46,XY", "46,XX"],
        "ASXL1": [0, 1]
    })

    buf = io.StringIO()
    df.to_csv(buf, sep=";", index=False)
    csv_bytes = buf.getvalue().encode("latin1")

    # -----------------------
    # Fake schema service
    # -----------------------
    fake_schema = {
        "data": {
            "clinical": {"ID": ["string"], "WHO 2016": ["category"]},
            "karyotype": {"KARYOTYPE": ["string"]},
            "mutations": {"ASXL1": ["int"]}
        }
    }

    class FakeSchemaResponse:
        status_code = 200
        def json(self):
            return {"schema": fake_schema}

    # -----------------------
    # Fake catalogue response
    # -----------------------
    class FakeCatalogueResponse:
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
            return FakeCatalogueResponse()

    monkeypatch.setattr("main.httpx.AsyncClient", FakeAsyncClient)

    # -----------------------
    # Fake minio save
    # -----------------------
    async def fake_save(df, name):
        return name

    monkeypatch.setattr("utils.save_dataframe_to_minio", fake_save)

    # -----------------------
    # Metadata
    # -----------------------
    metadata = {
        "title": "Test dataset",
        "description": "desc",
        "publisher": {
            "name": "Org",
            "mail": "a@b.com",
            "url": "x",
            "type": "org",
            "note": "n"
        },
        "accessRights": "public",
        "contactPoint": "a@b.com",
        "theme": "health",
        "keyword": "aml",
        "license": "MIT",
        "conformsTo": "schema",
        "language": "en",
        "spatial": "EU",
        "temporal": {"startDate": "2020", "endDate": "2024"}
    }

    # -----------------------
    # Call API
    # -----------------------
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/dataset",
            files={"file": ("data.csv", csv_bytes, "text/csv")},
            data={
                "use_case": "aml1",
                "metadata": json.dumps(metadata)
            }
        )

    # -----------------------
    # Assertions
    # -----------------------
    assert response.status_code == 200
    assert response.json()["message"] == "Dataset uploaded and validated successfully"
