from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime, Boolean
from saleapp import db, app
from enum import Enum as RoleEnum
import hashlib
from flask_login import UserMixin
from datetime import datetime

# phân quyền
class UserRole(RoleEnum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"


# thông tin người dùng
class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=False, default="https://res.cloudinary.com/dapckqqhj/image/upload/v1734438576/rlpkm5rn7kqct2k5jcir.jpg")
    email = Column(String(50), nullable = True)
    phone = Column(String(50), nullable= True)
    user_role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    reviews = relationship('Review', backref='user', lazy=True)
    import_receipts = relationship('ImportReceipt', backref='user', lazy=True)
    orders = relationship('Order', backref='user', lazy=True)
    cart_items = relationship('CartItem',backref='user', lazy=True)
    purchases = relationship('Purchase', backref='user', lazy=True)


# thông tin thể loại sách
class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    books = relationship('Book', backref='category', lazy=True)


# thông tin tác giả sách
class Author(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    books = relationship('Book', backref='author', lazy=True)


# thông tin sách
class Book(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    author_id = Column(Integer, ForeignKey(Author.id), nullable=False)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    image = Column(String(255), nullable=True)
    price_physical = Column(Float, default=0, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    is_digital_avaible = Column(Boolean, default= False)
    description = Column(String(255), nullable=True)
    book_contents = relationship('BookContent', backref='book', lazy=True)
    digital_pricings = relationship('DigitalPricing', backref='book', lazy=True)
    purchases = relationship('Purchase', backref='book', lazy=True)
    order_details = relationship('OrderDetail', backref='book', lazy=True)
    import_receipt_details = relationship('ImportReceiptDetail', backref='book', lazy=True)
    cart_items = relationship('CartItem', backref='book', lazy=True)
    reviews = relationship('Review', backref='book', lazy=True)
    discounts = relationship('Discount', backref='book', lazy=True)


# đơn hàng của người dùng
class Order(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    order_date = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(String(50), nullable=False)
    payment_status = Column(String(50), nullable=False)
    payment_method = Column(String(50), nullable=False)
    shipping_address = Column(db.String(255), nullable=False)
    total_amount = Column(Float, nullable=False)
    order_details = relationship('OrderDetail', backref='order', lazy=True, cascade="all, delete-orphan")


# chi tiết đơn hàng
class OrderDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(Order.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    unit_price = Column(Float, default=0, nullable=False)


# giỏ hàng
class CartItem(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    quantity = Column(Integer, default=1)


# giá thuê sách đọc online
class DigitalPricing(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    access_type = Column(String(100), nullable = False)
    price = Column(Float, nullable = False)
    duration_day = Column(Integer, nullable = False)
    purchases = relationship('Purchase', backref='digital_pricing', lazy=True)


# lịch sử mua quyền đọc sách online
class Purchase(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    digital_pricing_id = Column(Integer, ForeignKey(DigitalPricing.id), nullable=False)
    time_start = Column(DateTime, nullable=False)
    time_end = Column(DateTime, nullable=False)
    create_date = Column(DateTime,default=datetime.now, nullable=False)


# nội dung sách đọc online
class BookContent(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(String(10000), nullable=False)


# phiếu nhập sách
class ImportReceipt(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    import_date = Column(DateTime, default=datetime.now, nullable=False)
    total_amount = Column(Float, nullable= False)
    note = Column (String(255), nullable=True)
    import_receipt_details = relationship('ImportReceiptDetail', backref='import_receipt', lazy=True)


# chi tiết nhập sách
class ImportReceiptDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    import_receipt_id = Column(Integer, ForeignKey(ImportReceipt.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    unit_price = Column(Float, nullable= False)


# đánh giá sách
class Review(db.Model): #bình luận
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String(255), nullable=False)
    created_date = Column(DateTime, default=datetime.now, nullable=False)


# thông tin giảm giá
class Discount(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    discount_type = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()


        # u = User(name='admin', username='a', password=str(hashlib.md5('1'.encode('utf-8')).hexdigest()),
        #          user_role=UserRole.ADMIN)
        # db.session.add(u)
        # u = User(name='staff', username='s', password=str(hashlib.md5('1'.encode('utf-8')).hexdigest()),
        #          user_role=UserRole.STAFF)
        # db.session.add(u)
        # db.session.commit()
        #
        # authors = ["Ngô Tất Tố","Nguyễn Nhật Ánh", "Tô Hoài","Kim Lân"]
        # author_objects = []
        # for author_name in authors:
        #     author = Author(name=author_name)
        #     db.session.add(author)
        #     author_objects.append(author)
        # db.session.commit()
        #
        #
        # c1 = Category(name='Văn học')
        # c2 = Category(name='Sách thiếu nhi')
        # c3 = Category(name='Giáo khoa - tham khảo')
        #
        # db.session.add_all([c1, c2, c3])
        # db.session.commit()
        #
        #
        # data = [{
        #     "name": "Bà già xông pha",
        #     "description": "Bão táp mưa sa cũng không cản được Băng Hưu Trí.",
        #     "price": 76000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734544786/m6pygvphn7zlrd3stzbl.jpg",
        #     "author_id": 1,
        #     "category_id": 1
        # }, {
        #     "name": "Hiểu Về Quyền Trẻ Em - Người Sên",
        #     "description": "Vào một ngày mùa đông cách đây rất nhiều năm",
        #     "price": 50000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734544786/cda1cvom2awwtkoikanr.webp",
        #     "author_id": 2,
        #     "category_id": 2
        # }, {
        #     "name": "Bầu trời năm ấy",
        #     "description": "Tôi đã yêu em...",
        #     "price": 37000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428224/mljvnwhxmo46ci3ysal2.jpg",
        #     "author_id": 3,
        #     "category_id": 3
        # }, {
        #     "name": "Đại cương về Nhà nước và Pháp luật",
        #     "description": "Sách giáo khoa, tài liệu cho các trường đại học.",
        #     "price": 45000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/jgwsfsambzvlos5cgk2g.jpg",
        #     "author_id": 4,
        #     "category_id": 1
        # }, {
        #     "name": "Mình nói gì hạnh phúc",
        #     "description": "Hạnh phúc là gì?",
        #     "price": 90000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/y0bg0xxfphgihzt6xflk.jpg",
        #     "author_id": 1,
        #     "category_id": 2
        # }, {
        #     "name": "Người đàn bà miền núi",
        #     "description": "Miền núi rừng cây xanh tươi tốt.",
        #     "price": 100000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
        #     "author_id": 1,
        #     "category_id": 3
        # },{
        #     "name": "Hoa",
        #     "description": "Một rừng hoa mai nở.",
        #     "price": 70000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
        #     "author_id": 2,
        #     "category_id": 3
        # },{
        #     "name": "Xu Xu đừng khóc",
        #     "description": "Đừng khóc nữa Xu ơi...",
        #     "price": 45000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428226/fxuiaviysvpqgu5wz2ot.jpg",
        #     "author_id": 2,
        #     "category_id": 1
        # }, {
        #     "name": "Sóc sợ sệt",
        #     "description": "Một con sóc đi lạc..",
        #     "price": 60000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428225/ud0apghlk6bhl4giilk9.jpg",
        #     "author_id": 3,
        #     "category_id": 2
        # }, {
        #     "name": "Bầu trời ngày hôm ấy",
        #     "description": "Rất đẹp!",
        #     "price": 81000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428224/mljvnwhxmo46ci3ysal2.jpg",
        #     "author_id": 3,
        #     "category_id": 2
        # }, {
        #     "name": "Nhà nước và Pháp luật",
        #     "description": "Đại cương.",
        #     "price": 99000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/jgwsfsambzvlos5cgk2g.jpg",
        #     "author_id": 4,
        #     "category_id": 1
        # }, {
        #     "name": "Hạnh Phúc",
        #     "description": "Là gì?",
        #     "price": 101000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/y0bg0xxfphgihzt6xflk.jpg",
        #     "author_id": 4,
        #     "category_id": 3
        # }, {
        #     "name": "Đàn bà",
        #     "description": "Là những niềm đau?",
        #     "price": 77000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
        #     "author_id": 1,
        #     "category_id": 2
        # }, {
        #     "name": "Hoa bằng lăng",
        #     "description": "Nở rộ...",
        #     "price": 55000,
        #     "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
        #     "author_id": 2,
        #     "category_id": 1
        #     }
        # ]
        #
        # for p in data:
        #     prod = Book(name=p['name'], description=p['description'], price=p['price'],
        #                    image=p['image'], category_id=p['category_id'], author_id=p['author_id'])
        #     db.session.add(prod)

        db.session.commit()
