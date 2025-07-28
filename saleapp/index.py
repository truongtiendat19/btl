import hashlib, hmac, os, uuid, math, requests, filetype, pdfkit
from flask import (
    render_template, request, redirect, session, jsonify,
    send_file, make_response, url_for, abort, flash)
from flask_login import login_user, logout_user, login_required, current_user
from saleapp import app, login, db, dao, utils
from saleapp.dao import check_username_exists
from saleapp.models import (
    UserRole, Book, ImportReceipt,
    DigitalPricing, Purchase, BookContent, Order, CartItem
)
from gtts import gTTS
from flask import Blueprint

# MoMo configuration
MOMO_PARTNER_CODE = "MOMODMJ120250721_TEST"
MOMO_ACCESS_KEY = "Csil0yiSO0r7Ete4"
MOMO_SECRET_KEY = "YY3r7SE6ZjBEvf6DuZGfKQQwYFbP7W6t"
MOMO_ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/create"
MOMO_REDIRECT_URL = "http://localhost:5000/momo/callback"
MOMO_IPN_URL = "http://127.0.0.1:5000/momo/ipn"


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
                # Xóa giỏ hàng trong session trước khi đăng nhập
                session.pop('cart', None)
                next = request.args.get('next')
                return redirect('/' if next is None else next)

            u = dao.auth_user(username=username, password=password, role=UserRole.ADMIN)
            if u:
                login_user(u)
                # Xóa giỏ hàng trong session trước khi đăng nhập
                session.pop('cart', None)
                return redirect('/admin')
            err_msg = 'Mật khẩu không đúng.'
        else:
            err_msg = 'Tên đăng nhập không tồn tại.'

    return render_template('login.html', err_msg=err_msg)


admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')


@admin_bp.route("/logout")
def admin_logout_process():
    session.pop('cart', None)
    logout_user()
    return redirect('/login')


# Đăng ký Blueprint
app.register_blueprint(admin_bp)


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
                           pages=math.ceil(total / app.config["PAGE_SIZE"]),
                           page=page)


@app.route("/books/<book_id>")
def details(book_id):
    comments = dao.load_comments(book_id)
    book = Book.query.get(book_id)
    my_purchases = Purchase.query.filter_by(user_id=current_user.id,
                                            book_id=book_id).all() if current_user.is_authenticated else []
    valid_purchases_dict = {}
    expired_purchase_ids = set()
    now = datetime.now()

    for p in my_purchases:
        if p.time_end and p.time_end >= now:
            valid_purchases_dict[p.digital_pricing_id] = p
        else:
            expired_purchase_ids.add(p.digital_pricing_id)

    ORDER = {'free': 1, 'prenium': 2}
    reading_packages = sorted(
        book.digital_pricings,
        key=lambda x: ORDER.get(x.access_type, 99)
    )

    return render_template(
        'details.html',
        book=dao.get_book_by_id(book_id),
        comments=comments,
        reading_packages=reading_packages,
        my_purchases=my_purchases,
        purchases_dict=valid_purchases_dict,
        expired_purchase_ids=expired_purchase_ids,
        now=now
    )


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
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        username = request.form.get('username')

        if dao.check_username_exists(username):
            err_msg = 'Tên đăng nhập đã tồn tại.'
        elif password != confirm:
            err_msg = 'Mật khẩu không khớp!'
        else:
            avatar = request.files.get('avatar')

            if avatar and avatar.filename:
                kind = filetype.guess(avatar.read())
                avatar.stream.seek(0)

                if not kind or kind.mime.split('/')[0] != 'image':
                    err_msg = 'Tệp tải lên không phải là ảnh hợp lệ!'
                    return render_template('register.html', err_msg=err_msg)

            data = request.form.copy()
            del data['confirm']
            dao.add_user(avatar=avatar, **data)
            return redirect('/login')

    return render_template('register.html', err_msg=err_msg)


