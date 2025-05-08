import pandas as pd
import os
from config import UPLOAD_FOLDER
from models import db, Attrengname

def handle_import(df, field_map, column_indices):
    ranges = []
    rename_dict = {(f["oldName"], f["newName"]) for f in field_map}
    ranges.append(df.loc[df.index[1:], "实测经度"].min())
    ranges.append(df.loc[df.index[1:], "实测经度"].max())
    ranges.append(df.loc[df.index[1:], "实测纬度"].min())
    ranges.append(df.loc[df.index[1:], "实测纬度"].max())
    rename = [f["newName"] for f in field_map]
    df_selected = df.iloc[:, column_indices]
    df_selected.columns = rename
    for col in df_selected.columns:
        df_selected[col] = pd.to_datetime(df_selected[col], errors='ignore')
        df_selected[col] = pd.to_numeric(df_selected[col], errors='ignore')
    records = df_selected.iloc[1:].to_dict(orient="records")
    return ranges, records, rename_dict


def parse_import(data):
    filename = data["filename"]
    field_map = data["fields"]
    column_indices = data["enabledIndices"]
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if filename.endswith('.xlsx'):
        data = pd.read_excel(filepath)
    if filename.endswith('.csv'):
        data = pd.read_csv(filepath)
    if filename.endswith('.txt'):
        data = pd.read_csv(filepath, sep='\t')
    ranges, records, rename_dict = handle_import(data, field_map, column_indices)
    return ranges, records, rename_dict


