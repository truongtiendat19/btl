from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456789@localhost/saledb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app=app)
admin = Admin(app=app, name="QUẢN LÝ BÁN SÁCH",template_mode="bootstrap3")