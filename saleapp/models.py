from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship, backref
from saleapp import app,db, admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime

class TheLoai(db.Model):
    __tablename__ = "TheLoai"
    ma = Column(Integer, primary_key=True,autoincrement=True)
    ten = Column(String(50), nullable=False)
    sachs = relationship('Sach', backref='the_loai', lazy=True)

    def __str__(self):
        return self.name

class Sach(db.Model):
    __tablename__ = "Sach"
    ma = Column(Integer, primary_key=True, autoincrement=True)
    ten = Column(String(50), nullable=False)
    anh_bia = Column(String(255),nullable=True)
    mo_ta = Column(String(255),nullable=True)
    gia = Column(Float, default = 0)
    nha_xuat_ban = Column(String(50), nullable=True)
    nam_xuat_ban = Column(DateTime, nullable=True)
    so_luong = Column(Integer, nullable= True)
    ma_the_loai = Column(Integer, ForeignKey(TheLoai.ma), nullable=False)

    def __str__(self):
        return self.name

admin.add_view(ModelView(TheLoai, db.session))
admin.add_view(ModelView(Sach, db.session))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        c1 = TheLoai(ten='Sách thiếu nhi')
        c2 = TheLoai(ten='Sách văn học')
        c3 = TheLoai(ten='Sách nấu ăn')

        db.session.add_all([c1, c2, c3])
        db.session.commit()

        sachs = [{
            "ten": "Đắc nhân tâm",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 170000,
            "ma_the_loai": 2
        }, {
            "ten": "Percy Jackson & the Olympians: The Lightning Thief",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "Harry Potter",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 200000,
            "ma_the_loai": 2
        }, {
            "ten": "Alice's Adventures in Wonderland",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "iPhone 7 Plus",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "The Magic School Bus",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "iPhone 7 Plus",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "Những câu chuyện ngụ ngôn của Aesop",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "Cô bé Lọ Lem",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "Bạch Tuyết và bảy chú lùn",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "Tintin",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "Mickey Mouse",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "Những người khốn khổ",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 2
        }, {
            "ten": "The Very Hungry Caterpillar",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 17000000,
            "ma_the_loai": 1
        }, {
            "ten": "Truyện Kiều",
            "anh_bia": "https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg",
            "mo_ta": "Apple, 32GB, RAM: 3GB, iOS13",
            "gia": 300000,
            "ma_the_loai": 2
        }]

        for p in sachs:
            prod = Sach(**p)
            db.session.add(prod)
        db.session.commit()

