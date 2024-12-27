import math
from flask import render_template, request, redirect, session, jsonify, url_for, flash
from apscheduler.schedulers.background import BackgroundScheduler
from functools import wraps
from flask import render_template, request, redirect, session, jsonify, url_for
import dao, utils
from saleapp import app, login, db
from flask_login import login_user, logout_user, login_required, current_user
from saleapp.models import UserRole, Category,Author, Book, ImportReceipt, ImportReceiptDetails, ManageRule,ReceiptDetails,Receipt
from saleapp.models import UserRole, Category,Author, Book, ImportReceipt, ImportReceiptDetails, Bill,BillDetails,Book,Order
from datetime import datetime,timedelta
import random
from threading import Thread
import time
from sqlalchemy.exc import SQLAlchemyError
from saleapp.models import UserRole,Book


@app.route('/api/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    book_list = [{
        "id": book.id,
        "name": book.name,
        "category": book.category.name,
        "price": book.price
    } for book in books]
    return jsonify(book_list)


@app.route('/import_bill', methods=['POST'])
def import_bill():
    try:
        data = request.json
        customer_name = data.get("customerName")
        invoice_date = data.get("invoiceDate")
        staff_name = data.get("staffName")
        details = data.get("details")  # Dạng JSON chứa danh sách sách

        # Tạo một hóa đơn mới
        new_bill = Bill(
            name_customer=customer_name,
            created_date=datetime.strptime(invoice_date, '%Y-%m-%d'),
            user_id=1  # Thay ID nhân viên xử lý hóa đơn tại đây
        )
        db.session.add(new_bill)
        db.session.flush()  # Đảm bảo `new_bill` có ID để dùng ở bước tiếp theo

        # Thêm chi tiết hóa đơn
        for detail in details:
            book = Book.query.get(detail.get("bookId"))
            if not book or book.quantity < int(detail.get("quantity")):
                return jsonify({"message": f"Sách {book.name if book else 'không xác định'} không đủ số lượng"}), 400

            book.quantity -= int(detail.get("quantity"))  # Cập nhật tồn kho
            db.session.add(book)

            bill_detail = BillDetails(
                bill_id=new_bill.id,
                book_id=detail.get("bookId"),
                quantity=int(detail.get("quantity")),
                unit_price=book.price
            )
            db.session.add(bill_detail)

        # Lưu thay đổi
        db.session.commit()

        return jsonify({"message": "Hóa đơn được lưu thành công!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Đã xảy ra lỗi: {str(e)}"}), 500


# TRANG HOÁ ĐƠN
scheduler = BackgroundScheduler()

def check_and_cancel_orders():
    current_time = datetime.utcnow()
    expired_time = current_time - timedelta(hours=48)

    # Lọc các đơn hàng quá hạn
    expired_orders = Order.query.filter(
        Order.order_time < expired_time,
        Order.status == 'pending',
        Order.payment_status == 'unpaid'
    ).all()

    for order in expired_orders:
        order.status = 'cancelled'
        db.session.commit()

# Khởi động APScheduler ngay khi ứng dụng được tạo
scheduler.add_job(check_and_cancel_orders, 'interval', hours=1)
scheduler.start()

@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    if scheduler.running:
        scheduler.shutdown()

@app.route('/ds')
def ds():
    return render_template('DS.html')



@app.route('/login', methods=['GET', 'POST'])
def login_process():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Xác thực đăng nhập
        u = dao.auth_user(username=username, password=password, role=UserRole.CUSTOMER)
        if u:
            login_user(u)
            next = request.args.get('next')
            return redirect('/' if next is None else next)

    return render_template('login.html')


def role_required(role):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):

            if not current_user.is_authenticated:
                return redirect(url_for('login_staff_process'))

            if current_user.user_role.name != role:
                return redirect(url_for('login_staff_process'))

            return func(*args, **kwargs)
        return decorated_view
    return wrapper


