import io
import pandas as pd
import pytest
from fastapi import HTTPException
from csv_input import read_csv_input


@pytest.mark.parametrize('delimiter', [',', ';', '\t', '|'])
def test_upload_delimiters_preserve_columns(delimiter):
    raw = delimiter.join(['', 'Age', 'Gender'])+'\n'+delimiter.join(['id1','43','1'])+'\n'
    frame = read_csv_input(raw.encode())
    assert list(frame.columns) == ['Age','Gender']
    assert frame.iloc[0].tolist() == [43,1]


def test_quoted_commas_and_utf8_bom():
    frame = read_csv_input('\ufeffAge,Note\n43,"comma, in text"\n'.encode())
    assert frame.iloc[0]['Note'] == 'comma, in text'


def test_old_one_column_serialization_rejected():
    raw = pd.DataFrame({'Age,Gender':['43,1']}).to_csv(index=False).encode()
    with pytest.raises(HTTPException) as error:
        read_csv_input(raw)
    assert error.value.status_code == 400


def test_empty_csv_rejected():
    with pytest.raises(HTTPException):
        read_csv_input(b'Age,Gender\n')
