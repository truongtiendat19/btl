from datetime import datetime
from flask import session
from saleapp.models import Category, Book, User, Author, Review, OrderDetail, Order
from saleapp import app, db
import hashlib
import cloudinary.uploader
from sqlalchemy import func
from flask_login import current_user
from operator import or_
def load_comments(book_id):
    return Review.query.filter_by(book_id=book_id).order_by(Review.created_date.desc()).all()

def load_categories():
    return Category.query.order_by('id').all()

def load_authors():
    return Author.query.order_by('id').all()

def load_books(kw=None, category_id=None, author_id=None, price_filter=None, page=1):
    books = Book.query

    if kw:
        books = books.filter(Book.name.contains(kw))
    if category_id:
        books = books.filter(Book.category_id == category_id)
    if author_id:
        books = books.filter(Book.author_id == author_id)
    if price_filter == 'paid':
        books = books.filter(Book.price_physical > 0)
    elif price_filter == 'free':
        books = books.filter(Book.price_physical == 0)

    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    books = books.slice(start, start + page_size)
    return books.all()

def count_books(kw=None, category_id=None, author_id=None, price_filter=None):
    query = Book.query

    if kw:
        query = query.filter(Book.name.contains(kw))
    if category_id:
        query = query.filter(Book.category_id == category_id)
    if author_id:
        query = query.filter(Book.author_id == author_id)
    if price_filter == 'paid':
        query = query.filter(Book.price_physical > 0)
    elif price_filter == 'free':
        query = query.filter(Book.price_physical == 0)

    return query.count()

def auth_user(username, password, role):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User.query.filter(User.username.__eq__(username.strip()),
                          User.password.__eq__(password))
    if role:
        u = u.filter(User.user_role.__eq__(role))
    return u.first()

def add_user(name, username, password, avatar=None, user_role=None):
    avatar_url = 'https://res.cloudinary.com/dapckqqhj/image/upload/v1734438576/rlpkm5rn7kqct2k5jcir.jpg'
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    if avatar and avatar.filename:
        res = cloudinary.uploader.upload(avatar)
        avatar_url = res.get('secure_url')
    u = User(name=name, username=username, password=password, avatar=avatar_url, user_role=user_role)
    db.session.add(u)
    db.session.commit()

def check_username_exists(username):
    user = User.query.filter_by(username=username).first()
    return user is not None

def get_user_by_id(id):
    return User.query.get(id)

def get_book_by_id(id):
    return Book.query.get(id)

def stats_books():
    return db.session.query(Category.id, Category.name, func.count(Book.id))\
        .join(Book, Book.category_id.__eq__(Category.id), isouter=True).group_by(Category.id).all()


def add_receipt(cart, customer_phone, customer_address, payment_method, delivery_method, order_id=None):
    if not cart:
        return None

    total_amount = sum(item['quantity'] * item['price'] for item in cart.values())
    order = Order(
        user_id=current_user.id,
        order_date=datetime.now(),
        status='Pending',
        payment_status='Pending' if payment_method else 'Unpaid',
        payment_method='MoMo' if payment_method else 'COD',
        shipping_address=customer_address,
        total_amount=total_amount
    )
    if order_id:
        order.id = order_id  # Set custom order ID for MoMo
    db.session.add(order)
    db.session.flush()  # Ensure order ID is generated

    for item in cart.values():
        order_detail = OrderDetail(
            order_id=order.id,
            book_id=item['id'],
            quantity=item['quantity'],
            unit_price=item['price']
        )
        db.session.add(order_detail)

    db.session.commit()
    if not payment_method:  # Clear cart for non-MoMo payments
        session.pop('cart', None)
    return order


if __name__ == '__main__':
    with app.app_context():
        print(count_books())