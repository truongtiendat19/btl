from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin

app = Flask(__name__)
app.secret_key ="\xd7\xf5`\x1a\xcd*\x1e\x19\xd3b\xc0Z\xa5'Aa"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456789@localhost/saledb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"]=8

db = SQLAlchemy(app=app)
admin = Admin(app=app, name="QUẢN LÝ BÁN SÁCH",template_mode="bootstrap3")

