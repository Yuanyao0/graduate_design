SECRET_KEY = 'super-secret'
JWT_SECRET_KEY = 'jwt-super-secret'
JWT_ACCESS_TOKEN_EXPIRES = 300     # 5分钟
JWT_REFRESH_TOKEN_EXPIRES = 86400  # 1天

# MySQL数据库连接
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:y20030814@localhost:3306/marine_data'
SQLALCHEMY_TRACK_MODIFICATIONS = False
# MongoDB数据库连接
MONGO_URI = 'mongodb://localhost:27017'
# 上传文件路径
UPLOAD_FOLDER = './uploads'

# 邮件配置
MAIL_SERVER = 'smtp.qq.com' 
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = '1226015813@qq.com'
MAIL_PASSWORD = 'abucplmtcfrhjbdj'
