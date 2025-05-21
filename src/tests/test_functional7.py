# test_upload_minio_direct.py

import pandas as pd
import uuid
from utils import save_dataframe_to_minio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_save_dataframe_to_minio_direct():
    # Create a dummy DataFrame
    data = {
        'name': ['Alice', 'Bob'],
        'age': [30, 25],
        'city': ['Athens', 'Thessaloniki']
    }
    df = pd.DataFrame(data)

    # Create a unique filename
    disease = "test-disease"
    node = "test-node"
    iid = str(uuid.uuid4())
    filename = f"{disease}_{node}_{iid}.csv"

    logging.info(f"Uploading DataFrame to MinIO: {filename}")

    try:
        minio_path = save_dataframe_to_minio(df, filename, node)
        logging.info(f"✅ Upload successful. File stored at: {minio_path}")
        print(f"✅ Check your MinIO bucket: {minio_path}")
    except Exception as e:
        logging.error(f"❌ Upload failed: {str(e)}")

if __name__ == "__main__":
    test_save_dataframe_to_minio_direct()
