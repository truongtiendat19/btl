
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from saleapp import db, app
from enum import Enum as RoleEnum
import hashlib
from flask_login import UserMixin
from datetime import datetime


class UserRole(RoleEnum):
    ADMIN = 1
    MANAGER = 2
    STAFF = 3
    CUSTOMER =4


# người dùng
class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    avatar = Column(String(100), default="https://res.cloudinary.com/dapckqqhj/image/upload/v1734438576/rlpkm5rn7kqct2k5jcir.jpg")
    receipts = relationship('Receipt', backref='user', lazy=True)
    comments = relationship('Comment', backref='user', lazy=True)
    bills = relationship('Bill', backref='user', lazy=True)
    import_receipt = relationship('ImportReceipt', backref='user', lazy=True)
    user_role = Column(Enum(UserRole))


# thể loại
class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    books = relationship('Book', backref='category', lazy=True)

    def __str__(self):
        return self.name


# tác giả
class Author(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    books = relationship('Book', backref='author', lazy=True)

    def __str__(self):
        return self.name


# sách
class Book(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    image = Column(String(100), nullable=True)
    price = Column(Float, default=0)
    quantity = Column(Integer, nullable=False, default= 0)
    receipt_details = relationship('ReceiptDetails', backref='book', lazy=True)
    bill_details = relationship('BillDetails', backref='book', lazy=True)
    import_receipt_details = relationship('ImportReceiptDetails', backref='book', lazy=True)
    comments = relationship('Comment', backref='book', lazy=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    author_id = Column(Integer, ForeignKey(Author.id), nullable=False)


    def __str__(self):
        return self.name


# hóa đơn cho khách đặt trực tuyến
class Receipt(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    details = relationship('ReceiptDetails', backref='receipt', lazy=True)


# chi tiết hóa đơn trực tuyến
class ReceiptDetails(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)


# hóa đơn cho khách mua trực tiếp
class Bill(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now())
    name_customer = Column(String(50), nullable=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    details = relationship('BillDetails', backref='bill', lazy=True)


# chi tiết hóa đơn mua trực tiếp
class BillDetails(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    receipt_id = Column(Integer, ForeignKey(Bill.id), nullable=False)


# phiếu nhập sách
class ImportReceipt(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_import = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    details = relationship('ImportReceiptDetails', backref='importReceipt', lazy=True)


# chi tiết phiếu nhập sách
class ImportReceiptDetails(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    quantity = Column(Integer, default=0)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    importreceipt_id = Column(Integer, ForeignKey(ImportReceipt.id), nullable=False)


class Comment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(255), nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        u = User(name='manager', username='m', password=str(hashlib.md5('1'.encode('utf-8')).hexdigest()),
                  user_role=UserRole.MANAGER,
                  avatar='https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg')
        db.session.add(u)
        db.session.commit()

        u = User(name='admin', username='admin1', password=str(hashlib.md5('123456789'.encode('utf-8')).hexdigest()),
                 user_role=UserRole.ADMIN, avatar='https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg')
        db.session.add(u)
        db.session.commit()

        authors = ["Ngô Tất Tố","Nguyễn Nhật Ánh", "Tô Hoài","Kim Lân"]
        author_objects = []
        for author_name in authors:
            author = Author(name=author_name)
            db.session.add(author)
            author_objects.append(author)
        db.session.commit()


        c1 = Category(name='Văn học')
        c2 = Category(name='Sách thiếu nhi')
        c3 = Category(name='Giáo khoa - tham khảo')

        db.session.add_all([c1, c2, c3])
        db.session.commit()


        data = [{
            "name": "Bà già xông pha",
            "description": "Bão táp mưa sa cũng không cản được Băng Hưu Trí.",
            "price": 76000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734544786/m6pygvphn7zlrd3stzbl.jpg",
            "author_id": 1,
            "category_id": 1
        }, {
            "name": "Hiểu Về Quyền Trẻ Em - Người Sên",
            "description": "Vào một ngày mùa đông cách đây rất nhiều năm",
            "price": 50000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734544786/cda1cvom2awwtkoikanr.webp",
            "author_id": 2,
            "category_id": 2
        }, {
            "name": "Bầu trời năm ấy",
            "description": "Tôi đã yêu em...",
            "price": 37000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428224/mljvnwhxmo46ci3ysal2.jpg",
            "author_id": 3,
            "category_id": 3
        }, {
            "name": "Đại cương về Nhà nước và Pháp luật",
            "description": "Sách giáo khoa, tài liệu cho các trường đại học.",
            "price": 45000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/jgwsfsambzvlos5cgk2g.jpg",
            "author_id": 4,
            "category_id": 1
        }, {
            "name": "Mình nói gì hạnh phúc",
            "description": "Hạnh phúc là gì?",
            "price": 90000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/y0bg0xxfphgihzt6xflk.jpg",
            "author_id": 1,
            "category_id": 2
        }, {
            "name": "Người đàn bà miền núi",
            "description": "Miền núi rừng cây xanh tươi tốt.",
            "price": 100000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
            "author_id": 1,
            "category_id": 3
        },{
            "name": "Hoa",
            "description": "Một rừng hoa mai nở.",
            "price": 70000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
            "author_id": 2,
            "category_id": 3
        },{
            "name": "Xu Xu đừng khóc",
            "description": "Đừng khóc nữa Xu ơi...",
            "price": 45000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428226/fxuiaviysvpqgu5wz2ot.jpg",
            "author_id": 2,
            "category_id": 1
        }, {
            "name": "Sóc sợ sệt",
            "description": "Một con sóc đi lạc..",
            "price": 60000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428225/ud0apghlk6bhl4giilk9.jpg",
            "author_id": 3,
            "category_id": 2
        }, {
            "name": "Bầu trời ngày hôm ấy",
            "description": "Rất đẹp!",
            "price": 81000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428224/mljvnwhxmo46ci3ysal2.jpg",
            "author_id": 3,
            "category_id": 2
        }, {
            "name": "Nhà nước và Pháp luật",
            "description": "Đại cương.",
            "price": 99000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/jgwsfsambzvlos5cgk2g.jpg",
            "author_id": 4,
            "category_id": 1
        }, {
            "name": "Hạnh Phúc",
            "description": "Là gì?",
            "price": 101000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/y0bg0xxfphgihzt6xflk.jpg",
            "author_id": 4,
            "category_id": 3
        }, {
            "name": "Đàn bà",
            "description": "Là những niềm đau?",
            "price": 77000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
            "author_id": 1,
            "category_id": 2
        }, {
            "name": "Hoa bằng lăng",
            "description": "Nở rộ...",
            "price": 55000,
            "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
            "author_id": 2,
            "category_id": 1
            }
        ]

        for p in data:
            prod = Book(name=p['name'], description=p['description'], price=p['price'],
                           image=p['image'], category_id=p['category_id'], author_id=p['author_id'])
            db.session.add(prod)

        db.session.commit()
