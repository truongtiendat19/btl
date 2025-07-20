import cloudinary.uploader
from sqlalchemy import extract, func
from saleapp import db, app
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from saleapp.models import Category, Author, Book, User, UserRole, ImportReceipt, ImportReceiptDetail, Order,OrderDetail, Book, Author, Category
from flask_login import current_user, logout_user
from datetime import  datetime
from sqlalchemy.exc import SQLAlchemyError
from flask_admin import BaseView, expose
from flask import request, redirect, url_for, flash, jsonify
import cloudinary.uploader


# tùy chỉnh trang admin
class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        books = db.session.query(Book.id, Book.name, Book.quantity).all()
        return self.render('admin/index.html', books=books, current_user=current_user)


# tạo trang chủ admin
admin = Admin(app, name='ReadZone', index_view=MyAdminIndexView(name='Trang chủ'))


class MyAdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class AdminView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


# trang quản lí thể loại sách
class CategoryView(MyAdminView):
    can_export = True
    column_searchable_list = ['name']
    can_delete = False
    column_list = ['name']
    column_labels = {
        'name': 'Thể loại',
    }


# trang quản lí thông tin tác giả
class AuthorView(MyAdminView):
    can_export = True
    column_searchable_list = ['name']
    can_delete = False
    column_list = ['name']
    column_labels = {
        'name': 'Tác giả',
    }


# trang quản lí thông tin sách
class BookView(MyAdminView):
    column_list = ['name', 'category', 'author', 'price_physical']
    column_searchable_list = ['name']
    can_view_details = True
    can_export = True
    can_edit = True
    can_delete = False
    column_labels = {
        'name': 'Tên sách',
        'category': 'Thể loại',
        'author': 'Tác giả',
        'quantity': 'Số lượng',
        'image': 'Ảnh bìa',
        'price_physical': 'Giá',
        'is_digital_avaible':'Đọc trực tuyến',
        'description': 'Mô tả'
    }
    form_columns = [
        'name',
        'author',
        'category',
        'image',
        'price_physical',
        'is_digital_avaible',
        'description'
    ]

    def _category_formatter(view, context, model, name):
        return model.category.name if model.category else ''

    def _author_formatter(view, context, model, name):
        return model.author.name if model.author else ''

    column_formatters = {
        'category': _category_formatter,
        'author': _author_formatter,
    }


# trang quản lí user
class UserView(MyAdminView):
    column_list = ['name','user_role','email','phone']
    column_searchable_list = ['name', 'user_role']
    can_export = True
    can_delete = False
    can_edit = False
    column_labels = {
        'name': 'Tên',
        'username': 'Tên tài khoản',
        'user_role':'Vai trò',
        'password': 'Mật khẩu',
        'email':'Email',
        'phone':'Số điện thoại'
    }
    form_columns = [
        'name',
        'username',
        'password',
        'email',
        'phone',
        'user_role'
    ]


# đăng xuất
class LogoutView(BaseView):
    @expose("/")
    def index(self):
        logout_user()
        return redirect('/login')


class BookAdminView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        books = Book.query.all()
        authors = Author.query.all()
        categories = Category.query.all()

        if request.method == 'POST':
            book_id = request.form.get('book_id')
            if book_id:
                book = Book.query.get(book_id)
                msg = "Cập nhật sách thành công!"
            else:
                book = Book()
                db.session.add(book)
                msg = "Thêm sách mới thành công!"

            book.name = request.form['name']
            book.author_id = request.form['author_id']
            book.category_id = request.form['category_id']
            book.price_physical = float(request.form.get('price_physical', 0))
            book.is_digital_avaible = 'is_digital_avaible' in request.form
            book.description = request.form.get('description')

            image_file = request.files.get('image')
            if image_file and image_file.filename != '':
                result = cloudinary.uploader.upload(image_file, folder="book_images")
                book.image = result['secure_url']

            db.session.commit()
            flash(msg, 'success')
            return redirect(url_for('.index'))

        return self.render('admin/book_custom_view.html', books=books, authors=authors, categories=categories)

    @expose('/<int:book_id>')
    def get_book(self, book_id):
        book = Book.query.get_or_404(book_id)
        return jsonify({
            'id': book.id,
            'name': book.name,
            'author_id': book.author_id,
            'category_id': book.category_id,
            'image': book.image,
            'price_physical': book.price_physical,
            'quantity': book.quantity,
            'is_digital_avaible': book.is_digital_avaible,
            'description': book.description
        })


