# tests/func.py
import json
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture
def valid_schema():
    return {
        "data": {
            "clinical": {
                "ID": ["string"],
                "WHO 2016": ["category"]
            },
            "karyotype": {
                "KARYOTYPE": ["string"]
            },
            "mutations": {
                "ASXL1": ["int"]
            }
        }
    }


@pytest.fixture
def valid_metadata():
    return {
        "title": "AML dataset",
        "description": "test dataset",
        "publisher": {
            "name": "Org",
            "mail": "mail@org.com",
            "type": "org",
            "note": "note",
            "url": "http://org.com"
        },
        "contactPoint": "mail@org.com",
        "theme": "health",
        "keyword": "aml",
        "accessRights": "public",
        "license": "MIT",
        "conformsTo": "schema",
        "language": "en",
        "spatial": "EU",
        "temporal": {"startDate": "2020", "endDate": "2021"}
    }


@pytest.fixture
def real_csv_file(tmp_path):
    p = tmp_path / "dataset.csv"
    p.write_text(
        "ID;WHO 2016;KARYOTYPE;ASXL1\n"
        "1;AML;46,XY;0\n"
        "2;AML;46,XX;1\n"
    )
    return p


# -----------------------------
# Functional Upload Test
# -----------------------------

def test_upload_dataset(
    monkeypatch,
    real_csv_file,
    valid_schema,
    valid_metadata
):

    # ---- Mock annotation service ----
    class FakeSchemaResponse:
        status_code = 200
        def json(self):
            return {"schema": valid_schema}

    async def fake_get(url):
        return FakeSchemaResponse()

    # ---- Mock catalogue service ----
    class FakePostResponse:
        status_code = 200
        text = "ok"

    async def fake_post(url, json):
        return FakePostResponse()

    # ---- Mock minio save ----
    async def fake_save(df, name):
        return name

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
    monkeypatch.setattr("httpx.AsyncClient.post", fake_post)
    monkeypatch.setattr("utils.save_dataframe_to_minio", fake_save)

    with open(real_csv_file, "rb") as f:
        r = client.post(
            "/dataset",
            files={"file": ("dataset.csv", f, "text/csv")},
            data={
                "use_case": "aml1",
                "metadata": json.dumps(valid_metadata)
            }
        )

    assert r.status_code == 200
    assert "filename" in r.json()
