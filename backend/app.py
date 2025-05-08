from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import File
import jwt
import datetime
import io
import os
import pandas as pd
import zipfile
import random
import string
from models import db, User, File, Attrengname
from upload_handler import parse_file
from import_handler import parse_import
from mongo import mongo_db, collection_map
from openpyxl.utils import get_column_letter
from flask_mail import Mail, Message
from redis_config import r


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
            return jsonify({'message': 'Invalid credentials'}), 409
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
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    fields = parse_file(file)
    print(fields)
    if fields:
        return jsonify({"fields": fields})
    else:        
        return jsonify({"error": "Invalid file format or file is empty"}), 400 

# 导入文件
@app.route("/api/import", methods=["POST"])
@token_required
def import_data(user_id):
    data = request.json
    filename = data["filename"]
    dataType = data["dataType"]
    dataAttr = data["dataAttr"]
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    base_name, ext = os.path.splitext(filename)
    existing_file = File.query.filter_by(filename=filename, user_id=user_id).first()
    if existing_file:
        # 添加时间戳或计数器后缀避免重名
        filename = f"{base_name}_{(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime('%Y%m%d%H%M%S')}{ext}"
        # filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # existing_file = File.query.filter_by(filename=filename, user_id=user_id).first()

    ranges, records, rename_dict = parse_import(data)
    file_stat = os.stat(filepath)
    file_record = File(
        filename=filename,
        user_id=user_id,
        filesize=file_stat.st_size,
        fileformat=ext[1:],
        collection = collection_map.get((dataType, dataAttr)),
        datatype=dataType,
        dataattr=dataAttr,
        lon_min = ranges[0],
        lon_max = ranges[1],
        lat_min = ranges[2],
        lat_max = ranges[3]
    )
    db.session.add(file_record)
    db.session.commit()  # 获得 file_record.id
    for r in records:
        r["file_id"] = file_record.id 
    collection = collection_map.get((dataType, dataAttr))
    mongo_db[collection].insert_many(records)
    for dict in rename_dict:
        Attrengname_record = Attrengname(
            attrName = dict[0],
            engName = dict[1],
            fileid = file_record.id
        )
        db.session.add(Attrengname_record)
    db.session.commit()
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

# 获取当前用户的文件列表
@app.route("/api/getfileinfo", methods=["GET"])
def get_user_files():
    files = File.query.all()
    file_list = []
    for file in files:
        formatted_time = file.upload_time.strftime('%Y-%m-%d %H:%M:%S')
        filesize_kb = round(file.filesize / 1024, 2)
        file_list.append({
            "id": file.id,
            "filename": file.filename,
            "filesize": f"{filesize_kb} kB",
            "fileformat": file.fileformat,
            "upload_time": formatted_time,
            "datatype": file.datatype,
            "dataattr": file.dataattr,
            "download_times": file.download_times
        })
    return jsonify({"files": file_list})

# 下载对应文件
@app.route('/api/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    file = File.query.filter_by(id=file_id).first()
    collection = file.collection
    if not file:
        return jsonify({'error': 'File not found'}), 404

    export_format = request.args.get('format')
    if export_format not in ['csv', 'excel']:
        return jsonify({'error': 'Invalid format'}), 400

    records = list(mongo_db[collection].find({'file_id': file_id}))
    if not records:
        return jsonify({'error': 'No records found'}), 404

    for doc in records:
        doc.pop('_id', None)
        doc.pop('file_id', None)

    # 转换为 DataFrame
    df = pd.DataFrame(records)
    # 格式化日期
    for col in df.select_dtypes(include=['datetime64[ns]', 'datetime']):
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    # 字段重命名
    mappings = Attrengname.query.filter_by(fileid=file.id).all()
    rename_dict = {m.engName: m.attrName for m in mappings}
    df.rename(columns=rename_dict, inplace=True)
    
    # 构造文件名（去扩展名）
    filename_base = os.path.splitext(file.filename)[0]
    response = None
    # === CSV 导出 ===
    if export_format == 'csv':
        buffer = io.StringIO()
        buffer.write('\ufeff')
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        response = send_file(
            io.BytesIO(buffer.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{filename_base}.csv"
        )

    # === Excel 导出（设置列宽） ===
    else:
        # 日期字段转字符串，防止 ####
        # for col in df.select_dtypes(include=['datetime64[ns]', 'datetime']):
        #     df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            worksheet = writer.sheets['Sheet1']

            # 中文/英文兼容的宽度函数
            def get_display_width(s):
                return sum(2 if ord(c) > 127 else 1 for c in str(s))

            for i, col in enumerate(df.columns):
                # 获取该列所有值 + 列名的最大宽度
                max_len = max([get_display_width(v) for v in df[col]] + [get_display_width(col)])
                col_letter = get_column_letter(i + 1)
                worksheet.column_dimensions[col_letter].width = max_len + 2  # 加点间距

        buffer.seek(0)
        response = send_file(
            buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{filename_base}.xlsx"
        )
    file.download_times += 1
    db.session.commit()
    response.headers['X-Download-Times'] = str(file.download_times)
    return response

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

# 批量下载
@app.route('/api/download/batch', methods=['POST'])
def download_batch():
    ids = request.json.get('ids', [])
    export_format = request.json.get('format', 'csv')

    memory_zip = io.BytesIO()
    print(1)

    with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        print(1)
        
        for file_id in ids:
            file = File.query.filter_by(id=file_id).first()
            collection = file.collection
            if not file:
                return jsonify({'error': 'File not found'}), 404

            if export_format not in ['csv', 'excel']:
                return jsonify({'error': 'Invalid format'}), 400

            records = list(mongo_db[collection].find({'file_id': file_id}))
            if not records:
                return jsonify({'error': 'No records found'}), 404
            print(1)
            for doc in records:
                doc.pop('_id', None)
                doc.pop('file_id', None)

            # 转换为 DataFrame
            df = pd.DataFrame(records)
            # 格式化日期
            for col in df.select_dtypes(include=['datetime64[ns]', 'datetime']):
                df[col] = df[col].dt.strftime('%Y-%m-%d')
            # 字段重命名
            mappings = Attrengname.query.filter_by(fileid=file.id).all()
            rename_dict = {m.engName: m.attrName for m in mappings}
            df.rename(columns=rename_dict, inplace=True)
            filename_base = os.path.splitext(file.filename)[0]
            print(1)

            if export_format == 'csv':
                buffer = io.StringIO()
                df.to_csv(buffer, index=False)
                zf.writestr(f"{filename_base}.csv", buffer.getvalue())
            elif export_format == 'excel':
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                zf.writestr(f"{filename_base}.xlsx", buffer.getvalue())
            print(1)

    memory_zip.seek(0)
    return send_file(
        memory_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name='batch_download.zip'
    )

if __name__ == '__main__':
    app.run(debug=True)