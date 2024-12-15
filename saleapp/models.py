from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from saleapp import app,db
from datetime import datetime

class TheLoai(db.Model):
    __tablename__ = "TheLoai"
    ma = Column(Integer, primary_key=True,autoincrement=True)
    ten = Column(String(50), nullable=False)
    sachs = relationship('Sach', backref='the_loai', lazy=True)

class Sach(db.Model):
    __tablename__ = "Sach"
    ma = Column(Integer, primary_key=True, autoincrement=True)
    ten = Column(String(50), nullable=False)
    anh_bia = Column(String(255),nullable=True)
    mo_ta = Column(String(255),nullable=True)
    gia = Column(Float, default = 0)
    nha_xuat_ban = Column(String(50), nullable=False)
    nam_xuat_ban = Column(DateTime, nullable=False)
    so_luong = Column(Integer, nullable= False)
    ma_the_loai = Column(Integer, ForeignKey(TheLoai.ma), nullable=False)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

