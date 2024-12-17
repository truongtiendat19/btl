import random
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from saleapp import db, app
from enum import Enum as RoleEnum
import hashlib
from flask_login import UserMixin
from datetime import datetime


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
    products = relationship('Product', backref='category', lazy=True)

    def __str__(self):
        return self.name


class Product(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    price = Column(Float, default=0)
    image = Column(String(100), nullable=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    details = relationship('ReceiptDetails', backref='product', lazy=True)
    comments = relationship('Comment', backref='product', lazy=True)

    def __str__(self):
        return self.name


class Receipt(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    details = relationship('ReceiptDetails', backref='receipt', lazy=True)


class ReceiptDetails(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)


class Comment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(255), nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()



        u = User(name='admin', username='admin', password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                 user_role=UserRole.ADMIN)
        db.session.add(u)
        db.session.commit()

        c1 = Category(name='Mobile')
        c2 = Category(name='Tablet')
        c3 = Category(name='Desktop')

        db.session.add_all([c1, c2, c3])
        db.session.commit()

        data = [{
            "name": "iPhone 7 Plus",
            "description": "Apple, 32GB, RAM: 3GB, iOS13",
            "price": 17000000,
            "image": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1688179242/hclq65mc6so7vdrbp7hz.jpg",
            "category_id": 1
        }, {
            "name": "iPad Pro 2020",
            "description": "Apple, 128GB, RAM: 6GB",
            "price": 37000000,
            "image": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg",
            "category_id": 2
        }, {
            "name": "iPad Pro 2021",
            "description": "Apple, 128GB, RAM: 6GB",
            "price": 37000000,
            "image": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg",
            "category_id": 2
        }, {
            "name": "iPad Pro 2022",
            "description": "Apple, 128GB, RAM: 6GB",
            "price": 37000000,
            "image": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg",
            "category_id": 2
        }, {
            "name": "iPad Pro 2023",
            "description": "Apple, 128GB, RAM: 6GB",
            "price": 37000000,
            "image": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg",
            "category_id": 2
        }, {
            "name": "iPad Pro 2024",
            "description": "Apple, 128GB, RAM: 6GB",
            "price": 37000000,
            "image": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg",
            "category_id": 2
        }]

        for p in data:
            prod = Product(name=p['name'] + ' ' + str(random.randint(1, 100)), description=p['description'], price=p['price'],
                           image=p['image'], category_id=p['category_id'])
            db.session.add(prod)

        db.session.commit()

        c1 = Comment(content='good', product_id=1, user_id=1)
        c2 = Comment(content='nice', product_id=1, user_id=1)
        c3 = Comment(content='excellent', product_id=1, user_id=1)
        db.session.add_all([c1, c2, c3])
        db.session.commit()