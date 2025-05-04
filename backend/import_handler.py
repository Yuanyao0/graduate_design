import pandas as pd
import os
from config import UPLOAD_FOLDER
from models import db, Attrengname

def handle_excel(data, filepath):
    field_map = data["fields"]
    column_indices = data["enabledIndices"]
    ranges = []
    df = pd.read_excel(filepath)
    rename_dict = {(f["oldName"], f["newName"]) for f in field_map}
    ranges.append(df.loc[df.index[1:], "实测经度"].min())
    ranges.append(df.loc[df.index[1:], "实测经度"].max())
    ranges.append(df.loc[df.index[1:], "实测纬度"].min())
    ranges.append(df.loc[df.index[1:], "实测纬度"].max())
    rename = [f["newName"] for f in field_map]
    df_selected = df.iloc[:, column_indices]
    df_selected.columns = rename
    records = df_selected.iloc[1:].to_dict(orient="records")
    return ranges, records, rename_dict


def parse_import(data):
    filename = data["filename"]
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if filename.endswith('.xlsx'):
        ranges, records, rename_dict = handle_excel(data,filepath)
        return ranges, records, rename_dict


