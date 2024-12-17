from saleapp.models import Category, Book, User, Receipt, ReceiptDetails, Comment
from saleapp import app, db
import hashlib
import cloudinary.uploader
from flask_login import current_user
from sqlalchemy import func
from datetime import datetime


def load_categories():
    return Category.query.order_by('id').all()


def load_books(kw=None, category_id=None, page=1):
    books = Book.query

    if kw:
        books = books.filter(Book.name.contains(kw))

    if category_id:
        books = books.filter(Book.category_id == category_id)

    page_size = app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    books = books.slice(start, start + page_size)

    return books.all()


def count_books():
    return Book.query.count()


def auth_user(username, password, role=None):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    u = User.query.filter(User.username.__eq__(username.strip()),
                          User.password.__eq__(password))
    if role:
        u = u.filter(User.user_role.__eq__(role))

    return u.first()


def add_user(name, username, password, avatar):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    u = User(name=name, username=username, password=password,
             avatar='https://res.cloudinary.com/dapckqqhj/image/upload/v1734438576/rlpkm5rn7kqct2k5jcir.jpg')

    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.avatar = res.get('secure_url')

    db.session.add(u)
    db.session.commit()


def add_receipt(cart):
    if cart:
        r = Receipt(user=current_user)
        db.session.add(r)

        for c in cart.values():
            d = ReceiptDetails(quantity=c['quantity'], unit_price=c['price'],
                               book_id=c['id'], receipt=r)
            db.session.add(d)

        db.session.commit()


def get_user_by_id(id):
    return User.query.get(id)


def revenue_stats(kw=None):
    query = db.session.query(Book.id, Book.name, func.sum(ReceiptDetails.quantity * ReceiptDetails.unit_price))\
                      .join(ReceiptDetails, ReceiptDetails.book_id.__eq__(Book.id)).group_by(Book.id)

    if kw:
        query = query.filter(Book.name.contains(kw))

    return query.all()


def period_stats(p='month', year=datetime.now().year):
    return db.session.query(func.extract(p, Receipt.created_date),
                            func.sum(ReceiptDetails.quantity * ReceiptDetails.unit_price))\
                      .join(ReceiptDetails, ReceiptDetails.receipt_id.__eq__(Receipt.id))\
                      .group_by(func.extract(p, Receipt.created_date), func.extract('year', Receipt.created_date))\
                      .filter(func.extract('year', Receipt.created_date).__eq__(year)).all()


def stats_books():
    return db.session.query(Category.id, Category.name, func.count(Book.id))\
        .join(Book, Book.category_id.__eq__(Category.id), isouter=True).group_by(Category.id).all()


def get_prod_by_id(id):
    return Book.query.get(id)


def load_comments(book_id):
    return Comment.query.filter(Comment.book_id.__eq__(book_id))


def add_comment(content, book_id):
    c = Comment(content=content, book_id=book_id, user=current_user)
    db.session.add(c)
    db.session.commit()

    return c


if __name__ == '__main__':
    with app.app_context():
        print(count_books())