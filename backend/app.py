from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import File
import json
import jwt
import datetime
import io
import os
import pandas as pd
import zipfile
import random
import string
import difflib
from models import db, User, File, Attr
from file_handler import parse_import, parse_file
from mongo import mongo_db, collection_map
from openpyxl.utils import get_column_letter
from flask_mail import Mail, Message
from redis_config import r
from pymongo import ASCENDING, DESCENDING
from bson.json_util import dumps


app = Flask(__name__)
app.config.from_object('config')
# app.config['SECRET_KEY'] = config.SECRET_KEY
# 暴露给前端一些自定义的响应头
CORS(app, expose_headers=["X-Download-Times"], supports_credentials=True)
# CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "http://localhost:3000"}})
db.init_app(app)
mail = Mail(app)

# 生成验证码
def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

# 装饰器，获取userid
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token is None:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            if token.startswith("Bearer "):
                token = token[7:]  # 去除前缀
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(user_id, *args, **kwargs)
    return decorated

# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = request.headers.get('Authorization')
#         if token is None:
#             print("[Token] Missing Authorization header")
#             return jsonify({'message': 'Token is missing'}), 401

#         try:
#             if token.startswith("Bearer "):
#                 token = token[7:]
#             print("[Token] Raw token:", token)
#             data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
#             print("[Token] Decoded payload:", data)
#             user_id = data['user_id']
#         except jwt.ExpiredSignatureError:
#             print("[Token] Expired")
#             return jsonify({'message': 'Token has expired'}), 401
#         except jwt.InvalidTokenError as e:
#             print("[Token] Invalid:", str(e))
#             return jsonify({'message': 'Invalid token'}), 401

#         return f(user_id, *args, **kwargs)
#     return decorated

# # 处理OPTIONS请求
# @app.route('/api/*', methods=["OPTIONS"])
# def options():
#     return jsonify({"message": "preflight check passed"}), 200

# 注册接口
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    code = data.get('code')
    hashed_password = generate_password_hash(password)

    if not all([username, email, password, code]):
        return jsonify({'message': 'All fields are required'}), 400
    # 查重
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'email already register, please login!'}), 409
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409
    real_code = r.get(f'verify:{email}')
    if not real_code or real_code != code:
        return jsonify({'message': 'Invalid or expired verification code'}), 400

    # 新建用户
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'})

