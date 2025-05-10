import pandas as pd
import os
from config import UPLOAD_FOLDER
from models import Attr
import math
import numpy as np


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'xlsx', 'csv', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file(data):
    col_names = data.iloc[0]
    units = data.iloc[1]
    fields = {}
    for name, unit in zip(col_names, units):
        fields[name] = unit
    return fields


def parse_import(filename, rename_dict):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if filename.endswith('.xlsx'):
        data = pd.read_excel(filepath)
    if filename.endswith('.csv'):
        data = pd.read_csv(filepath)
    if filename.endswith('.txt'):
        data = pd.read_csv(filepath, sep='\t')
    cols = list(rename_dict.keys())
    datatype = {}
    for key,val in rename_dict.items():
        attr = Attr.query.filter_by(engName=val).first()
        datatype[key] = attr.datatype
    df_selected = data[cols]
    df_selected.drop(0, inplace=True)
    for col in df_selected.columns:
        if datatype[col] == 'float':
            df_selected[col] = df_selected[col].apply(lambda x: pd.to_numeric(x, errors='coerce') if not pd.isna(x) and str(x).strip() != '' else x)
        elif datatype[col] == 'int':
            df_selected[col] = df_selected[col].apply(lambda x: pd.to_numeric(x, errors='coerce') if not pd.isna(x) and str(x).strip() != '' else x)
        elif datatype[col] == 'date':
            def try_parse_date(val):
                try:
                    return pd.to_datetime(val)
                except Exception:
                    return val  # 出错保留原值
            df_selected[col] = df_selected[col].apply(try_parse_date)
        elif datatype[col] == 'string':
            df_selected[col] = df_selected[col].astype(str)

    df_selected.rename(columns=rename_dict, inplace=True)
    records = df_selected.to_dict(orient="records")
    return records

def parse_file(fname):
    if fname and allowed_file(fname):
        filepath = os.path.join(UPLOAD_FOLDER, fname)
        if fname.endswith('.xlsx'):
            data = pd.read_excel(filepath, header=None)
            fields = handle_file(data)
        if fname.endswith('csv'):
            data = pd.read_csv(filepath, header=None)
            fields = handle_file(data)
        if fname.endswith('txt'):
            data = pd.read_csv(filepath, sep='\t', header=None)
            fields = handle_file(data)
        # print(fields)
        return fields
    else:
        return []
