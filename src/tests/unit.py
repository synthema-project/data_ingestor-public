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


@pytest.fixture
def sample_df():
    return pd.DataFrame({"a": [1, 2], "b": [3, 4]})


# ---------------------------------------------------
# save_dataframe_to_minio
# ---------------------------------------------------
@patch("utils.minio_client.put_object")
def test_save_dataframe_to_minio_success(mock_put, sample_df):
    mock_put.return_value = True

    result = save_dataframe_to_minio(sample_df, "test.csv")
    assert result == "test.csv"
    assert mock_put.called


@patch("utils.minio_client.put_object")
def test_save_dataframe_to_minio_failure(mock_put, sample_df):
    mock_put.side_effect = S3Error("err", "message", "request", "resource", "host")

    with pytest.raises(Exception):
        save_dataframe_to_minio(sample_df, "test.csv")


# ---------------------------------------------------
# remove_dataset_from_minio
# ---------------------------------------------------
@patch("utils.minio_client.remove_object")
def test_remove_dataset_from_minio_success(mock_delete):
    mock_delete.return_value = True
    assert remove_dataset_from_minio("test.csv") is True


@patch("utils.minio_client.remove_object")
def test_remove_dataset_from_minio_failure(mock_delete):
    mock_delete.side_effect = S3Error("err", "msg", "", "", "")
    with pytest.raises(Exception):
        remove_dataset_from_minio("test.csv")


# ---------------------------------------------------
# get_dataset_from_minio
# ---------------------------------------------------
@patch("utils.minio_client.get_object")
def test_get_dataset_from_minio_success(mock_get):
    mock_obj = MagicMock()
    mock_obj.read.return_value = b"a,b\n1,2\n"
    mock_get.return_value = mock_obj

    df = get_dataset_from_minio("test.csv")
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 2)


@patch("utils.minio_client.get_object")
def test_get_dataset_from_minio_not_found(mock_get):
    mock_get.side_effect = S3Error("err", "msg", "", "", "")

    with pytest.raises(Exception):
        get_dataset_from_minio("test.csv")
