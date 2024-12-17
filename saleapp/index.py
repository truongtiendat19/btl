from saleapp import app
from flask import render_template, request, redirect, session, jsonify
from pyexpat.errors import messages
from saleapp import dao
from saleapp.models import *

# @app.route("/")
# def index():
#     cates = dao.load_categories()  # Gọi hàm lấy danh mục từ dao.py
#     return render_template('index.html', categories=cates)


@app.route('/')
def index():
    cart = None
    return render_template('index.html', cart=cart or [])


@app.route("/login", methods=['get', 'post'])
def login():
    return render_template('login.html')


@app.route("/login1", methods=['get', 'post'])
def login1():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == '123':
            return 'successful'
    return 'failed'

@app.route("/hello/<name>")
def hello(name):
    return render_template('index.html',message="XIN CHÀO %s" %name)

if __name__ == "__main__":
    app.run(debug=True)