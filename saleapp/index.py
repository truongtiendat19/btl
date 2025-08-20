import hmac, uuid, math, requests, filetype
from flask import (
    render_template, request, redirect, jsonify,
    send_file, url_for, abort, flash)
from flask_login import login_user, logout_user, login_required
from saleapp import login, dao, utils, scheduler
from saleapp.dao import *
from saleapp.models import *
from gtts import gTTS
from flask import Blueprint
from datetime import datetime, timedelta
import os
from sqlalchemy.orm import joinedload

# from chatbot import chatbot_bp
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
            u = dao.auth_user(username=username, password=password)
            if u:
                if u.is_active == True:
                    login_user(u)
                    session.pop('cart', None)

                    if u.user_role == UserRole.CUSTOMER:
                        next_url = request.args.get('next')
                        return redirect(next_url if next_url else '/')
                    elif u.user_role in [UserRole.ADMIN, UserRole.STAFF]:
                        return redirect('/admin')
                else:
                    err_msg = 'Tài khoản không có quyền truy cập.'
            else:
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


@app.route("/api/chatbot/books")
def get_books():
    books = Book.query.filter_by(is_active=True).all()
    return jsonify([
        {
            "id": b.id,
            "name": b.name,
            "price": b.price_physical,
            "category": b.category.name if b.category else None,
            "author": b.author.name if b.author else None,
            "description": b.description,
            "image": b.image
        }
        for b in books
    ])


@app.route("/order_history")
@login_required
def order_history():
    try:
        query = Order.query.filter_by(user_id=current_user.id, payment_status='PAID')

        # Lọc theo ngày
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
                query = query.filter(Order.order_date >= from_date_obj)
            except ValueError:
                pass

        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Order.order_date < to_date_obj)
            except ValueError:
                pass

        orders = query.order_by(Order.order_date.desc()).all()

        return render_template('order_history.html', orders=orders)
    except Exception as e:
        print(f"Error in order_history: {str(e)}")
        abort(500, description="Lỗi khi tải lịch sử đơn hàng.")


@app.route("/order_details/<int:order_id>")
@login_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return render_template("access_denied.html"), 403
    return render_template('Reveiw.html', order=order)


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
    book = Book.query.get(book_id)

    # Kiểm tra user đã mua chưa
    my_purchases = Purchase.query.filter_by(user_id=current_user.id,
                                            book_id=book_id).all() if current_user.is_authenticated else []
    purchases_dict = {}
    now = datetime.now()
    for p in my_purchases:
        if p.time_end >= now:
            purchases_dict[p.digital_pricing_id] = p

    # Lấy sách liên quan
    related_books = Book.query.filter(
        Book.category_id == book.category_id,
        Book.id != book_id
    ).limit(4).all()

    #  Lấy các bình luận từ đơn hàng vật lý (qua OrderDetail)
    reviews = db.session.query(Review).join(OrderDetail).filter(OrderDetail.book_id == book_id).options(
        joinedload(Review.orderdetail).joinedload(OrderDetail.order),
        joinedload(Review.orderdetail).joinedload(OrderDetail.book)
    ).order_by(Review.created_date.desc()).all()

    # Tính sao trung bình
    avg_rating = db.session.query(func.avg(Review.rating)) \
        .join(OrderDetail).filter(OrderDetail.book_id == book_id).scalar() or 0

    # Tổng số lượt đánh giá
    total_reviews = db.session.query(Review).join(OrderDetail).filter(OrderDetail.book_id == book_id).count()

    return render_template('details.html',
                           book=book,
                           reading_packages=book.digital_pricings,
                           purchases_dict=purchases_dict,
                           now=now,
                           related_books=related_books,
                           reviews=reviews,
                           avg_rating=avg_rating,
                           total_reviews=total_reviews)


@app.context_processor
def common_response_data():
    return {
        'categories': dao.load_categories(),
        'cart_stats': utils.cart_stats(session.get('cart'))
    }


