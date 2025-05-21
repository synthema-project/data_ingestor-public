import pytest
from httpx import AsyncClient
from main import app
from minio import Minio
import pandas as pd
import io
import uuid
import os

@pytest.mark.asyncio
async def test_real_upload_to_minio_persists():
    # Setup MinIO client
    minio_client = Minio(
        endpoint=os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=True
    )
    bucket_name = os.getenv("MINIO_BUCKET_NAME")

    # Set unique node/disease
    node = "test-node"
    disease = "test-disease"
    iid = str(uuid.uuid4())
    filename_prefix = f"{disease}_{node}_"

    # Prepare test CSV file
    df = pd.DataFrame({
        "patient_id": [1, 2, 3],
        "age": [25, 45, 67],
        "diagnosis": ["positive", "negative", "positive"]
    })

    csv_io = io.StringIO()
    df.to_csv(csv_io, sep=';', index=False)
    csv_bytes = csv_io.getvalue().encode("latin1")

    # Upload via FastAPI endpoint
    async with AsyncClient(app=app, base_url="http://test") as ac:
        files = {
            "file": ("test.csv", csv_bytes, "text/csv")
        }
        response = await ac.post(
            "/dataset",
            params={"node": node, "disease": disease},
            files=files
        )

    assert response.status_code == 200, f"Upload failed: {response.text}"

#@pytest.mark.asyncio
#async def test_upload_and_delete_real_minio():
#    # Setup: MinIO client and test values
#    minio_client = Minio(
#        endpoint=os.getenv("MINIO_ENDPOINT"),
#        access_key=os.getenv("MINIO_ACCESS_KEY"),
#        secret_key=os.getenv("MINIO_SECRET_KEY"),
#        secure=True
#    )
#    bucket_name = os.getenv("MINIO_BUCKET_NAME")
#    node = "test-node"
#    disease = "test-disease"
#    iid = str(uuid.uuid4())
#    filename = f"{disease}_{node}_{iid}.csv"
#    object_path = f"{node}/{filename}"#

    # Create test DataFrame
#    df = pd.DataFrame({
#        "patient_id": [1, 2],
#        "age": [30, 45],
#        "diagnosis": ["positive", "negative"]
#    })

#    # Convert to CSV bytes for upload
#    csv_buffer = io.StringIO()
#    df.to_csv(csv_buffer, index=False, sep=';')
#    csv_buffer.seek(0)
#    csv_bytes = csv_buffer.getvalue().encode("latin1")

    # Upload via FastAPI
#    async with AsyncClient(app=app, base_url="http://test") as ac:
#        files = {
#            "file": ("test.csv", csv_bytes, "text/csv")
#        }
#        response = await ac.post(
#            "/dataset",
#            params={"node": node, "disease": disease},
#            files=files
#        )

#    assert response.status_code == 200, response.text
#    assert minio_client.stat_object(bucket_name, object_path)

#    # Delete via FastAPI
#    ##async with AsyncClient(app=app, base_url="http://test") as ac:
#    ##    response = await ac.delete(
#    ##        "/dataset",
#    ##       params={"node": node, "disease": disease, "filename": filename}
#    ##    )

#    ##assert response.status_code == 200

#    # Ensure file no longer exists
#    with pytest.raises(Exception):
#        minio_client.stat_object(bucket_name, object_path)
