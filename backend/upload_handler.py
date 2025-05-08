import os
import pandas as pd
from config import UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'xlsx', 'csv', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file(data):
    col_names = data.iloc[0]
    units = data.iloc[1]
    # 拼接列名与单位
    fields = []
    for name, unit in zip(col_names, units):
        if pd.isna(unit):
            fields.append(str(name))
        else:
            fields.append(f"{name} ({unit})")
    return fields

def parse_file(file):
    fname = file.filename 
    if file and allowed_file(fname):
        filepath = os.path.join(UPLOAD_FOLDER, fname)
        file.save(filepath)
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