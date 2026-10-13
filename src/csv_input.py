"""Shared CSV reader for full and partitioned dataset uploads."""
import csv
import io

import pandas as pd
from fastapi import HTTPException


def read_csv_input(raw: bytes) -> pd.DataFrame:
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('latin1')
    try:
        delimiter = csv.Sniffer().sniff(text[:65536], delimiters=',;\t|').delimiter
        frame = pd.read_csv(io.StringIO(text), sep=delimiter)
    except (csv.Error, ValueError, pd.errors.ParserError) as error:
        raise HTTPException(status_code=400, detail=f'Invalid CSV: {error}') from error
    # Reject files that were already serialized as one quoted column by the old
    # semicolon-only reader. Repair requires the original upload, not guessing.
    if len(frame.columns) == 1 and any(s in str(frame.columns[0]) for s in (',', ';', '\t', '|')):
        raise HTTPException(status_code=400, detail='CSV contains whole rows in one column; upload the original CSV')
    frame = frame.loc[:, ~frame.columns.str.match(r'^Unnamed')]
    if frame.empty:
        raise HTTPException(status_code=400, detail='CSV has no data rows or feature columns')
    return frame