@app.route("/api/books/<book_id>/comments", methods=['POST'])
@login_required
def add_comment(book_id):
    content = request.form.get('content')
    rating = request.form.get('stars', 5, type=int)
    image = request.files.get('image')

    if not content or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Nội dung bình luận không hợp lệ hoặc số sao không đúng"}), 400

    try:
        # Kiểm tra và tải ảnh lên Cloudinary nếu có
        image_url = None
        if image:
            kind = filetype.guess(image)
            if not kind or kind.mime.split('/')[0] != 'image':
                return jsonify({"error": "Tệp tải lên không phải là ảnh hợp lệ!"}), 400
            image.seek(0)  # Reset con trỏ file
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result.get('secure_url')

        c = dao.add_comment(content=content, book_id=book_id, rating=rating, image=image_url)

        # Lấy thông tin user
        user = None
        if c.order_detail_id:
            order_detail = OrderDetail.query.get(c.order_detail_id)
            order = Order.query.get(order_detail.order_id)
            user = User.query.get(order.user_id)
        else:
            # Nếu không có order_detail_id, lấy user từ Purchase
            purchase = Purchase.query.filter_by(book_id=book_id, user_id=current_user.id).first()
            if purchase:
                user = User.query.get(purchase.user_id)

        if not user:
            raise ValueError("Không tìm thấy thông tin người dùng")

        return jsonify({
            "id": c.id,
            "content": c.comment,
            "created_date": c.created_date.isoformat(),
            "user": {
                "avatar": user.avatar,
                "name": user.name
            },
            "rating": c.rating,
            "image": c.image
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": f"Lỗi hệ thống khi thêm bình luận: {str(e)}"}), 500


@app.route("/api/order-details/<int:order_detail_id>/comments", methods=["POST"])
@login_required
def comment_on_order_detail(order_detail_id):
    # Kiểm tra đã có bình luận chưa
    existing_review = Review.query.filter_by(order_detail_id=order_detail_id).first()
    if existing_review:
        return jsonify({'error': 'Bạn đã bình luận cho đơn mua này rồi!'}), 400

    # Lấy dữ liệu từ form
    content = request.form.get('content')
    rating = int(request.form.get('stars', 5))
    image = None

    # Xử lý ảnh nếu có
    file = request.files.get('image')
    if file:
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image = f"/static/uploads/{filename}"

    # Tạo và lưu Review
    try:
        review = Review(
            order_detail_id=order_detail_id,
            rating=rating,
            comment=content,
            image=image,
            user_id=current_user.id  # nếu Review model có user_id
        )
        db.session.add(review)
        db.session.commit()

        return jsonify({
            "created_date": review.created_date.strftime("%Y-%m-%d %H:%M"),
            "rating": review.rating,
            "comment": review.comment,
            "image": review.image
        })
    except Exception as ex:
        db.session.rollback()
        app.logger.error(f"Lỗi khi thêm bình luận: {ex}")
        return jsonify({'error': 'Không thể lưu bình luận.'}), 500


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


@app.route("/api/carts/<book_id>", methods=['PUT'])
@login_required
def update_cart(book_id):
    quantity = int(request.json.get('quantity', 0))
    if quantity < 0:
        return jsonify({"error": "Số lượng không hợp lệ!"}), 400

    cart_item = CartItem.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if cart_item:
        if quantity == 0:
            db.session.delete(cart_item)
        else:
            cart_item.quantity = quantity
        db.session.commit()

    # Cập nhật session['cart']
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    cart = {
        str(item.book_id): {
            "id": item.book_id,
            "name": item.book.name,
            "price": item.book.price_physical,
            "quantity": item.quantity
        } for item in cart_items
    }
    session['cart'] = cart

    return jsonify(utils.cart_stats(cart))


@app.route("/api/carts/<book_id>", methods=['DELETE'])
@login_required
def delete_cart(book_id):
    book_id = str(book_id)
    cart_item = CartItem.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()

    # Cập nhật session['cart']
    utils.sync_cart_to_session(current_user.id)

    return jsonify(utils.cart_stats(session.get('cart', {})))


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
            amount = str(int(utils.cart_stats(cart)['total_amount']))
            request_id = str(uuid.uuid4())
            order_info = f"Payment for order {order_id}"
            items = [
                {"id": item["id"], "name": item["name"], "price": item["price"], "quantity": item["quantity"]}
                for item in cart.values()
            ]
            session['pending_order'] = {
                "order_id": order_id,
                "customer_phone": customer_phone,
                "customer_address": customer_address,
                "delivery_method": delivery_method
            }

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

            try:
                response = requests.post(MOMO_ENDPOINT, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
                response.raise_for_status()
                response_data = response.json()
                print("MoMo Response:", response_data)

                if response_data.get("resultCode") == 0:
                    # Tạo đơn hàng
                    dao.add_receipt(cart, customer_phone, customer_address, True, delivery_method, order_id=order_id)

                    # Xóa giỏ hàng trong session
                    session.pop('cart', None)

                    # (Tùy chọn) Xóa giỏ hàng trong DB nếu bạn lưu bằng CartItem
                    from saleapp.models import CartItem
                    CartItem.query.filter_by(user_id=current_user.id).delete()
                    db.session.commit()
                    print("thanh toan")
                    return jsonify({"payUrl": response_data.get("payUrl")})
                else:
                    return jsonify({"error": response_data.get("message", "Thanh toán MoMo thất bại")}), 400

            except requests.exceptions.RequestException as e:
                print("MoMo Error:", str(e))
                return jsonify({"error": f"Lỗi kết nối MoMo: {str(e)}"}), 500

    return render_template('order_books.html', user=current_user)


@app.route("/momo/callback", methods=['GET'])
def momo_callback():
    result_code = request.args.get('resultCode')
    order_id = request.args.get('orderId')

    if result_code == '0':

        purchase = Purchase.query.filter_by(momo_order_id=order_id).first()
        if purchase:
            pricing = DigitalPricing.query.get(purchase.digital_pricing_id)
            if pricing:
                purchase.time_end = purchase.time_start + timedelta(days=pricing.duration_day)
            purchase.status = 'COMPLETED'
            db.session.commit()
            flash("Thanh toán gói đọc thành công!", "success")
            return redirect(url_for('read_book', book_id=purchase.book_id))

        # Cập nhật trạng thái
        order = Order.query.filter_by(order_id=order_id).first()
        if order:
            order.payment_status = 'PAID'
            db.session.commit()
            session.pop('cart', None)
        return redirect(url_for('index'))


    else:
        flash("Thanh toán thất bại: " + request.args.get('message', 'Lỗi không xác định'), "danger")


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
            order.payment_status = 'PAID'
            order.status = 'PENDING'
            db.session.commit()

        purchase = Purchase.query.filter_by(momo_order_id=order_id).first()
        if purchase:
            pricing = DigitalPricing.query.get(purchase.digital_pricing_id)
            purchase.time_end = purchase.time_start + timedelta(days=pricing.duration_day)
            purchase.status = 'COMPLETED'
            db.session.commit()
    return jsonify({"message": "IPN received"}), 200


@app.route('/cart')
def cart_view():
    if current_user.is_authenticated:
        # Lấy giỏ hàng từ DB
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        cart = {
            str(item.book_id): {
                "id": item.book_id,
                "name": item.book.name,
                "price": item.book.price_physical,
                "quantity": item.quantity
            } for item in cart_items
        }
        session['cart'] = cart
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
        return render_template("access_denied.html"), 403

    total_pages = BookContent.query.filter_by(book_id=book_id).count()
    if total_pages == 0:
        abort(404)

    page = request.args.get('page', default=1, type=int)
    action = request.args.get('action')

    last_page = purchase.page_number or 1
    if last_page < 1:
        last_page = 1
    if last_page > total_pages:
        last_page = total_pages

    if action == 'resume':
        page = last_page
    elif action == 'restart':
        page = 1

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    show_continue_modal = (action is None and page == 1 and last_page > 1)

    if not show_continue_modal and page != last_page:
        purchase.page_number = page
        db.session.commit()

    content = BookContent.query.filter_by(book_id=book_id, page_number=page).first()
    if not content:
        abort(404)

    return render_template(
        "read_book.html",
        content=content,
        page=page,
        total_pages=total_pages,
        book_id=book_id,
        last_page_read=last_page,
        show_continue_modal=show_continue_modal
    )


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
            # Lưu tạm
            purchase = Purchase(
                user_id=current_user.id,
                book_id=book.id,
                digital_pricing_id=pricing.id,
                unit_price=pricing.price,
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


@scheduler.task('interval', id='clear_expired', minutes=1)
def job_clear_expired():
    with app.app_context():
        clean_expired_pending_purchases()

if __name__ == '__main__':
    from saleapp import admin

    with app.app_context():
        app.run(debug=True)
