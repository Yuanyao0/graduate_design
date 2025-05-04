import os
import pandas as pd
from config import UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_excel(fpath):
    data = pd.read_excel(fpath, header=None)
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
            fields = handle_excel(filepath)
        # print(fields)
        return fields
    else:
        return []