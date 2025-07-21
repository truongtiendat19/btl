from xhtml2pdf import pisa
import io, filetype, os, dao, utils, math
from flask import render_template, request, redirect, session, jsonify, send_file, current_app
from saleapp import app, login
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from saleapp.dao import check_username_exists
from saleapp.models import UserRole, Book, ImportReceipt,ImportReceiptDetail, DigitalPricing
from flask import render_template, send_file, current_app
from xhtml2pdf import pisa
import io, os
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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

@app.route("/api/pay", methods=['post', 'get'])
@login_required
def pay():
    if request.method.__eq__('POST'):
        data = request.get_json()
        cart = session.get('cart')
        customer_phone = data.get('customer_phone')
        customer_address = data.get('customer_address')
        payment_method = data.get('payment_method') == 'Online'
        delivery_method = data.get('delivery_method')
        dao.add_receipt(cart, customer_phone, customer_address, payment_method, delivery_method)
        return redirect('/')
    return render_template('order_books.html', user=current_user)

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

@app.route('/admin/receipt/<int:receipt_id>/print')
def print_import_receipt(receipt_id):
    receipt = ImportReceipt.query.get_or_404(receipt_id)
    receipt_details = ImportReceiptDetail.query.filter_by(import_receipt_id=receipt.id).all()

    # Đăng ký font trước khi tạo PDF
    font_path = os.path.join(current_app.root_path, 'static/fonts/DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVu', font_path))

    html = render_template('admin/print_receipt.html',
                           receipt=receipt,
                           details=receipt_details,
                           now=datetime.now())

    result = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=result)
    result.seek(0)

    return send_file(result, download_name=f"phieu_nhap_{receipt.id}.pdf", as_attachment=True)


@app.route("/read/<int:book_id>/")
@login_required
def read_book(book_id):
    # Kiểm tra quyền truy cập
    now = datetime.now()

    purchase = db.session.query(Purchase).filter(
        Purchase.book_id == book_id,
        Purchase.user_id == current_user.id,
        Purchase.time_start <= now,
        Purchase.time_end >= now
    ).first()

    if not purchase:
        return redirect(url_for("access_denied"))

    # Lấy nội dung trang đầu tiên
    page = int(request.args.get('page', 1))
    content = db.session.query(BookContent).filter_by(book_id=book_id, page_number=page).first()

    if not content:
        return redirect(url_for("not_found"))

    total_pages = db.session.query(func.count(BookContent.id)).filter_by(book_id=book_id).scalar()

    return render_template("read_book.html",
                           content=content,
                           page=page,
                           total_pages=total_pages,
                           book_id=book_id)

@app.route('/book/<int:book_id>/buy', methods=['GET', 'POST'])
@login_required
def buy_book_access(book_id):
    book = Book.query.get_or_404(book_id)
    pricings = DigitalPricing.query.filter_by(book_id=book_id).all()

    if request.method == 'POST':
        pricing_id = request.form.get('pricing_id')
        pricing = DigitalPricing.query.get(pricing_id)

        if not pricing or pricing.book_id != book.id:
            flash("Gói đọc không hợp lệ.", "danger")
            return redirect(url_for('buy_book_access', book_id=book_id))

        now = datetime.now()
        time_end = now + timedelta(days=pricing.duration_day)

        # Tạo lịch sử mua quyền đọc
        purchase = Purchase(
            user_id=current_user.id,
            book_id=book.id,
            digital_pricing_id=pricing.id,
            time_start=now,
            time_end=time_end
        )
        db.session.add(purchase)
        db.session.commit()

        flash("✅ Mua quyền đọc thành công!", "success")
        return redirect(url_for('read_book', book_id=book.id))

    return render_template('buy_access.html', book=book, pricings=pricings)


if __name__ == '__main__':
    from saleapp import admin
    with app.app_context():
        app.run(debug=True)