# tests/unit.py

import io
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from utils import (
    save_dataframe_to_minio,
    remove_dataset_from_minio,
    get_dataset_from_minio,
)
from minio.error import S3Error
from http.client import HTTPResponse

@pytest.fixture
def sample_df():
    return pd.DataFrame({"a": [1, 2], "b": [3, 4]})


# Helper to create a valid S3Error
def make_s3error():
    return S3Error(
        code="err",
        message="msg",
        request_id="req123",
        host_id="host123",
        resource="/bucket/file",
        response=None
    )


# ---------------------------
# save_dataframe_to_minio
# ---------------------------
#@patch("utils.minio_client.put_object")
#def test_save_dataframe_to_minio_success(mock_put, sample_df):
#    mock_put.return_value = True
#    path = save_dataframe_to_minio(sample_df, "file.csv")
#    assert path == "file.csv"

@patch("utils.minio_client.put_object")
def test_save_dataframe_to_minio_failure(mock_put, sample_df):
    mock_put.side_effect = make_s3error()

    with pytest.raises(Exception):
        save_dataframe_to_minio(sample_df, "test.csv")

@patch("utils.minio_client.put_object")
def test_save_dataframe_to_minio_failure(mock_put, sample_df):
    mock_put.side_effect = make_s3error()

    with pytest.raises(Exception):
        save_dataframe_to_minio(sample_df, "file.csv")


# ---------------------------
# remove_dataset_from_minio
# ---------------------------
@patch("utils.minio_client.remove_object")
def test_remove_dataset_from_minio_success(mock_delete):
    mock_delete.return_value = True
    assert remove_dataset_from_minio("file.csv") is True


@patch("utils.minio_client.remove_object")
def test_remove_dataset_from_minio_failure(mock_delete):
    mock_delete.side_effect = make_s3error()

    with pytest.raises(Exception):
        remove_dataset_from_minio("file.csv")


# ---------------------------
# get_dataset_from_minio
# ---------------------------
@patch("utils.minio_client.get_object")
def test_get_dataset_from_minio_success(mock_get):
    csv_content = "a,b\n1,2\n"
    mock_response = MagicMock()
    mock_response.read.return_value = csv_content.encode("utf-8")

    mock_get.return_value = mock_response

    df = get_dataset_from_minio("file.csv")
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["a"] == 1


@patch("utils.minio_client.get_object")
def test_get_dataset_from_minio_not_found(mock_get):
    mock_get.side_effect = make_s3error()

    with pytest.raises(Exception):
        get_dataset_from_minio("file.csv")
