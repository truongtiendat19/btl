import hashlib
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime, Boolean, func, Text
from saleapp import db, app
from enum import Enum as RoleEnum
from flask_login import UserMixin


# phân quyền
class UserRole(RoleEnum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    STAFF = "STAFF"


# thông tin người dùng
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=False,
                    default="https://res.cloudinary.com/dapckqqhj/image/upload/v1734438576/rlpkm5rn7kqct2k5jcir.jpg")
    email = Column(String(50), nullable=True)
    phone = Column(String(50), nullable=True)
    user_role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    import_receipts = relationship('ImportReceipt', backref='user', lazy=True)
    orders = relationship('Order', backref='user', lazy=True)
    cart_items = relationship('CartItem', backref='user', lazy=True)
    purchases = relationship('Purchase', backref='user', lazy=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __str__(self):
        return self.name


# thông tin thể loại sách
class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)

    def __str__(self):
        return self.name


# thông tin tác giả sách
class Author(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)

    def __str__(self):
        return self.name


digitalpricing_books = (
    db.Table('digitalpricing_books', db.Column('digitalpricing_id', db.Integer, db.ForeignKey('digital_pricing.id')),
             db.Column('book_id', db.Integer, db.ForeignKey('book.id'))))


# thông tin sách
class Book(db.Model):
    __tablename__ = 'book'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    author_id = Column(Integer, ForeignKey(Author.id), nullable=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)

    author = relationship('Author', backref='books', lazy=True)
    category = relationship('Category', backref='books', lazy=True)

    image = Column(String(255), nullable=True)
    price_physical = Column(Float, default=0, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    is_digital_avaible = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    book_contents = relationship('BookContent', backref='book', lazy=True)
    digital_pricings = relationship('DigitalPricing', secondary=digitalpricing_books, back_populates='books')
    purchases = relationship('Purchase', backref='book', lazy=True)
    order_detail = relationship('OrderDetail', backref='book', lazy=True)
    import_receipt_detail = relationship('ImportReceiptDetail', back_populates='book', lazy=True)
    cart_items = relationship('CartItem', backref='book', lazy=True)

    def __str__(self):
        return self.name


# đơn hàng
class Order(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(100), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    order_date = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String(50), nullable=False)
    payment_status = Column(String(50), nullable=False)
    payment_method = Column(String(50), nullable=False)
    shipping_address = Column(db.String(255), nullable=False)
    total_amount = Column(Float, nullable=False)
    order_details = relationship('OrderDetail', backref='order', lazy=True, cascade="all, delete-orphan")


# chi tiết đơn hàng
# OrderDetail model
class OrderDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(Order.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    unit_price = Column(Float, default=0, nullable=False)
    reviews = relationship('Review', backref='orderdetail', lazy=True)



# giỏ hàng
class CartItem(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    quantity = Column(Integer, default=1)


# gói thuê sách đọc online
class DigitalPricing(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    access_type = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    duration_day = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    purchases = relationship('Purchase', backref='digital_pricing', lazy=True)
    books = relationship('Book', secondary=digitalpricing_books, back_populates='digital_pricings')


# lịch sử mua quyền đọc sách online
class Purchase(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    unit_price = Column(Float, default=0, nullable=False)
    digital_pricing_id = Column(Integer, ForeignKey(DigitalPricing.id), nullable=False)
    time_start = Column(DateTime, nullable=False)
    time_end = Column(DateTime, nullable=True)
    create_date = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)
    momo_order_id = Column(String(100), nullable=True)
    page_number = Column(Integer, default=1)


# nội dung sách đọc online
class BookContent(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)


# phiếu nhập sách
class ImportReceipt(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    import_date = Column(DateTime, server_default=func.now(), nullable=False)
    total_amount = Column(Float, nullable=False)
    note = Column(String(255), nullable=True)
    import_receipt_detail = relationship('ImportReceiptDetail', backref='import_receipt', lazy=True)


# chi tiết nhập sách
class ImportReceiptDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    import_receipt_id = Column(Integer, ForeignKey(ImportReceipt.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    unit_price = Column(Float, nullable=False)
    book = relationship("Book", back_populates="import_receipt_detail", lazy=True)


# đánh giá sách
class Review(db.Model):  #bình luận
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    order_detail_id = Column(Integer, ForeignKey(OrderDetail.id), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String(255), nullable=False)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    image = db.Column(db.String(255))
    user = db.relationship('User', backref='reviews')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # with app.app_context():
        #     # Tạo người dùng
        #     admin = User(
        #         name='admin',
        #         username='a',
        #         password=hashlib.md5('1'.encode('utf-8')).hexdigest(),
        #         user_role=UserRole.ADMIN
        #     )
        #     db.session.add(admin)
        #
        #     # Thêm tác giả
        #     authors = ["Ngô Tất Tố", "Nguyễn Nhật Ánh", "Tô Hoài", "Kim Lân"]
        #     author_objects = []
        #     for name in authors:
        #         author = Author(name=name)
        #         db.session.add(author)
        #         author_objects.append(author)
        #
        #     # Thêm thể loại
        #     c1 = Category(name='Văn học')
        #     c2 = Category(name='Sách thiếu nhi')
        #     c3 = Category(name='Giáo khoa - tham khảo')
        #     db.session.add_all([c1, c2, c3])
        #     db.session.commit()  # Commit trước để các ID được tạo
        #
        #     # Thêm sách
        #     books_data = [
        #         {
        #             "name": "Bà già xông pha",
        #             "description": "Bão táp mưa sa cũng không cản được Băng Hưu Trí.",
        #             "price_physical": 76000,
        #             "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734544786/m6pygvphn7zlrd3stzbl.jpg",
        #             "author": author_objects[0],
        #             "category": c1
        #         },
        #         {
        #             "name": "Hiểu Về Quyền Trẻ Em - Người Sên",
        #             "description": "Vào một ngày mùa đông cách đây rất nhiều năm",
        #             "price_physical": 50000,
        #             "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734544786/cda1cvom2awwtkoikanr.webp",
        #             "author": author_objects[1],
        #             "category": c2
        #         },
        #         {
        #             "name": "Bầu trời năm ấy",
        #             "description": "Tôi đã yêu em...",
        #             "price_physical": 37000,
        #             "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428224/mljvnwhxmo46ci3ysal2.jpg",
        #             "author": author_objects[2],
        #             "category": c3
        #         },
        #         {
        #             "name": "Đại cương về Nhà nước và Pháp luật",
        #             "description": "Sách giáo khoa, tài liệu cho các trường đại học.",
        #             "price_physical": 45000,
        #             "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/jgwsfsambzvlos5cgk2g.jpg",
        #             "author": author_objects[3],
        #             "category": c1
        #         },
        #         {
        #             "name": "Mình nói gì hạnh phúc",
        #             "description": "Hạnh phúc là gì?",
        #             "price_physical": 90000,
        #             "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428222/y0bg0xxfphgihzt6xflk.jpg",
        #             "author": author_objects[0],
        #             "category": c2
        #         },
        #         {
        #             "name": "Người đàn bà miền núi",
        #             "description": "Miền núi rừng cây xanh tươi tốt.",
        #             "price_physical": 100000,
        #             "image": "https://res.cloudinary.com/dapckqqhj/image/upload/v1734428221/tuizny2flckfxzjbxakp.jpg",
        #             "author": author_objects[0],
        #             "category": c3
        #         }
        #     ]
        #
        #     for b in books_data:
        #         book = Book(
        #             name=b["name"],
        #             description=b["description"],
        #             price_physical=b["price_physical"],
        #             image=b["image"],
        #             author=b["author"],
        #             category=b["category"],
        #             quantity=10,
        #             is_digital_avaible=True
        #         )
        #         db.session.add(book)
        #
        #     db.session.commit()