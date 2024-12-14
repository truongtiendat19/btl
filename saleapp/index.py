from flask import Flask, render_template, request
from pyexpat.errors import messages

app = Flask(__name__)

@app.route("/")
def trangchu():
    return render_template('index.html')

@app.route("/dangnhap")
def dangnhap():
    return "DANG NHAP "


@app.route("/hello/<name>")
def hello(name):
    return render_template('index.html',message="XIN CHÀO %s" %name)


if __name__ == "__main__":
    app.run(debug=True)