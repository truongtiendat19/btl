import random
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from saleapp import db, app
from enum import Enum as RoleEnum
import hashlib
from flask_login import UserMixin
from datetime import datetime
import cloudinary

class UserRole(RoleEnum):
    ADMIN = 1
    USER = 2


class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    avatar = Column(String(100),
                    default="https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg")
    user_role = Column(Enum(UserRole), default=UserRole.USER)
    receipts = relationship('Receipt', backref='user', lazy=True)
    comments = relationship('Comment', backref='user', lazy=True)


class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    books = relationship('Book', backref='category', lazy=True)

    def __str__(self):
        return self.name

class Author(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    books = relationship('Book', backref='author', lazy=True)

class Book(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    image = Column(String(100), nullable=True)
    price = Column(Float, default=0)
    quantity = Column(Integer, nullable=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    details = relationship('ReceiptDetails', backref='book', lazy=True)
    comments = relationship('Comment', backref='book', lazy=True)

    def __str__(self):
        return self.name


class Receipt(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    details = relationship('ReceiptDetails', backref='receipt', lazy=True)


class ReceiptDetails(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)


class Comment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(255), nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()



        # u = User(name='admin', username='admin', password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
        #          user_role=UserRole.ADMIN)
        # db.session.add(u)
        # db.session.commit()
        #
        # c1 = Category(name='Mobile')
        # c2 = Category(name='Tablet')
        # c3 = Category(name='Desktop')
        #
        # db.session.add_all([c1, c2, c3])
        # db.session.commit()
        #
        #
        # data = [{
        #     "name": "Xu Xu đừng khóc",
        #     "description": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "price": 17000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428226/fxuiaviysvpqgu5wz2ot.jpg",
        #     "category_id": 1
        # }, {
        #     "name": "Sóc sợ sệt",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428225/ud0apghlk6bhl4giilk9.jpg",
        #     "category_id": 2
        # }, {
        #     "name": "Bầu trời năm ấy",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428224/mljvnwhxmo46ci3ysal2.jpg",
        #     "category_id": 2
        # }, {
        #     "name": "Đại cương về Nhà nước và Pháp luật",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/jgwsfsambzvlos5cgk2g.jpg",
        #     "category_id": 2
        # }, {
        #     "name": "Mình nói gì hạnh phúc",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/y0bg0xxfphgihzt6xflk.jpg",
        #     "category_id": 2
        # }, {
        #     "name": "Người đàn bà miền núi ",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
        #     "category_id": 2
        # },{
        #     "name": "Hoa ",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
        #     "category_id": 2
        # },{
        #     "name": "Xu Xu đừng khóc 1",
        #     "description": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "price": 17000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428226/fxuiaviysvpqgu5wz2ot.jpg",
        #     "category_id": 1
        # }, {
        #     "name": "Sóc sợ sệt 2",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428225/ud0apghlk6bhl4giilk9.jpg",
        #     "category_id": 2
        # }, {
        #     "name": "Bầu trời năm ấy 2",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428224/mljvnwhxmo46ci3ysal2.jpg",
        #     "category_id": 2
        # }, {
        #     "name": "Đại cương về Nhà nước và Pháp luật 2",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/jgwsfsambzvlos5cgk2g.jpg",
        #     "category_id": 2
        # }, {
        #     "name": "Mình nói gì hạnh phúc 2",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/y0bg0xxfphgihzt6xflk.jpg",
        #     "category_id": 2
        # }, {
        #     "name": "Người đàn bà miền núi 2",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
        #     "category_id": 2
        # }, {
        #     "name": "Hoa 2",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
        #     "category_id": 2}
        # ]
        #
        # for p in data:
        #     prod = Book(name=p['name'] + ' ' + str(random.randint(1, 100)), description=p['description'], price=p['price'],
        #                    image=p['image'], category_id=p['category_id'])
        #     db.session.add(prod)
        #
        # db.session.commit()
        #
        # c1 = Comment(content='good', book_id=1, user_id=1)
        # c2 = Comment(content='nice', book_id=1, user_id=1)
        # c3 = Comment(content='excellent', book_id=1, user_id=1)
        # db.session.add_all([c1, c2, c3])
        # db.session.commit()