@app.route('/staff', methods=['GET', 'POST'])
def login_staff_process():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')


        for role in [UserRole.MANAGER, UserRole.STAFF, UserRole.ADMIN]:
            u = dao.auth_user(username=username, password=password, role=role)
            if u:
                login_user(u)

                if role == UserRole.MANAGER:
                    return redirect('/admin')
                elif role == UserRole.STAFF:
                    return redirect('/sale')
                elif role == UserRole.ADMIN:
                    return redirect('/admin')

    return render_template('login_staff.html')


@app.route('/sale')
@login_required
@role_required('STAFF')
def sale():
    return render_template('/sale.html', user=current_user)


@app.route("/")
def index():
    # fi
    kw = request.args.get('kw')
    cate_id = request.args.get('category_id')
    page = request.args.get('page', 1)

    books = dao.load_books(kw=kw, category_id=cate_id, page=int(page))

    total = dao.count_books()

    return render_template('index.html', books=books,
                           pages=math.ceil(total/app.config["PAGE_SIZE"]))


@app.route("/books/<book_id>")
def details(book_id):
    comments = dao.load_comments(book_id)
    return render_template('details.html', book=dao.get_book_by_id(book_id), comments=comments)


@app.route("/api/books/<book_id>/comments", methods=['post'])
@login_required
def add_comment(book_id):
    c = dao.add_comment(content=request.json.get('content'), book_id=book_id)
    return jsonify({
        "id": c.id,
        "content": c.content,
        "created_date": c.created_date,
        "user": {
            "avatar": c.user.avatar
        }
    })


@app.route("/logout")
def logout_process():
    logout_user()
    return redirect('/login')


@app.route("/logout_staff")
def logout_staff_manager_process():
    logout_user()
    return redirect('/staff')


@app.route('/register', methods=['get', 'post'])
def register_process():
    err_msg = ''
    if request.method.__eq__('POST'):
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password.__eq__(confirm):
            data = request.form.copy()
            del data['confirm']

            avatar = request.files.get('avatar')
            dao.add_user(avatar=avatar, **data)

            return redirect('/login')
        else:
            err_msg = 'Mật khẩu không khớp!'

    return render_template('register.html', err_msg=err_msg)


@app.route("/api/carts", methods=['post'])
def add_to_cart():
    cart = session.get('cart')
    if not cart:
        cart = {}

    id = str(request.json.get('id'))
    name = request.json.get('name')
    price = request.json.get('price')

    if id in cart:
        cart[id]['quantity'] = cart[id]['quantity'] + 1
    else:
        cart[id] = {
            "id": id,
            "name": name,
            "price": price,
            "quantity": 1
        }

    session['cart'] = cart

    return jsonify(utils.cart_stats(cart))


@app.route("/api/carts/<book_id>", methods=['put'])
def update_cart(book_id):
    quantity = request.json.get('quantity', 0)

    cart = session.get('cart')
    if cart and book_id in cart:
        cart[book_id]["quantity"] = int(quantity)

    session['cart'] = cart

    return jsonify(utils.cart_stats(cart))


@app.route("/api/carts/<book_id>", methods=['delete'])
def delete_cart(book_id):
    cart = session.get('cart')
    if cart and book_id in cart:
        del cart[book_id]

    session['cart'] = cart

    return jsonify(utils.cart_stats(cart))


@app.route("/api/pay", methods=['post'])
@login_required
def pay():
    cart = session.get('cart')
    try:
        dao.add_receipt(cart)
    except Exception as ex:
        return jsonify({'status': 500, 'msg': str(ex)})
    else:
        del session['cart']
        return jsonify({'status': 200, 'msg': 'successful'})


@app.route('/cart')
def cart_view():
    return render_template('cart.html')


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.context_processor
def common_response_data():
    return {
        'categories': dao.load_categories(),
        'cart_stats': utils.cart_stats(session.get('cart'))
    }


if __name__ == '__main__':
    from saleapp import admin
    with app.app_context():
        app.run(debug=True)
