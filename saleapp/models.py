import random
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from saleapp import db, app
from enum import Enum as RoleEnum
import hashlib
from flask_login import UserMixin
from datetime import datetime
import cloudinary

class StaffRole(RoleEnum):
    ADMIN = 1
    STAFF = 2


class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    avatar = Column(String(100),
                    default="https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg")

class Customer(User):
    receipts = relationship('Receipt', backref='customer', lazy=True)
    comments = relationship('Comment', backref='customer', lazy=True)

class Staff(User):
    staff_role = Column(Enum(StaffRole))

class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    books = relationship('Book', backref='category', lazy=True)

    def __str__(self):
        return self.name

author_book = db.Table('author_book',
                       Column('author_id', Integer, ForeignKey('author.id'), primary_key=True),
                       Column('book_id', Integer, ForeignKey('book.id'), primary_key=True))

class Author(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)

class Book(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    image = Column(String(100), nullable=True)
    price = Column(Float, default=0)
    quantity = Column(Integer, nullable=True)
    details = relationship('ReceiptDetails', backref='book', lazy=True)
    comments = relationship('Comment', backref='book', lazy=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    author_id = relationship('Author', secondary='author_book', lazy='subquery', backref=backref('books',lazy=True) )


    def __str__(self):
        return self.name

class Receipt(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now())
    customer_id = Column(Integer, ForeignKey(Customer.id), nullable=False)
    details = relationship('ReceiptDetails', backref='receipt', lazy=True)

class ReceiptDetails(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)

class ImportReceipt(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_import = Column(DateTime, default=datetime.now())
    staff_id = Column(Integer, ForeignKey(Staff.id), nullable=False)
    details = relationship('ImportReceiptDetails', backref='importReceipt', lazy=True)

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
    customer_id = Column(Integer, ForeignKey(Customer.id), nullable=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()


        # u = Staff(name='admin', username='admin', password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
        #          staff_role=StaffRole.ADMIN)
        # db.session.add(u)
        # db.session.commit()

        # a1 = Author(name = 'Catharina Ingelman Sundberg')
        # a2 = Author(name = 'Aleix Cabrera')
        # db.session.add_all([a1, a2])
        # db.session.commit()
        # c1 = Category(name='Văn học')
        # c2 = Category(name='Sách thiếu nhi')
        # c3 = Category(name='Giáo khoa - tham khảo')
        # c4 = Category(name='Tâm lý - kỹ năng sống')
        # c5 = Category(name='Nuôi dạy con')
        # c6 = Category(name='Kinh tế')
        # c7 = Category(name='Sách học ngoại ngữ')
        # c8 = Category(name='Tiểu sử hồi ký')
        #
        # db.session.add_all([c1, c2, c3])
        # db.session.commit()
        #
        #
        # data = [{
        #     "name": "Bà già xông pha",
        #     "description": "Bão táp mưa sa cũng không cản được Băng Hưu Trí. Họ theo đuổi một lý tưởng lớn lao hòng phụng sự công bằng xã hội. Nhưng lý tưởng này cần tiền, rất nhiều tiền. Tiếp tục cướp ngân hàng thì cũng được thôi, nhưng dăm ba triệu đô lúc nà không còn thấm tháp vào đâu so với tham vọng của họ…",
        #     "price": 76000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734544786/m6pygvphn7zlrd3stzbl.jpg",
        #     "category_id": 1,
        #     "author_id": 1
        # }, {
        #     "name": "Hiểu Về Quyền Trẻ Em - Người Sên",
        #     "description": "Vào một ngày mùa đông cách đây rất nhiều năm, tất cả các quốc gia trên hành tinh này đã tụ họp lại để cùng nhau thông qua Tuyên ngôn vê Quyên trẻ em. Bản Tuyên ngôn gồm 10 nguyên tắc, như một lời hiệu triệu tới các dân tộc trên toàn thế giới, rằng phải đảm bảo trẻ em có quyền được chăm sóc sức khỏe, được giáo dục, được vui chơi giải trí, được bảo vệ khỏi sự bóc lột, được thể hiện quan điểm riêng...và nhiều nhiều quyền khác nữa. Tất cả trẻ em đề có những quyền này.",
        #     "price": 14000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734544786/cda1cvom2awwtkoikanr.webp",
        #     "category_id": 2,
        #     "author_id": 2
        # }, {
        #     "name": "Bầu trời năm ấy",
        #     "description": "Apple, 128GB, RAM: 6GB",
        #     "price": 37000000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428224/mljvnwhxmo46ci3ysal2.jpg",
        #     "category_id": 2,
        #     "author_id": 1
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
        #     "category_id": 2,
        #     "author_id": 2
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
        #     "category_id": 1,
        #     "author_id": 2
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
        #     "category_id": 2,
        #     "author_id": 1
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
        #     "category_id": 2,
        #     "author_id": 1
        #     }
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