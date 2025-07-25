import json
import math
import uuid
import hmac
import hashlib
import requests
from flask import render_template, request, redirect, session, jsonify, url_for
import dao, utils
from saleapp import app, login, db
from flask_login import login_user, logout_user, login_required, current_user
from saleapp.dao import check_username_exists
from saleapp.models import UserRole, Book, User, Category, Author, Order
from saleapp.models import DigitalPricing
# MoMo configuration
MOMO_PARTNER_CODE = "YOUR_MOMO_PARTNER_CODE"  # Replace with your MoMo partner code
MOMO_ACCESS_KEY = "YOUR_MOMO_ACCESS_KEY"      # Replace with your MoMo access key
MOMO_SECRET_KEY = "YOUR_MOMO_SECRET_KEY"      # Replace with your MoMo secret key
MOMO_ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/create"
MOMO_REDIRECT_URL = "http://yourdomain.com/momo/callback"  # Replace with your domain
MOMO_IPN_URL = "http://yourdomain.com/momo/ipn"           # Replace with your domain
@app.route('/api/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    book_list = [{
        "id": book.id,
        "name": book.name,
        "category": book.category.name,
        "price": book.price_physical,
        "author": book.author.name
    } for book in books]
    return jsonify(book_list)

@app.route('/login', methods=['GET', 'POST'])
def login_process():
    err_msg = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if check_username_exists(username):
            u = dao.auth_user(username=username, password=password, role=UserRole.CUSTOMER)
            if u:
                login_user(u)
                next = request.args.get('next')
                return redirect('/' if next is None else next)

            u = dao.auth_user(username=username, password=password, role=UserRole.ADMIN)
            if u:
                login_user(u)
                return redirect('/admin')
            err_msg = 'Mật khẩu không đúng.'
        else:
            err_msg = 'Tên đăng nhập không tồn tại.'

    return render_template('login.html', err_msg=err_msg)

@app.route("/")
def index():
    kw = request.args.get('kw')
    cate_id = request.args.get('category_id')
    author_id = request.args.get('author_id')
    price_filter = request.args.get('price_filter')
    page = request.args.get('page', 1, type=int)

    books = dao.load_books(kw=kw, category_id=cate_id, author_id=author_id, price_filter=price_filter, page=page)
    total = dao.count_books(kw=kw, category_id=cate_id, author_id=author_id, price_filter=price_filter)

    return render_template('index.html',
                           books=books,
                           authors=dao.load_authors(),
                           categories=dao.load_categories(),
                           pages=math.ceil(total/app.config["PAGE_SIZE"]),
                           page=page)

@app.route("/books/<book_id>")
def details(book_id):
    book = dao.get_book_by_id(book_id)
    comments = dao.load_comments(book_id)
    digital_pricing = DigitalPricing.query.filter_by(book_id=book_id).order_by(DigitalPricing.price.asc()).first()

    return render_template('details.html',
                           book=book,
                           comments=comments,
                           digital_pricing=digital_pricing)

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

@app.route('/register', methods=['get', 'post'])
def register_process():
    err_msg = ''
    if request.method.__eq__('POST'):
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        username = request.form.get('username')

        if dao.check_username_exists(username):
            err_msg = 'Tên đăng nhập đã tồn tại.'
        else:
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

@app.route('/api/update-cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    book_id = str(data.get('book_id'))
    delta = int(data.get('delta', 0))

    cart = session.get('cart', {})
    if book_id in cart:
        cart[book_id]['quantity'] += delta
        if cart[book_id]['quantity'] <= 0:
            del cart[book_id]
        session['cart'] = cart
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Không tìm thấy sản phẩm trong giỏ hàng'})


@app.route("/api/carts/<book_id>", methods=['delete'])
def delete_cart(book_id):
    cart = session.get('cart')
    if cart and book_id in cart:
        del cart[book_id]
    session['cart'] = cart
    return jsonify(utils.cart_stats(cart))


@app.route("/api/pay", methods=['post', 'get'])
@login_required
def pay():
    if request.method.__eq__('POST'):
        data = request.get_json()
        cart = session.get('cart')
        customer_phone = data.get('customer_phone')
        customer_address = data.get('customer_address')
        payment_method = data.get('payment_method')
        delivery_method = data.get('delivery_method')

        if payment_method == 'MoMo':
            order_id = str(uuid.uuid4())
            amount = int(utils.cart_stats(cart)['total_amount'])
            request_id = str(uuid.uuid4())
            order_info = f"Payment for order {order_id}"
            items = [
                {"id": item["id"], "name": item["name"], "price": item["price"], "quantity": item["quantity"]}
                for item in cart.values()
            ]

            raw_signature = f"accessKey={MOMO_ACCESS_KEY}&amount={amount}&extraData=&ipnUrl={MOMO_IPN_URL}&orderId={order_id}&orderInfo={order_info}&partnerCode={MOMO_PARTNER_CODE}&redirectUrl={MOMO_REDIRECT_URL}&requestId={request_id}&requestType=captureWallet"
            signature = hmac.new(
                MOMO_SECRET_KEY.encode('utf-8'),
                raw_signature.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            payload = {
                "partnerCode": MOMO_PARTNER_CODE,
                "partnerName": "ReadZone",
                "storeId": "ReadZone",
                "requestId": request_id,
                "amount": amount,
                "orderId": order_id,
                "orderInfo": order_info,
                "redirectUrl": MOMO_REDIRECT_URL,
                "ipnUrl": MOMO_IPN_URL,
                "lang": "vi",
                "extraData": "",
                "requestType": "captureWallet",
                "signature": signature,
                "items": items
            }

            print("Payload:", json.dumps(payload, indent=2))  # Gỡ lỗi payload
            try:
                response = requests.post(MOMO_ENDPOINT, json=payload)
                response_data = response.json()
                print("Phản hồi MoMo:", response.text)  # Gỡ lỗi phản hồi
                if response_data.get("resultCode") == 0:
                    dao.add_receipt(cart, customer_phone, customer_address, True, delivery_method, order_id=order_id)
                    return jsonify({"payUrl": response_data.get("payUrl")})
                else:
                    return jsonify({"error": response_data.get("message")}), 400
            except Exception as e:
                print("Lỗi:", str(e))
                return jsonify({"error": str(e)}), 500

        dao.add_receipt(cart, customer_phone, customer_address, payment_method == 'Online', delivery_method)
        return redirect('/')
    return render_template('order_books.html', user=current_user)


# @app.route("/momo/callback", methods=['GET'])
# @login_required
# def momo_callback():
#     result_code = request.args.get('resultCode')
#     order_id = request.args.get('orderId')
#
#     if result_code == '0':
#         # Payment successful, update order status
#         order = Order.query.filter_by(id=order_id).first()
#         if order:
#             order.payment_status = 'Paid'
#             order.status = 'Confirmed'
#             db.session.commit()
#             session.pop('cart', None)  # Clear cart
#             return redirect(url_for('index'))
#     return render_template('index.html', success=result_code == '0')


# @app.route("/momo/ipn", methods=['POST'])
# def momo_ipn():
#     data = request.get_json()
#     if data.get('resultCode') == 0:
#         order_id = data.get('orderId')
#         order = Order.query.filter_by(id=order_id).first()
#         if order:
#             order.payment_status = 'Paid'
#             order.status = 'Confirmed'
#             db.session.commit()
#     return jsonify({"message": "IPN received"}), 200

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