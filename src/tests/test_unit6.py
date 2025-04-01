import os
import pytest
from pathlib import Path 
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.orm import Session
from models import NodeDatasetInfo
from sqlmodel import SQLModel, create_engine, Session as TestSession
from tempfile import TemporaryDirectory
from storage import minio_client

# Get the directory path of the current script
current_dir = Path(__file__).resolve().parent

def test_bucket_exists():
    print('BUCKET EXISTS')
    assert minio_client.bucket_exists("data-annotation") is True

#Test Client for the FastAPI app
client = TestClient(app)

def test_upload_dataset():
    file_path = current_dir / "example_data" / "AML_DATASET_ES.csv"   
    with open(file_path, "rb") as file:
      response = client.post(
          "/dataset",
          files={"file": ("AML_DATA_ES.csv", file, "text/csv")},
          data={"node": "test_node", "disease": "test_disease"},
      )

    assert response.status_code == 200
    assert "Dataset uploaded and validated successfully" in response.json()["message"]

