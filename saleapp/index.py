import math
from functools import wraps
from flask import render_template, request, redirect, session, jsonify, url_for
import dao, utils
from saleapp import app, login
from flask_login import login_user, logout_user, login_required, current_user
from saleapp.models import UserRole,Book



# TRANG HOÁ ĐƠN

@app.route('/api/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    data = [{"id": book.id, "name": book.name, "category": book.category.name, "price": book.price} for book in books]
    return jsonify(data)


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
