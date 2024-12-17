import random
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from saleapp import db, app, admin
from enum import Enum as RoleEnum
from flask_admin.contrib.sqla import ModelView
import hashlib
from flask_login import UserMixin
from datetime import datetime

# class UserRole(RoleEnum):
#     ADMIN = 1
#     USER = 2
#
# class User(db.Model, UserMixin):
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), nullable=False)
#     username = Column(String(100), nullable=False, unique=True)
#     password = Column(String(100), nullable=False)
#     avatar = Column(String(100),
#                     default="https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg")
#     user_role = Column(Enum(UserRole), default=UserRole.USER)
#     receipts = relationship('Receipt', backref='user', lazy=True)
#     comments = relationship('Comment', backref='user', lazy=True)
#
class Category(db.Model):
    __tablename__ = "Category"
    ma = Column(Integer, primary_key=True,autoincrement=True)
    name = Column(String(50), nullable=False)
    books = relationship('Book', backref='category', lazy=False)

    def __str__(self):
        return self.name

class Book(db.Model):
    __tablename__ = "Book"
    ma = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    anh_bia = Column(String(255),nullable=True)
    mo_ta = Column(String(255),nullable=True)
    gia = Column(Float, default = 0)
    nha_xuat_ban = Column(String(50), nullable=True)
    nam_xuat_ban = Column(DateTime, nullable=True)
    so_luong = Column(Integer, nullable= True)
    ma_the_loai = Column(Integer, ForeignKey(Category.ma), nullable=False)

    def __str__(self):
        return self.name

class CategoryModelView(ModelView):
    can_create = True
    form_columns = ['name', 'ma', 'books']

class BookModelView(ModelView):
    can_create = True
    form_columns = ['name', 'ma_the_loai']  # Các trường trong biểu mẫu
    # form_overrides = {
    #     'category': SelectField  # Tùy chỉnh kiểu nhập liệu cho trường category
    # }
    # form_args = {
    #     'category': {
    #         'choices': [(category.id, category.ten) for category in Category.query.all()]
    #         # Hiển thị danh sách các category
    #     }
    # }


admin.add_view(CategoryModelView(Category, db.session))
admin.add_view(BookModelView(Book, db.session))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        c1 = Category(name='Sách thiếu nhi')
        c2 = Category(name='Sách văn học')
        c3 = Category(name='Sách nấu ăn')

        db.session.add_all([c1, c2, c3])
        db.session.commit()

        # books = [{
        #     "ten": "Đắc nhân tâm",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 170000,
        #     "ma_the_loai": 2
        # }, {
        #     "ten": "Percy Jackson & the Olympians: The Lightning Thief",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "Harry Potter",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 200000,
        #     "ma_the_loai": 2
        # }, {
        #     "ten": "Alice's Adventures in Wonderland",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "iPhone 7 Plus",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "The Magic School Bus",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "iPhone 7 Plus",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "Những câu chuyện ngụ ngôn của Aesop",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "Cô bé Lọ Lem",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "Bạch Tuyết và bảy chú lùn",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "Tintin",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "Mickey Mouse",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "Những người khốn khổ",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 2
        # }, {
        #     "ten": "The Very Hungry Caterpillar",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 17000000,
        #     "ma_the_loai": 1
        # }, {
        #     "ten": "Truyện Kiều",
        #     "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
        #     "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
        #     "gia": 300000,
        #     "ma_the_loai": 2
        # }]
        #
        # for p in books:
        #     prod = Book(**p)
        #     db.session.add(prod)
        # db.session.commit()


