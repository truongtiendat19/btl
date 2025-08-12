import json
import os
from datetime import datetime, timedelta
from flask import session
from saleapp.models import Category, Book, User, Author, Review, OrderDetail, Order, Purchase
from saleapp import app, db
import hashlib
import cloudinary.uploader
from sqlalchemy import func
from flask_login import current_user
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from base64 import b64encode
import logging

import numpy as np
from urllib.request import urlopen
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def encrypt_payload(data):
    with open('mykey.pem', 'r') as f:
        key = RSA.importKey(f.read())
    cipher = PKCS1_v1_5.new(key)
    cipher_text = cipher.encrypt(json.dumps(data).encode())
    return b64encode(cipher_text).decode()


def load_comments(book_id):
    return Review.query.join(OrderDetail).filter(OrderDetail.book_id == book_id)\
        .order_by(Review.created_date.desc()).all()



def load_categories():
    return Category.query.order_by('id').all()


def load_authors():
    return Author.query.order_by('id').all()


def load_books(kw=None, category_id=None, author_id=None, price_filter=None, page=1):
    books = Book.query

    if kw:
        books = books.filter(Book.name.contains(kw))
    if category_id:
        try:
            books = books.filter(Book.category_id == int(category_id))
        except ValueError:
            pass
    if author_id:
        try:
            books = books.filter(Book.author_id == int(author_id))
        except ValueError:
            pass

    if price_filter:
        try:
            if '+' in price_filter:
                min_price = int(price_filter.replace('+', ''))
                books = books.filter(Book.price_physical >= min_price)
            else:
                min_price, max_price = map(int, price_filter.split('-'))
                books = books.filter(Book.price_physical >= min_price, Book.price_physical <= max_price)
        except Exception as e:
            print("Lỗi khi xử lý:", e)

    # phân trang
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


def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User.query.filter(User.username.__eq__(username.strip()),
                          User.password.__eq__(password))

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
    return db.session.get(Book, id)



def stats_books():
    return db.session.query(Category.id, Category.name, func.count(Book.id)) \
        .join(Book, Book.category_id.__eq__(Category.id), isouter=True).group_by(Category.id).all()


def add_receipt(cart, customer_phone, customer_address, payment_method, delivery_method, order_id=None):
    if not cart:
        return None

    total_amount = sum(item['quantity'] * item['price'] for item in cart.values())
    order = Order(
        user_id=current_user.id,
        order_date=datetime.now(),
        status='PENDING',
        payment_status='UNPAID',
        payment_method='MoMo',
        shipping_address=customer_address,
        total_amount=total_amount
    )

    # Chỉ gán order_id nếu có (UUID chuỗi), và gán vào cột order_id, KHÔNG gán vào id (int)
    if order_id:
        order.order_id = order_id

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

    # Xoá giỏ hàng nếu là COD (MoMo sẽ xoá sau khi callback thành công)
    if not payment_method:
        session.pop('cart', None)

    return order

def clean_expired_pending_purchases():
    expiration_time = datetime.now() - timedelta(minutes=11)
    expired = Purchase.query.filter(
        Purchase.status == 'PENDING',
        Purchase.create_date <= expiration_time
    ).all()

    for p in expired:
        db.session.delete(p)
    db.session.commit()

def add_comment(book_id, content, rating=5, image=None):
    try:
        if not Book.query.get(book_id):
            raise ValueError("Sách không tồn tại")

        now = datetime.now()
        # Kiểm tra quyền mua sách qua Purchase (gói đọc trực tuyến)
        purchase = Purchase.query.filter(
            Purchase.book_id == book_id,
            Purchase.user_id == current_user.id,
            Purchase.time_start <= now,
            Purchase.time_end >= now,
            Purchase.status == 'COMPLETED'
        ).first()

        # Kiểm tra quyền mua sách qua Order (sách vật lý)
        order_detail = OrderDetail.query.join(Order).filter(
            Order.user_id == current_user.id,
            OrderDetail.book_id == book_id,
            Order.payment_status == 'PAID'
        ).first()

        # Yêu cầu ít nhất một trong hai điều kiện trên phải đúng
        if not (purchase or order_detail):
            raise ValueError("Bạn cần mua sách trước khi bình luận")

        # Sử dụng order_detail_id từ đơn hàng nếu có, nếu không thì để null
        order_detail_id = order_detail.id if order_detail else None

        # Nếu không có order_detail_id (chỉ có Purchase), vẫn cho phép bình luận
        if not order_detail_id and not purchase:
            raise ValueError("Không tìm thấy đơn hàng hoặc gói đọc hợp lệ để bình luận")

        c = Review(
            user_id=current_user.id,
            order_detail_id=order_detail_id,
            rating=rating,
            comment=content,
            image=image
        )
        db.session.add(c)
        db.session.commit()
        return c
    except Exception as e:
        logger.error(f"Lỗi khi thêm bình luận: {str(e)}")
        db.session.rollback()
        raise


if __name__ == '__main__':
    with app.app_context():
        print(count_books())