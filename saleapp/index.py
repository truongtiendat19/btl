import math
from flask import render_template, request, redirect, session, jsonify, url_for, flash
import dao, utils
from saleapp import app, login, db
from flask_login import login_user, logout_user, login_required, current_user
from saleapp.models import UserRole, Category,Author, Book, ImportReceipt, ImportReceiptDetails
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError


@app.route('/login', methods=['get', 'post'])
def login_manager():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        # Xác thực đăng nhập
        u = dao.auth_user(username=username, password=password, role=UserRole.MANAGER)
        if u:
            login_user(u)
            return render_template('manager_dashboard.html', user=current_user)
        else:
            u = dao.auth_user(username=username, password=password, role=UserRole.STAFF)
            if u:
                login_user(u)
                return render_template('sale.html', user=current_user)
            else:
                u = dao.auth_user(username=username, password=password)
                if u:
                    login_user(u)
                    next = request.args.get('next')
                    return redirect('/' if next is None else next)
            # Thêm thông báo lỗi nếu không xác thực được
        flash("Sai tên đăng nhập hoặc mật khẩu. Vui lòng thử lại.", "danger")

    return render_template('login.html')



@app.route('/import_books', methods=['GET', 'POST'])
def import_books():
    if request.method == 'POST':
        date_import = request.form.get('date_import')
        if not date_import:
            date_import = datetime.now().strftime('%Y-%m-%d')

        books = request.form.getlist('book')
        categories = request.form.getlist('category')
        authors = request.form.getlist('author')
        quantities = request.form.getlist('quantity')

        errors = []
        success = []

        if not (len(books) == len(categories) == len(authors) == len(quantities)):
            flash("Dữ liệu nhập không hợp lệ. Vui lòng kiểm tra lại!", "danger")
            return redirect(url_for('import_books'))

        for book_name, category_name, author_name, quantity_str in zip(books, categories, authors, quantities):
            try:
                quantity = int(quantity_str)

                if quantity < 150:
                    errors.append(f"Số lượng nhập cho sách '{book_name}' phải lớn hơn hoặc bằng 150!")
                    continue

                category = Category.query.filter_by(name=category_name).first()
                if not category:
                    category = Category(name=category_name)
                    db.session.add(category)
                    db.session.commit()

                author = Author.query.filter_by(name=author_name).first()
                if not author:
                    author = Author(name=author_name)
                    db.session.add(author)
                    db.session.commit()

                book = Book.query.filter_by(name=book_name, category_id=category.id).first()
                if book and book.quantity >= 300:
                    errors.append(f"Sách '{book_name}' đã đủ số lượng (>300), không thể nhập thêm!")
                    continue

                if not book:
                    book = Book(name=book_name, category_id=category.id, author_id=author.id, quantity=0)
                    db.session.add(book)

                book.quantity += quantity
                db.session.commit()

                import_receipt = ImportReceipt(date_import=date_import, user_id=current_user.id)
                db.session.add(import_receipt)
                db.session.commit()

                receipt_detail = ImportReceiptDetails(
                    quantity=quantity,
                    book_id=book.id,
                    importreceipt_id=import_receipt.id
                )
                db.session.add(receipt_detail)
                db.session.commit()

                success.append(f"Nhập thành công sách '{book_name}' với số lượng {quantity}!")

            except ValueError:
                errors.append(f"Số lượng '{quantity_str}' không hợp lệ cho sách '{book_name}'!")
            except SQLAlchemyError as e:
                db.session.rollback()
                errors.append(f"Lỗi cơ sở dữ liệu khi nhập sách '{book_name}': {str(e)}")

        if success:
            flash(" ".join(success), "success")
        if errors:
            flash(" ".join(errors), "danger")

        return redirect(url_for('import_books'))

    return render_template('import_books.html', datetime=datetime)



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


# @app.route("/login", methods=['get', 'post'])
# def login_process():
#     if request.method.__eq__('POST'):
#         username = request.form.get('username')
#         password = request.form.get('password')
#
#         u = dao.auth_user(username=username, password=password)
#         if u:
#             login_user(u)
#             next = request.args.get('next')
#             return redirect('/' if next is None else next)
#
#         flash("Tên đăng nhập hoặc mật khẩu không đúng!", "danger")
#
#     return render_template('login.html')


@app.route("/login-admin", methods=['post'])
def login_admin_process():
    username = request.form.get('username')
    password = request.form.get('password')

    u = dao.auth_user(username=username, password=password, role=UserRole.ADMIN)
    if u:
        login_user(u)
    flash("Tên đăng nhập hoặc mật khẩu không đúng!", "danger")

    return redirect('/admin')


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
