from saleapp.models import Category, Book, User, Receipt, ReceiptDetails, Comment, BillDetails, Bill
from saleapp import app, db
import hashlib
import cloudinary.uploader
from flask_login import current_user
from sqlalchemy import func
from operator import  or_


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


def add_user(name, username, password, avatar, user_role=None):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    u = User(name=name, username=username, password=password, avatar=avatar, user_role=user_role)

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


def get_book_by_id(id):
    return Book.query.get(id)


def load_comments(book_id):
    return Comment.query.filter(Comment.book_id.__eq__(book_id))


def add_comment(content, book_id):
    c = Comment(content=content, book_id=book_id,user=current_user)
    db.session.add(c)
    db.session.commit()

    return c


def revenue_by_category(month, year):
    return db.session.query(
        Category.name.label("category_name"),
        func.sum(
            func.coalesce(ReceiptDetails.quantity * ReceiptDetails.unit_price, 0) +
            func.coalesce(BillDetails.quantity * BillDetails.unit_price, 0)
        ).label("total_revenue"),
        func.count(
            func.coalesce(ReceiptDetails.id, 0) + func.coalesce(BillDetails.id, 0)
        ).label("total_count")
    )\
    .select_from(Category)\
    .join(Book, Book.category_id == Category.id)\
    .outerjoin(ReceiptDetails, ReceiptDetails.book_id == Book.id)\
    .outerjoin(Receipt, Receipt.id == ReceiptDetails.receipt_id)\
    .outerjoin(BillDetails, BillDetails.book_id == Book.id)\
    .outerjoin(Bill, Bill.id == BillDetails.bill_id)\
    .filter(
        or_(
            func.extract('month', Receipt.created_date) == month,
            func.extract('month', Bill.created_date) == month
        ),
        or_(
            func.extract('year', Receipt.created_date) == year,
            func.extract('year', Bill.created_date) == year
        )
    )\
    .group_by(Category.name).all()


def book_frequency_by_month(month, year):
    total_books = db.session.query(
        func.sum(
            func.coalesce(ReceiptDetails.quantity, 0) + func.coalesce(BillDetails.quantity, 0)
        )
    )\
    .select_from(Book)\
    .outerjoin(ReceiptDetails, ReceiptDetails.book_id == Book.id)\
    .outerjoin(Receipt, Receipt.id == ReceiptDetails.receipt_id)\
    .outerjoin(BillDetails, BillDetails.book_id == Book.id)\
    .outerjoin(Bill, Bill.id == BillDetails.bill_id)\
    .filter(
        or_(
            func.extract('month', Receipt.created_date) == month,
            func.extract('month', Bill.created_date) == month
        ),
        or_(
            func.extract('year', Receipt.created_date) == year,
            func.extract('year', Bill.created_date) == year
        )
    ).scalar()

    query = db.session.query(
        Book.name.label("book_name"),
        Category.name.label("category_name"),
        func.sum(
            func.coalesce(ReceiptDetails.quantity, 0) + func.coalesce(BillDetails.quantity, 0)
        ).label("total_quantity")
    )\
    .select_from(Book)\
    .join(Category, Category.id == Book.category_id)\
    .outerjoin(ReceiptDetails, ReceiptDetails.book_id == Book.id)\
    .outerjoin(Receipt, Receipt.id == ReceiptDetails.receipt_id)\
    .outerjoin(BillDetails, BillDetails.book_id == Book.id)\
    .outerjoin(Bill, Bill.id == BillDetails.bill_id)\
    .filter(
        or_(
            func.extract('month', Receipt.created_date) == month,
            func.extract('month', Bill.created_date) == month
        ),
        or_(
            func.extract('year', Receipt.created_date) == year,
            func.extract('year', Bill.created_date) == year
        )
    )\
    .group_by(Book.name, Category.name)

    # Tính tỷ lệ
    results = []
    for book_name, category_name, quantity in query.all():
        percentage = (quantity / total_books * 100) if total_books else 0
        results.append((book_name, category_name, quantity, round(percentage, 2)))

    return results


def stats_books():
    return db.session.query(Category.id, Category.name, func.count(Book.id))\
        .join(Book, Book.category_id.__eq__(Category.id), isouter=True).group_by(Category.id).all()


if __name__ == '__main__':
    with app.app_context():
        print(count_books())