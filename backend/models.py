from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    upload_time = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8))
    filesize = db.Column(db.Integer)
    fileformat = db.Column(db.String(10))
    collection = db.Column(db.String(64))
    datatype = db.Column(db.String(64))
    dataattr = db.Column(db.String(64))

# class Location(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     loca_code = db.Column(db.String(64))
#     lon = db.Column(db.Float)
#     lat = db.Column(db.Float)

class Attr(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attrName = db.Column(db.String(80), unique=True, nullable=False)
    engName = db.Column(db.String(128), unique=True, nullable=False)
    datatype = db.Column(db.String(20), nullable=False)
    unit = db.Column(db.String(20))

class Attrclass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attrclassName = db.Column(db.String(80), unique=True, nullable=False)
    eng_label = db.Column(db.String(128), nullable=False)

# class Attrengname(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     attrName = db.Column(db.String(80), nullable=False)
#     engName = db.Column(db.String(80), nullable=False)
#     fileid = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)