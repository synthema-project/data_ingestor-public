import io
import os
import json
import uuid
import pytest
import pandas as pd
from httpx import AsyncClient
from minio import Minio
from main import app

@pytest.mark.asyncio
async def test_real_upload_to_minio_persists():

    # -------------------------
    # Environment
    # -------------------------
    minio_client = Minio(
        endpoint=os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False   # usually False in docker
    )

    bucket = os.getenv("MINIO_BUCKET_NAME")

    use_case = "aml1"

    # -------------------------
    # Metadata (valid pydantic)
    # -------------------------
    metadata = {
        "title": "Test Dataset",
        "description": "integration test",
        "publisher": {
            "name": "Org",
            "url": "https://org.org",
            "mail": "mail@org.com",
            "type": "org",
            "note": "note"
        },
        "contactPoint": "mail@org.com",
        "theme": "health",
        "keyword": "aml",
        "accessRights": "public",
        "license": "MIT",
        "conformsTo": "schema",
        "language": "en",
        "spatial": "EU",
        "temporal": {"startDate": "2020", "endDate": "2024"}
    }

    # -------------------------
    # CSV data
    # -------------------------
    df = pd.DataFrame({
        "ID": ["P1", "P2"],
        "WHO 2016": ["AML", "AML"],
        "KARYOTYPE": ["46,XY", "46,XX"],
        "ASXL1": [0, 1]
    })

    csv_io = io.StringIO()
    df.to_csv(csv_io, sep=";", index=False)
    csv_bytes = csv_io.getvalue().encode("latin1")

    # -------------------------
    # Call API
    # -------------------------
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/dataset",
            files={"file": ("dataset.csv", csv_bytes, "text/csv")},
            data={
                "use_case": use_case,
                "metadata": json.dumps(metadata)
            }
        )

    # -------------------------
    # Assertions
    # -------------------------
    assert response.status_code == 200, response.text

    payload = response.json()
    assert "filename" in payload

    object_name = payload["filename"]

    # -------------------------
    # Verify in MinIO
    # -------------------------
    stat = minio_client.stat_object(bucket, object_name)
    assert stat.size > 0