@app.route("/api/carts", methods=['post'])
@login_required
def add_to_cart():
    data = request.json
    book_id = str(data.get('id'))
    name = data.get('name')
    price = data.get('price')

    # Kiểm tra xem sách đã có trong giỏ hàng của người dùng chưa
    cart_item = CartItem.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            book_id=book_id,
            quantity=1
        )
        db.session.add(cart_item)
    db.session.commit()

    # Tính toán thống kê giỏ hàng từ cơ sở dữ liệu
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    cart = {str(item.book_id): {
        "id": item.book_id,
        "name": item.book.name,
        "price": item.book.price_physical,
        "quantity": item.quantity
    } for item in cart_items}

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


@app.route("/api/pay", methods=['POST', 'GET'])
@login_required
def pay():
    if request.method == 'POST':
        data = request.get_json()
        cart = session.get('cart')
        if not cart:
            return jsonify({"error": "Giỏ hàng trống"}), 400
        customer_phone = data.get('customer_phone')
        customer_address = data.get('customer_address')
        payment_method = data.get('payment_method')
        delivery_method = data.get('delivery_method')

        if not all([customer_phone, customer_address, payment_method, delivery_method]):
            return jsonify({"error": "Vui lòng điền đầy đủ thông tin"}), 400

        if payment_method == 'MoMo':
            order_id = str(uuid.uuid4())
            amount = str(int(utils.cart_stats(cart)['total_amount']))  # Đảm bảo là chuỗi
            request_id = str(uuid.uuid4())
            order_info = f"Payment for order {order_id}"
            items = [
                {"id": item["id"], "name": item["name"], "price": item["price"], "quantity": item["quantity"]}
                for item in cart.values()
            ]

            raw_signature = (f"accessKey={MOMO_ACCESS_KEY}&amount={amount}&extraData=&ipnUrl={MOMO_IPN_URL}"
                             f"&orderId={order_id}&orderInfo={order_info}&partnerCode={MOMO_PARTNER_CODE}"
                             f"&redirectUrl={MOMO_REDIRECT_URL}&requestId={request_id}&requestType=captureWallet")
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

            print("====== MOMO CREATE REQUEST ======")
            print("Payload:", payload)
            print("Raw Signature:", raw_signature)
            print("Calculated Signature:", signature)

            try:
                response = requests.post(MOMO_ENDPOINT, json=payload, headers={"Content-Type": "application/json"},
                                         timeout=10)
                response.raise_for_status()
                response_data = response.json()
                print("MoMo Response:", response_data)
                if response_data.get("resultCode") == 0:
                    dao.add_receipt(cart, customer_phone, customer_address, True, delivery_method, order_id=order_id)
                    return jsonify({"payUrl": response_data.get("payUrl")})
                else:
                    return jsonify({"error": response_data.get("message", "Thanh toán MoMo thất bại")}), 400
            except requests.exceptions.RequestException as e:
                print("MoMo Error:", str(e))
                return jsonify({"error": f"Lỗi kết nối MoMo: {str(e)}"}), 500

        # Xử lý COD
        order = dao.add_receipt(cart, customer_phone, customer_address, False, delivery_method)
        session.pop('cart', None)
        return jsonify({"message": "Thanh toán COD thành công", "redirect_url": url_for('index')})
    return render_template('order_books.html', user=current_user)


@app.route("/momo/callback", methods=['GET'])
def momo_callback():
    result_code = request.args.get('resultCode')
    order_id = request.args.get('orderId')

    if result_code == '0':  # Thanh toán thành công

        order = Order.query.filter_by(order_id=order_id).first()
        if order:
            order.payment_status = 'Paid'
            order.status = 'Confirmed'
            db.session.commit()
            session.pop('cart', None)
            flash("Thanh toán đơn hàng thành công!", "success")
            return redirect(url_for('index'))

        purchase = Purchase.query.filter_by(momo_order_id=order_id).first()
        if purchase:
            pricing = DigitalPricing.query.get(purchase.digital_pricing_id)
            purchase.time_end = purchase.time_start + timedelta(days=pricing.duration_day)
            purchase.status = 'COMPLETED'
            db.session.commit()
            flash("Thanh toán gói đọc thành công!", "success")
            return redirect(url_for('read_book', book_id=purchase.book_id))

        flash("Không tìm thấy đơn hàng!", "danger")
    else:
        flash("Thanh toán thất bại: " + request.args.get('message', 'Lỗi không xác định'), "danger")

    return redirect(url_for('index'))