# Tạo View cho Category
class CategoryAdminView(AdminView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        categories = Category.query.all()

        if request.method == 'POST':
            category_id = request.form.get('category_id')
            name = request.form['name'].strip()

            # Kiểm tra trùng tên khi thêm mới
            if not category_id and Category.query.filter_by(name=name).first():
                flash('❌ Thể loại đã tồn tại!', 'danger')
            else:
                if category_id:
                    category = Category.query.get(category_id)
                    category.name = name
                    msg = '✅ Cập nhật thể loại thành công!'
                else:
                    category = Category(name=name)
                    db.session.add(category)
                    msg = '✅ Thêm thể loại thành công!'

                db.session.commit()
                flash(msg, 'success')
                return redirect(url_for('.index'))

        return self.render('admin/category_custom_view.html', categories=categories)

    @expose('/<int:category_id>')
    def get_category(self, category_id):
        category = Category.query.get_or_404(category_id)
        return jsonify({
            'id': category.id,
            'name': category.name
        })


# Tạo View cho Author
class AuthorAdminView(AdminView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        authors = Author.query.all()

        if request.method == 'POST':
            author_id = request.form.get('author_id')
            name = request.form['name'].strip()

            # Kiểm tra trùng khi thêm mới
            if not author_id and Author.query.filter_by(name=name).first():
                flash('❌ Tác giả đã tồn tại!', 'danger')
            else:
                if author_id:
                    author = Author.query.get(author_id)
                    author.name = name
                    msg = "✅ Cập nhật tác giả thành công!"
                else:
                    author = Author(name=name)
                    db.session.add(author)
                    msg = "✅ Thêm tác giả thành công!"

                db.session.commit()
                flash(msg, 'success')
                return redirect(url_for('.index'))

        return self.render('admin/author_custom_view.html', authors=authors)

    @expose('/<int:author_id>')
    def get_author(self, author_id):
        author = Author.query.get_or_404(author_id)
        return jsonify({
            'id': author.id,
            'name': author.name
        })


# trang nhập sách
class ImportBooksView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def import_books(self):
        current_datetime = datetime.now()

        if request.method == 'POST':
            date_import = request.form.get('date_import', current_datetime.strftime('%Y-%m-%d'))
            books = request.form.getlist('book')
            quantities = request.form.getlist('quantity')
            prices = request.form.getlist('unit_price')
            note = request.form.get("note")

            errors, success = [], []
            total_amount = 0

            try:
                receipt = ImportReceipt(
                    import_date=date_import,
                    user_id=current_user.id,
                    total_amount=0,
                    note=note
                )
                db.session.add(receipt)

                for book_name, quantity_str, price_str in zip(books, quantities, prices):
                    book = Book.query.filter_by(name=book_name).first()
                    if not book:
                        errors.append(f"❌ Không tìm thấy sách '{book_name}'.")
                        continue

                    try:
                        quantity = int(quantity_str)
                        price = float(price_str)

                        if quantity < 1 or price < 0:
                            raise ValueError
                    except ValueError:
                        errors.append(f"❌ Dữ liệu không hợp lệ cho sách '{book_name}': SL={quantity_str}, ĐG={price_str}")
                        continue

                    # Cộng dồn tổng tiền
                    total_amount += quantity * price

                    # Cập nhật kho sách
                    book.quantity += quantity

                    detail = ImportReceiptDetail(
                        book_id=book.id,
                        quantity=quantity,
                        unit_price=price,
                        import_receipt=receipt
                    )
                    db.session.add(detail)

                    success.append(f"✅ Đã nhập {quantity} quyển '{book.name}' với đơn giá {price:,.0f}đ")

                # Gán lại tổng tiền vào phiếu
                receipt.total_amount = total_amount
                db.session.commit()

                if success:
                    flash(" ".join(success), "success")
                if errors:
                    flash(" ".join(errors), "danger")

            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"❌ Lỗi hệ thống: {str(e)}", "danger")

            return redirect(url_for('importbooksview.import_books'))

        # Load danh sách sách để fill form
        books = Book.query.all()
        books_data = [{
            "name": book.name,
            "category": {"name": book.category.name},
            "author": {"name": book.author.name}
        } for book in books]

        return self.render('admin/import_books.html',
                           books=books,
                           books_data=books_data,
                           current_datetime=current_datetime)


class ImportReceiptHistoryView(AdminView):
    @expose('/')
    def import_receipt_history(self):
        receipts = ImportReceipt.query.order_by(ImportReceipt.import_date.desc()).all()
        return self.render("admin/import_receipt_history.html", receipts=receipts)


class RevenueStatsView(AdminView):
    @expose('/')
    def revenue_stats(self):

        # Lấy tháng & năm hiện tại
        now = datetime.now()
        month = int(request.args.get('month', now.month))
        year = int(request.args.get('year', now.year))

        # Thống kê doanh thu đơn hàng trong tháng
        orders_in_month = db.session.query(Order).filter(
            extract('month', Order.order_date) == month,
            extract('year', Order.order_date) == year
        ).all()

        total_revenue = sum(order.total_amount for order in orders_in_month)
        total_orders = len(orders_in_month)

        # Thống kê số lượng bán ra của từng sách
        stats = db.session.query(
            Book.name,
            func.sum(OrderDetail.quantity),
            func.sum(OrderDetail.quantity * OrderDetail.unit_price)
        ).join(OrderDetail).join(Order).filter(
            extract('month', Order.order_date) == month,
            extract('year', Order.order_date) == year
        ).group_by(Book.id).all()

        return self.render('admin/stats.html',
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           stats=stats,
                           month=month,
                           year=year)


admin.add_view(CategoryAdminView(name='Thể loại', category='Quản lý sách', endpoint='categories'))
admin.add_view(AuthorAdminView(name='Tác giả', category='Quản lý sách', endpoint='authors'))
admin.add_view(BookAdminView(name='Sách', category='Quản lý sách', endpoint='books'))
admin.add_view(ImportBooksView(name='Nhập sách', category='Quản lý kho'))
admin.add_view(ImportReceiptHistoryView(name='Xuất phiếu nhập', category='Quản lý kho'))
admin.add_view(UserView(User, db.session,name='Tài khoản'))
admin.add_view(RevenueStatsView(name="Thống kê - Báo cáo", endpoint="revenue_stats"))
admin.add_view(LogoutView(name='Đăng xuất'))