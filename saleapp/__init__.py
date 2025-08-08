import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary
from flask_apscheduler import APScheduler

scheduler = APScheduler()

# tạo ứng dụng
app = Flask(__name__)


scheduler.init_app(app)
scheduler.start()

# Đặt secret_key để bảo mật session
app.secret_key = 'your_secret_key'

# thiết lập khóa bí mật
app.secret_key = 'ab8f61d1c7b9d0e2c6f4c8ab7314f8cfe0baf1f9732fcf80'

# cấu hình sơ sở dữ liệu
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456789@localhost/db?charset=utf8mb4"
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


UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Tạo thư mục nếu chưa tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