@app.route("/momo/ipn", methods=['POST'])
def momo_ipn():
    data = request.get_json()

    received_signature = data.get('signature')
    raw_signature = (f"accessKey={MOMO_ACCESS_KEY}&amount={data.get('amount')}&extraData={data.get('extraData')}"
                     f"&ipnUrl={MOMO_IPN_URL}&orderId={data.get('orderId')}&orderInfo={data.get('orderInfo')}"
                     f"&partnerCode={data.get('partnerCode')}&redirectUrl={MOMO_REDIRECT_URL}"
                     f"&requestId={data.get('requestId')}&requestType={data.get('requestType')}")
    expected_signature = hmac.new(
        MOMO_SECRET_KEY.encode('utf-8'),
        raw_signature.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if received_signature != expected_signature:
        return jsonify({"message": "Chữ ký không hợp lệ"}), 400

    if data.get('resultCode') == 0:
        order_id = data.get('orderId')
        order = Order.query.filter_by(order_id=order_id).first()
        if order:
            order.payment_status = 'Paid'
            order.status = 'Confirmed'
            db.session.commit()

        purchase = Purchase.query.filter_by(momo_order_id=order_id).first()
        if purchase:
            pricing = DigitalPricing.query.get(purchase.digital_pricing_id)
            purchase.time_end = purchase.time_start + timedelta(days=pricing.duration_day)
            purchase.status = 'COMPLETED'
            db.session.commit()
    return jsonify({"message": "IPN received"}), 200


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
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        cart = {str(item.book_id): {
            "id": item.book_id,
            "name": item.book.name,
            "price": item.book.price_physical,
            "quantity": item.quantity
        } for item in cart_items}
        session['cart'] = cart  # Đồng bộ với session nếu cần
    else:
        cart = session.get('cart', {})

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


@app.route('/admin/receipt/<int:receipt_id>/print')
def print_import_receipt(receipt_id):
    receipt = ImportReceipt.query.get_or_404(receipt_id)
    html = render_template('admin/print_receipt.html', receipt=receipt, now=datetime.now())

    config = pdfkit.configuration(wkhtmltopdf=r'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')

    pdf_data = pdfkit.from_string(
        html,
        False,
        configuration=config,
        options={"enable-local-file-access": ""}
    )

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=phieu_nhap_{receipt_id}.pdf'

    def cleanup():
        try:
            os.remove(pdf_data)
        except Exception as e:
            print("Lỗi xoá file tạm:", e)

    return response


from datetime import datetime, timedelta


@app.route('/api/buy_reading_package', methods=['POST'])
@login_required
def buy_reading_package():
    data = request.json
    package_id = data.get('package_id')
    book_id = data.get('book_id')

    now = datetime.now()
    pkg = DigitalPricing.query.get(package_id)

    if not pkg:
        return jsonify({'success': False, 'message': 'Không tìm thấy gói đọc!'})

    if pkg.access_type != 'free':
        return jsonify({'success': False, 'message': 'Sai loại gói!'})

    existing = Purchase.query.filter_by(
        user_id=current_user.id,
        digital_pricing_id=package_id,
        book_id=book_id
    ).filter(Purchase.time_end >= now).first()

    if existing:
        return jsonify({'success': True})

    # Tạo mới gói free
    purchase = Purchase(
        user_id=current_user.id,
        book_id=book_id,
        digital_pricing_id=package_id,
        time_start=now,
        time_end=now + timedelta(days=pkg.duration_day),
        status='COMPLETED'
    )
    db.session.add(purchase)
    db.session.commit()

    return jsonify({'success': True})


@app.route("/read/<int:book_id>/")
@login_required
def read_book(book_id):
    now = datetime.now()
    purchase = Purchase.query.filter(
        Purchase.book_id == book_id,
        Purchase.user_id == current_user.id,
        Purchase.time_start <= now,
        Purchase.time_end >= now,
    ).first()

    if not purchase:
        return render_template("access_denied.html")

    page = int(request.args.get('page', 1))
    content = BookContent.query.filter_by(book_id=book_id, page_number=page).first()

    if not content:
        abort(404)

    total_pages = BookContent.query.filter_by(book_id=book_id).count()

    return render_template("read_book.html",
                           content=content,
                           page=page,
                           total_pages=total_pages,
                           book_id=book_id)


@app.route("/read_audio_temp/<int:book_id>/<int:page>")
@login_required
def read_audio(book_id, page):
    now = datetime.now()
    purchase = Purchase.query.filter(
        Purchase.book_id == book_id,
        Purchase.user_id == current_user.id,
        Purchase.time_start <= now,
        Purchase.time_end >= now
    ).first()
    if not purchase:
        return render_template("access_denied.html")

    content = BookContent.query.filter_by(book_id=book_id, page_number=page).first()
    if not content:
        abort(404)

    from tempfile import NamedTemporaryFile
    import os

    with NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tts = gTTS(content.content, lang="vi")
        tts.save(tmp_file.name)
        tmp_file_path = tmp_file.name

    response = send_file(tmp_file_path, mimetype="audio/mpeg", as_attachment=False)

    @response.call_on_close
    def cleanup():
        try:
            os.remove(tmp_file_path)
        except Exception as e:
            print("Lỗi xoá file tạm:", e)

    return response


@app.route("/api/pay_reading_package", methods=['GET'])
@login_required
def pay_reading_package():
    package_id = request.args.get('package_id')
    book_id = request.args.get('book_id')

    if not all([package_id, book_id]):
        return "Thiếu thông tin", 400

    pricing = DigitalPricing.query.get(package_id)
    book = Book.query.get(book_id)

    if not pricing or not book:
        return "Không tìm thấy gói đọc hoặc sách", 404

    if pricing.price == 0:
        return "Gói miễn phí không cần thanh toán", 400

    now = datetime.now()
    existing_purchase = Purchase.query.filter(
        Purchase.user_id == current_user.id,
        Purchase.book_id == book.id,
        Purchase.digital_pricing_id == pricing.id,
        Purchase.time_end >= now
    ).first()

    if existing_purchase:
        return redirect(url_for('read_book', book_id=book.id))

    order_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    amount = str(int(pricing.price))
    order_info = f"Mua gói đọc {pricing.access_type} cho sách {book.name}"

    raw_signature = (f"accessKey={MOMO_ACCESS_KEY}&amount={amount}&extraData=&ipnUrl={MOMO_IPN_URL}"
                     f"&orderId={order_id}&orderInfo={order_info}&partnerCode={MOMO_PARTNER_CODE}"
                     f"&redirectUrl={MOMO_REDIRECT_URL}&requestId={request_id}&requestType=captureWallet")

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
        "items": [{
            "id": book.id,
            "name": book.name,
            "price": pricing.price,
            "quantity": 1
        }]
    }

    try:
        response = requests.post(MOMO_ENDPOINT, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        response.raise_for_status()
        response_data = response.json()
        if response_data.get("resultCode") == 0:
            # Lưu tạm thông tin đơn hàng gói đọc
            purchase = Purchase(
                user_id=current_user.id,
                book_id=book.id,
                digital_pricing_id=pricing.id,
                time_start=datetime.now(),
                time_end=datetime.now(),
                create_date=datetime.now(),
                momo_order_id=order_id
            )
            db.session.add(purchase)
            db.session.commit()

            return redirect(response_data.get("payUrl"))
        else:
            return f"Lỗi MoMo: {response_data.get('message', 'Không xác định')}", 400

    except requests.exceptions.RequestException as e:
        return f"Lỗi kết nối MoMo: {str(e)}", 500


if __name__ == '__main__':
    from saleapp import admin

    with app.app_context():
        app.run(debug=True)