@app.route('/api/sendcode', methods=['POST'])
def send_code():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'message': 'Email is required'}), 400

    cooldown_key = f'verify:cooldown:{email}'
    if r.exists(cooldown_key):
        return jsonify({'message': 'Please wait before requesting another code'}), 429

    code = generate_code()
    
    # 保存验证码（5分钟）
    r.setex(f'verify:{email}', 300, code)
    
    # 设置发送冷却（60秒）
    r.setex(cooldown_key, 60, '1')

    try:
        msg = Message("Your Verification Code", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"Your verification code is: {code} (valid for 5 minutes)"
        mail.send(msg)
        return jsonify({'message': 'Verification code sent successfully'})
    except Exception as e:
        return jsonify({'message': f'Failed to send email: {str(e)}'}), 500

# 检查邮箱是否存在
@app.route('/api/checkemail', methods=['POST'])
def checkemail():
    data = request.json
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({'message': 'email is not register, please register'}), 409
    return jsonify({'message': 'email has register'})

# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    loginways = data.get('loginways')
    if loginways == 'username':
        username = data.get('username')
        input_password = data.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, input_password):
            access_token = jwt.encode({
                'username': username,
                'user_id': user.id,
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            refresh_token = jwt.encode({
                'username': username,
                'user_id': user.id,
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            refresh_token_expiry = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat()
            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'refresh_token_expiry': refresh_token_expiry
            })
        else:
            return jsonify({'message': '用户名或者密码有误'}), 409
    else:
        email = data.get('email')
        code = data.get('code')
        user = User.query.filter_by(email=email).first()
        real_code = r.get(f'verify:{email}')
        if code and real_code == code:
            access_token = jwt.encode({
                'username': user.username,
                'user_id': user.id,
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            refresh_token = jwt.encode({
                'username': user.username,
                'user_id': user.id,
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            refresh_token_expiry = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat()
            return jsonify({
                'username': user.username,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'refresh_token_expiry': refresh_token_expiry
            })
        else:
            return jsonify({'message': 'Invalid or expired verification code'}), 409

# 刷新token
@app.route('/api/refresh', methods=['POST'])
def refresh_token():
    data = request.json
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify({'message': 'Missing refresh token'}), 401

    try:
        decoded = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=["HS256"])
        new_access_token = jwt.encode({
            'username': decoded['username'],
            'user_id': decoded['user_id'],  
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({'access_token': new_access_token})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Refresh token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid refresh token'}), 401


# 获取当前用户信息
@app.route('/api/userinfo', methods=['GET'])
@token_required
def userinfo(user_id):
    user = User.query.filter_by(id=user_id).first()
    return jsonify({'username': user.username,'email': user.email})


# 更新当前用户信息
@app.route('/api/updateUserInfo', methods=['POSt'])
@token_required
def updateuserinfo(user_id):
    data = request.json
    updateuser = User.query.filter_by(id=user_id).first()
    if data.get('category') == 'username': 
        update_username = data.get('username')
        user = User.query.filter_by(username=update_username).first()
        if user:
            return jsonify({'message': 'username already exists'}), 409
        else:
            updateuser.username = update_username
            db.session.commit()
            return jsonify({'message': 'username already update'})
    elif data.get('category') == 'passward': 
        update_passward = data.get('passward')
        hashed_updatepassword = generate_password_hash(update_passward)
        updateuser.passward = hashed_updatepassword
        db.session.commit()
        return jsonify({'message': 'passward already update'})
    elif data.get('category') == 'email':
        update_email = data.get('email')
        code = data.code
        user = User.query.filter_by(email=update_email).first()
        if user:
            return jsonify({'message': 'email already exists'}), 409
        real_code = r.get(f'verify:{update_email}')
        if code and real_code == code:
            updateuser.email = update_email
            db.session.commit()
            return jsonify({'message': 'email already update'})
        else:
            return jsonify({'message': 'Invalid or expired verification code'}), 409

# 判断文件名是否存在
@app.route("/api/checkfilename", methods=["POST"])
def check_filename():
    data = request.json
    filename = data.get("filename")
    exists = File.query.filter_by(filename=filename).first()
    return jsonify({"exists": bool(exists)})

# 解析文件
@app.route("/api/upload", methods=["POST"])
def upload():
    # if request.method == "OPTIONS":
    #     response = make_response()
    #     response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
    #     response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    #     response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
    #     response.headers.add("Access-Control-Allow-Credentials", "true")
    #     return response, 200
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    filename = file.filename
    if filename == '':
        return jsonify({"error": "No selected file"}), 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    fields_dict = parse_file(filename)
    fields = []
    for key in fields_dict.keys():
        fields.append(key)
    if fields:
        return jsonify({"fields": fields})
    else:        
        return jsonify({"error": "Invalid file format or file is empty"}), 400 

# 字段名模糊匹配
@app.route("/api/attrmatch", methods=["POST"])
@token_required
def attr_match(user_id):
    data = request.json
    field_names = data.get("fieldNames", [])

    all_attrs = Attr.query.all()
    attr_list = [{"attrName": a.attrName, "engName": a.engName, "datatype": a.datatype} for a in all_attrs]
    attr_names = [a["attrName"] for a in attr_list]

    results = {}

    for field in field_names:
        matches = difflib.get_close_matches(field, attr_names, n=5, cutoff=0.5)
        results[field] = matches

    return jsonify(results)

# 检查属性英文名是否存在
@app.route("/api/checkEngnameExist", methods=["POST"])
def checkEngnameifExist():
    data = request.json
    attr = Attr.query.filter_by(engName=data.get("engName")).first()
    if attr:
        return jsonify({"error": "该英文名已经存在"}), 409
    else:
        return jsonify({"message": "ok"})

# 导入数据
@app.route("/api/import", methods=["POST"])
@token_required
def import_data(user_id):
    data = request.json
    filename = data["filename"]
    dataType = data["dataType"]
    dataAttr = data["dataAttr"]
    fields = data["fields"]
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    fields_dict = parse_file(filename)
    base_name, ext = os.path.splitext(filename)
    existing_file = File.query.filter_by(filename=filename).first()
    if existing_file:
        filename = f"{base_name}_{(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime('%Y%m%d%H%M%S')}{ext}"
    rename_dict = {}

    # 字段名映射
    for f in fields:
        if f.get("newAttr"):
            rename_dict[f["colname"]] = f["engName"]
            attrunit = fields_dict[f["colname"]]
            if pd.isna(fields_dict[f["colname"]]):
                attrunit = ''
            db.session.add(Attr(
                attrName=f["colname"],
                engName=f["engName"],
                datatype=f["datatype"],
                unit=attrunit
            ))
            db.session.commit()
        else:
            attr = Attr.query.filter_by(attrName=f["attrname"]).first()
            rename_dict[f["colname"]] = attr.engName
        
    records = parse_import(filename, rename_dict)

    # 插入 File 表
    file_stat = os.stat(filepath)
    file_record = File(
        filename=filename,
        user_id=user_id,
        filesize=file_stat.st_size,
        fileformat=ext[1:],
        collection=collection_map.get((dataType, dataAttr)),
        datatype=dataType,
        dataattr=dataAttr
    )
    db.session.add(file_record)
    db.session.commit()

    for r in records:
        r["file_id"] = file_record.id

    collection = file_record.collection
    mongo_db[collection].insert_many(records)

    os.remove(filepath)
    return jsonify({"status": "success"})

# 取消导入接口
@app.route("/api/cancel", methods=["POST"])
def cancel_import():
    data = request.json
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"status": "cancelled and file deleted"})
    else:
        return jsonify({"error": "File not found"}), 404

# 获取文件列表
@app.route("/api/getfileinfo", methods=["GET"])
def get_files():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 手动分页
    query = File.query \
        .join(User, File.user_id == User.id) \
        .with_entities(File, User.username) \
        .order_by(File.upload_time.desc())
    
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    file_list = []
    for f, username in items:  # 直接解包元组
        file_list.append({
            "fileid": f.id,
            "filename": f.filename,
            "username": username,
            "filesize": round(f.filesize / 1024, 2),
            "upload_time": f.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
            "datatype": "观测数据" if f.datatype == 'observation' else "模拟数据"
        })

    return jsonify({
        "files": file_list,
        "total": total,
        "pages": (total + per_page - 1) // per_page,  # 计算总页数
        "current_page": page,
        "per_page": per_page
    })

@app.route("/api/deletefile", methods=["POST"])
def delete_file():
    try:
        fileid = request.json.get('fileid')
        file = File.query.filter_by(id=fileid).first()
        if file:
            db.session.delete(file)
            db.session.commit()
        filetype = file.datatype
        fileattr = file.dataattr
        collections = collection_map.get((filetype, fileattr))
        result = mongo_db[collections].delete_many({"file_id": fileid})
        return jsonify({'message': f"删除了 {result.deleted_count} 条记录"})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# 查询数据
@app.route('/api/querydata', methods=['POST'])
def query_data():
    try:
        data = request.get_json()
        data_type = data.get('dataType')
        data_cat = data.get('dataCategory')
        date_range=data.get('dateRange')
        # print(data['dateRange'])
        # 确定查询的集合
        collections = []
        if data_type and data_cat:
            collections = [collection_map.get((data_type, data_cat))]
        elif data_type or data_cat:
            for (dt, da), name in collection_map.items():
                if (data_type and dt == data_type) or (data_cat and da == data_cat):
                    collections.append(name)
        else:
            collections = list(collection_map.values())
        
        if not collections:
            return jsonify([])
        
        # 构建查询条件
        query_conditions = []
        
        # 日期范围
        if date_range and len(date_range) == 2:
            try:
                if date_range[0] and date_range[1]:  # 非空判断
                    start_date = datetime.datetime.strptime(date_range[0], '%Y-%m-%d')
                    end_date = datetime.datetime.strptime(date_range[1], '%Y-%m-%d')
                    query_conditions.append({'date': {'$gte': start_date, '$lte': end_date}})
            except Exception as e:
                print("日期解析失败：", e)

        # 经度范围
        if data.get('longitude') and (data['longitude'].get('min') is not None or data['longitude'].get('max') is not None):
            longitude_condition = {}
            if data['longitude'].get('min') is not None:
                longitude_condition['$gte'] = float(data['longitude']['min'])
            if data['longitude'].get('max') is not None:
                longitude_condition['$lte'] = float(data['longitude']['max'])
            query_conditions.append({'longitude': longitude_condition})
        print(1)
        
        # 纬度范围
        if data.get('latitude') and (data['latitude'].get('min') is not None or data['latitude'].get('max') is not None):
            latitude_condition = {}
            if data['latitude'].get('min') is not None:
                latitude_condition['$gte'] = float(data['latitude']['min'])
            if data['latitude'].get('max') is not None:
                latitude_condition['$lte'] = float(data['latitude']['max'])
            query_conditions.append({'latitude': latitude_condition})
        print(1)
        
        # 站位
        if data.get('location'):
            query_conditions.append({'location': {'$regex': data['location'], '$options': 'i'}})
        print(1)
        
        # 水深范围
        if data.get('waterDeep') and (data['waterDeep'].get('min') is not None or data['waterDeep'].get('max') is not None):
            water_deep_condition = {}
            if data['waterDeep'].get('min') is not None:
                water_deep_condition['$gte'] = float(data['waterDeep']['min'])
            if data['waterDeep'].get('max') is not None:
                water_deep_condition['$lte'] = float(data['waterDeep']['max'])
            query_conditions.append({'waterDeep': water_deep_condition})
        print(1)
        
        # 采样层次
        if data.get('sampleLevel'):
            query_conditions.append({'sampleLevel': data['sampleLevel']})
        print(1)
        
        # 水样/网样
        if data.get('waterSampleOrNetSample'):
            query_conditions.append({'waterSampleornetSample': data['waterSampleOrNetSample']})
        
        # 采样深度范围
        if data.get('sampleDeep') and (data['sampleDeep'].get('min') is not None or data['sampleDeep'].get('max') is not None):
            sample_deep_condition = {}
            if data['sampleDeep'].get('min') is not None:
                sample_deep_condition['$gte'] = float(data['sampleDeep']['min'])
            if data['sampleDeep'].get('max') is not None:
                sample_deep_condition['$lte'] = float(data['sampleDeep']['max'])
            query_conditions.append({'sampleDeep': sample_deep_condition})
        
        # 生物类群
        if data.get('group'):
            query_conditions.append({'group': data['group']})
        
        # 底质类型
        if data.get('substrateType'):
            query_conditions.append({'substrateType': data['substrateType']})
        
        # 采泥器类型
        if data.get('mudSamplerType'):
            query_conditions.append({'mudSamplerType': data['mudSamplerType']})
        
        # 采样次数范围
        if data.get('samplingTimes') and (data['samplingTimes'].get('min') is not None or data['samplingTimes'].get('max') is not None):
            sampling_times_condition = {}
            if data['samplingTimes'].get('min') is not None:
                sampling_times_condition['$gte'] = int(data['samplingTimes']['min'])
            if data['samplingTimes'].get('max') is not None:
                sampling_times_condition['$lte'] = int(data['samplingTimes']['max'])
            query_conditions.append({'samplingTimes': sampling_times_condition})
        print(query_conditions)
        
        # 组合查询条件
        final_query = {}
        if query_conditions:
            final_query = {'$and': query_conditions}
        print(final_query)
        
        # 查询所有符合条件的集合
        results = []
        for collection in collections:
            cursor = mongo_db[collection].find(final_query, {'_id': 0, 'file_id': 0})
            results.extend(list(cursor))
        
        all_keys = set()
        for doc in results:
            if 'date' in doc and isinstance(doc['date'], datetime.datetime):
                doc['date'] = doc['date'].strftime('%Y-%m-%d')
            all_keys.update(doc.keys())
        
        key_dict = {}
        for key in all_keys:
            attr = Attr.query.filter_by(engName=key).first()
            if attr.unit:
                key_dict[key] = f"{attr.attrName} ({attr.unit})"
            else:
                key_dict[key] = f"{attr.attrName}"

        return jsonify({
            'results': results,
            'colsdict': key_dict 
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 下载文件
@app.route('/api/downloadData', methods=['POST'])
def download_data():
    data = request.json
    export_format = data.get("format", "csv")  # csv 或 excel
    export_data = data.get("data", [])

    df = pd.DataFrame(export_data)
    output = io.BytesIO()
    if export_format == "excel":
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         download_name="data.xlsx", as_attachment=True)
    else:
        output.write(df.to_csv(index=False).encode("utf-8"))
        output.seek(0)
        return send_file(output, mimetype="text/csv",
                         download_name="data.csv", as_attachment=True)
# @app.route("/api/getfileinfo", methods=["GET"])
# def get_files():
#     page = request.args.get('page', 1, type=int)  # 当前页，默认是第 1 页
#     per_page = request.args.get('per_page', 10, type=int)
#     query = File.query\
#     .join(User, File.user_id == User.id)\
#     .with_entities(File, User.username)\
#     .order_by(File.upload_time.desc())  # 稳定排序

#     files = db.paginate(query, page=page, per_page=per_page, error_out=False)

#     file_list = []
#     for f, username in files.items:
#         file_list.append({
#             "filename": f.filename,
#             "username": username,
#             "filesize": round(f.filesize / 1024, 2),
#             "upload_time": f.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
#             "datatype": "观测数据" if f.datatype == 'observation' else "模拟数据"
#         })
#     return jsonify({
#         "files": file_list,
#         "total": files.total,  # 总记录数
#         "pages": files.pages,  # 总页数
#         "current_page": files.page,  # 当前页数
#         "per_page": files.per_page  # 每页的文件数
#     })

# # 下载对应文件
# @app.route('/api/download/<int:file_id>', methods=['GET'])
# def download_file(file_id):
#     file = File.query.filter_by(id=file_id).first()
#     collection = file.collection
#     if not file:
#         return jsonify({'error': 'File not found'}), 404

#     export_format = request.args.get('format')
#     if export_format not in ['csv', 'excel']:
#         return jsonify({'error': 'Invalid format'}), 400

#     records = list(mongo_db[collection].find({'file_id': file_id}))
#     if not records:
#         return jsonify({'error': 'No records found'}), 404

#     for doc in records:
#         doc.pop('_id', None)
#         doc.pop('file_id', None)

#     # 转换为 DataFrame
#     df = pd.DataFrame(records)
#     # 格式化日期
#     for col in df.select_dtypes(include=['datetime64[ns]', 'datetime']):
#         df[col] = df[col].dt.strftime('%Y-%m-%d')
#     # 字段重命名
#     mappings = Attrengname.query.filter_by(fileid=file.id).all()
#     rename_dict = {m.engName: m.attrName for m in mappings}
#     df.rename(columns=rename_dict, inplace=True)
    
#     # 构造文件名（去扩展名）
#     filename_base = os.path.splitext(file.filename)[0]
#     response = None
#     # === CSV 导出 ===
#     if export_format == 'csv':
#         buffer = io.StringIO()
#         buffer.write('\ufeff')
#         df.to_csv(buffer, index=False)
#         buffer.seek(0)
#         response = send_file(
#             io.BytesIO(buffer.getvalue().encode('utf-8')),
#             mimetype='text/csv',
#             as_attachment=True,
#             download_name=f"{filename_base}.csv"
#         )

#     # === Excel 导出（设置列宽） ===
#     else:
#         # 日期字段转字符串，防止 ####
#         # for col in df.select_dtypes(include=['datetime64[ns]', 'datetime']):
#         #     df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

#         buffer = io.BytesIO()
#         with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
#             df.to_excel(writer, index=False, sheet_name='Sheet1')
#             worksheet = writer.sheets['Sheet1']

#             # 中文/英文兼容的宽度函数
#             def get_display_width(s):
#                 return sum(2 if ord(c) > 127 else 1 for c in str(s))

#             for i, col in enumerate(df.columns):
#                 # 获取该列所有值 + 列名的最大宽度
#                 max_len = max([get_display_width(v) for v in df[col]] + [get_display_width(col)])
#                 col_letter = get_column_letter(i + 1)
#                 worksheet.column_dimensions[col_letter].width = max_len + 2  # 加点间距

#         buffer.seek(0)
#         response = send_file(
#             buffer,
#             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#             as_attachment=True,
#             download_name=f"{filename_base}.xlsx"
#         )
#     file.download_times += 1
#     db.session.commit()
#     response.headers['X-Download-Times'] = str(file.download_times)
#     return response

# @app.route('/api/download/<int:file_id>', methods=['GET'])
# def download_file(file_id):
#     file = File.query.filter_by(id=file_id).first()
#     collection = file.collection
#     if not file:
#         return jsonify({'error': 'File not found'}), 404
#     format = request.args.get('format')
#     if format not in ['csv', 'excel']:
#         return jsonify({'error': 'Invalid format'}), 400
#     records = list(mongo_db[collection].find({'file_id': file_id}))
#     if not records:
#         return jsonify({'error': 'No records found'}), 404
#     for doc in records:
#         doc.pop('_id', None)
#         doc.pop('file_id', None)
#     df = pd.DataFrame(records)
#     mappings = Attrengname.query.filter_by(fileid=file.id).all()
#     rename_dict = {mapping.engName: mapping.attrName for mapping in mappings}
#     df.rename(columns=rename_dict, inplace=True)    
#     # 获取导出格式
#     export_format = request.args.get('format')
#     if export_format not in ['csv', 'excel']:
#         return jsonify({'error': 'Invalid format'}), 400

#     filename_base = os.path.splitext(file.filename)[0]  # 去除原始文件扩展名

#     if export_format == 'csv':
#         buffer = io.StringIO()
#         df.to_csv(buffer, index=False)
#         buffer.seek(0)
#         return send_file(
#             io.BytesIO(buffer.getvalue().encode('utf-8')),
#             mimetype='text/csv',
#             as_attachment=True,
#             download_name=f"{filename_base}.csv"
#         )
#     else:
#         buffer = io.BytesIO()
#         with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
#             df.to_excel(writer, index=False, sheet_name='Sheet1')
#         buffer.seek(0)
#         return send_file(
#             buffer,
#             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#             as_attachment=True,
#             download_name=f"{filename_base}.xlsx"
#         )

# # 批量下载
# @app.route('/api/download/batch', methods=['POST'])
# def download_batch():
#     ids = request.json.get('ids', [])
#     export_format = request.json.get('format', 'csv')

#     memory_zip = io.BytesIO()
#     print(1)

#     with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
#         print(1)
        
#         for file_id in ids:
#             file = File.query.filter_by(id=file_id).first()
#             collection = file.collection
#             if not file:
#                 return jsonify({'error': 'File not found'}), 404

#             if export_format not in ['csv', 'excel']:
#                 return jsonify({'error': 'Invalid format'}), 400

#             records = list(mongo_db[collection].find({'file_id': file_id}))
#             if not records:
#                 return jsonify({'error': 'No records found'}), 404
#             print(1)
#             for doc in records:
#                 doc.pop('_id', None)
#                 doc.pop('file_id', None)

#             # 转换为 DataFrame
#             df = pd.DataFrame(records)
#             # 格式化日期
#             for col in df.select_dtypes(include=['datetime64[ns]', 'datetime']):
#                 df[col] = df[col].dt.strftime('%Y-%m-%d')
#             # 字段重命名
#             mappings = Attrengname.query.filter_by(fileid=file.id).all()
#             rename_dict = {m.engName: m.attrName for m in mappings}
#             df.rename(columns=rename_dict, inplace=True)
#             filename_base = os.path.splitext(file.filename)[0]
#             print(1)

#             if export_format == 'csv':
#                 buffer = io.StringIO()
#                 df.to_csv(buffer, index=False)
#                 zf.writestr(f"{filename_base}.csv", buffer.getvalue())
#             elif export_format == 'excel':
#                 buffer = io.BytesIO()
#                 with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
#                     df.to_excel(writer, index=False)
#                 zf.writestr(f"{filename_base}.xlsx", buffer.getvalue())
#             print(1)

#     memory_zip.seek(0)
#     return send_file(
#         memory_zip,
#         mimetype='application/zip',
#         as_attachment=True,
#         download_name='batch_download.zip'
#     )

if __name__ == '__main__':
    app.run(debug=True)