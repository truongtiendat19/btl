from flask import Flask, render_template, request
from pyexpat.errors import messages
import dao
app = Flask(__name__)

@app.route("/")
def index():
    cates = dao.load_categories()  # Gọi hàm lấy danh mục từ dao.py
    return render_template('index.html', categories=cates)

@app.route("/dangnhap")
def dangnhap():
    return "DANG NHAP "


@app.route("/hello/<name>")
def hello(name):
    return render_template('index.html',message="XIN CHÀO %s" %name)


if __name__ == "__main__":
    app.run(debug=True)