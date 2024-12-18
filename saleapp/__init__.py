from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
import cloudinary

# tạo ứng dụng
app = Flask(__name__)

# thiết lập khóa bí mật
app.secret_key = 'ab8f61d1c7b9d0e2c6f4c8ab7314f8cfe0baf1f9732fcf80'

# cấu hình sơ sở dữ liệu
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456789@localhost/saledb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

# thiết lập số lượng mục hiển thị
app.config["PAGE_SIZE"] = 9

# khởi tạo ORM, LoginManager
db = SQLAlchemy(app)
login = LoginManager(app)

# cấu hình cloud
cloudinary.config(
    cloud_name="dapckqqhj",
    api_key="139655295655715",
    api_secret="jduVINOQaVK_Q7CjBa7EKHGiKAk",
    secure=True
)