import cloudinary.uploader, io
from sqlalchemy import extract, func
from saleapp import db, app
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from saleapp.models import (Category, Author, Book, User, UserRole, ImportReceipt,ImportReceiptDetail,
                            Order,OrderDetail, Book, Author, Category, DigitalPricing, BookContent)
from flask_login import current_user, logout_user
from datetime import  datetime
from sqlalchemy.exc import SQLAlchemyError
from flask import request, redirect, url_for, flash, jsonify
from PIL import Image


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
                existing_book = Book.query.filter_by(name=request.form['name']).first()
                if existing_book:
                    flash("Sách này đã tồn tại.", 'danger')
                    return redirect(url_for('.index'))

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
                try:
                    from PIL import Image
                    image = Image.open(image_file.stream)
                    image.verify()
                    image_file.stream.seek(0)
                except (IOError, SyntaxError):
                    flash("File ảnh bìa không hợp lệ! Vui lòng chọn ảnh đúng định dạng.", 'danger')
                    return redirect(url_for('.index'))

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

            if category_id:
                duplicate = Category.query.filter(
                    Category.name == name,
                    Category.id != int(category_id)
                ).first()
                if duplicate:
                    flash('Tên thể loại đã tồn tại.', 'danger')
                    return redirect(url_for('.index'))

                category = Category.query.get(category_id)
                category.name = name
                msg = 'Cập nhật thể loại thành công.'
            else:
                # Thêm mới: kiểm tra trùng bình thường
                if Category.query.filter_by(name=name).first():
                    flash('Thể loại đã tồn tại.', 'danger')
                    return redirect(url_for('.index'))

                category = Category(name=name)
                db.session.add(category)
                msg = 'Thêm thể loại mới thành công.'

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

    @expose('/delete/<int:category_id>')
    def delete_category(self, category_id):
        category = Category.query.get_or_404(category_id)

        if category.books:
            flash('Không thể xoá. Vẫn còn sách thuộc thể loại này.', 'danger')
        else:
            db.session.delete(category)
            db.session.commit()
            flash('Xoá thể loại thành công.', 'success')

        return redirect(url_for('.index'))


# Tạo View cho Author
class AuthorAdminView(AdminView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        authors = Author.query.all()

        if request.method == 'POST':
            author_id = request.form.get('author_id')
            name = request.form['name'].strip()

            if author_id:
                duplicate = Author.query.filter(
                    Author.name == name,
                    Author.id != int(author_id)
                ).first()
                if duplicate:
                    flash('Tên tác giả đã tồn tại.', 'danger')
                    return redirect(url_for('.index'))

                author = Author.query.get(author_id)
                author.name = name
                msg = "Cập nhật tác giả thành công."
            else:
                if Author.query.filter_by(name=name).first():
                    flash('Tác giả đã tồn tại.', 'danger')
                    return redirect(url_for('.index'))

                author = Author(name=name)
                db.session.add(author)
                msg = "Thêm tác giả thành công."

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

    @expose('/delete/<int:author_id>')
    def delete_author(self, author_id):
        author = Author.query.get_or_404(author_id)

        if author.books:
            flash('Không thể xoá. Vẫn còn sách thuộc tác giả này.', 'danger')
        else:
            db.session.delete(author)
            db.session.commit()
            flash('Đã xoá tác giả thành công.', 'success')

        return redirect(url_for('.index'))


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


class AddDigitalPricingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def add_digital_pricing(self):
        books = Book.query.all()
        pricings = DigitalPricing.query.all()

        if request.method == 'POST':
            pricing_id = request.form.get('pricing_id')
            book_ids = request.form.getlist('book_ids')  # lấy nhiều sách
            access_type = request.form.get('access_type')
            price = request.form.get('price')
            duration = request.form.get('duration')

            if not access_type or not price or not duration:
                flash("Vui lòng nhập đầy đủ thông tin gói.", "danger")
                return redirect(url_for('.add_digital_pricing'))

            if pricing_id:
                pricing = DigitalPricing.query.get(pricing_id)
                if not pricing:
                    flash("Gói đọc không tồn tại.", "danger")
                    return redirect(url_for('.index'))
                msg = "Cập nhật gói đọc thành công!"
            else:
                pricing = DigitalPricing()
                db.session.add(pricing)
                msg = "Thêm gói đọc mới thành công!"

            pricing.access_type = access_type
            pricing.price = float(price)
            pricing.duration_day = int(duration)


            if book_ids:
                books_selected = Book.query.filter(Book.id.in_(book_ids)).all()
                pricing.books = books_selected
            else:
                pricing.books = []

            db.session.commit()
            flash(msg, "success")
            return redirect(url_for('.add_digital_pricing'))

        return self.render('admin/add_digital_pricing.html',
                           books=books,
                           pricings=pricings)

    @expose('/<int:pricing_id>')
    def get_pricing(self, pricing_id):
        pricing = DigitalPricing.query.get_or_404(pricing_id)
        book_ids = [b.id for b in pricing.books]
        return jsonify({
            'id': pricing.id,
            'book_ids': book_ids,
            'access_type': pricing.access_type,
            'price': pricing.price,
            'duration_day': pricing.duration_day,
        })


class AddBookContentView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def add_book_content(self):
        all_books = Book.query.all()

        # Lấy những sách đã có nội dung
        book_ids_with_content = db.session.query(BookContent.book_id).distinct().all()
        book_ids_with_content = [b[0] for b in book_ids_with_content]
        books_with_content = Book.query.filter(Book.id.in_(book_ids_with_content)).all()

        selected_book = None
        contents = []

        book_id = request.args.get('book_id')
        if book_id:
            selected_book = Book.query.get(book_id)
            contents = BookContent.query.filter_by(book_id=book_id).order_by(BookContent.page_number).all()

        if request.method == 'POST':
            book_id = request.form.get('book_id')
            page_numbers = request.form.getlist('page_number[]')
            content_texts = request.form.getlist('content[]')

            BookContent.query.filter_by(book_id=book_id).delete()
            for i in range(len(page_numbers)):
                db.session.add(BookContent(
                    book_id=book_id,
                    page_number=int(page_numbers[i]),
                    content=content_texts[i]
                ))
            db.session.commit()
            flash("Đã lưu nội dung sách!", "success")
            return redirect(url_for('.add_book_content'))

        return self.render('admin/add_book_content.html',
                           all_books=all_books,
                           books_with_content=books_with_content,
                           selected_book=selected_book,
                           contents=contents)


class RevenueStatsView(AdminView):
    @expose('/')
    def revenue_stats(self):
        now = datetime.now()
        month = int(request.args.get('month', now.month))
        year = int(request.args.get('year', now.year))

        # Tổng doanh thu
        total_revenue = db.session.query(
            func.sum(OrderDetail.quantity * OrderDetail.unit_price)
        ).join(Order).filter(
            extract('month', Order.order_date) == month,
            extract('year', Order.order_date) == year
        ).scalar() or 0

        # Tổng đơn hàng
        total_orders = db.session.query(Order).filter(
            extract('month', Order.order_date) == month,
            extract('year', Order.order_date) == year
        ).count()

        # Chi phí nhập hàng
        total_cost = db.session.query(
            func.sum(ImportReceiptDetail.quantity * ImportReceiptDetail.unit_price)
        ).join(ImportReceipt).filter(
            extract('month', ImportReceipt.import_date) == month,
            extract('year', ImportReceipt.import_date) == year
        ).scalar() or 0

        # Lợi nhuận
        profit = total_revenue - total_cost

        # Thống kê từng sách
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
                           total_cost=total_cost,
                           profit=profit,
                           stats=stats,
                           month=month,
                           year=year,
                           now=now)


admin.add_view(CategoryAdminView(name='Thể loại', category='Quản lý sách', endpoint='categories'))
admin.add_view(AuthorAdminView(name='Tác giả', category='Quản lý sách', endpoint='authors'))
admin.add_view(BookAdminView(name='Sách', category='Quản lý sách', endpoint='books'))
admin.add_view(ImportBooksView(name='Nhập sách', category='Quản lý kho'))
admin.add_view(ImportReceiptHistoryView(name='Xuất phiếu nhập', category='Quản lý kho'))
# admin.add_view(UserView(User, db.session,name='Tài khoản'))
admin.add_view(AddDigitalPricingView(name='Gói đọc sách', category='Quản lý đọc sách'))
admin.add_view(AddBookContentView(name='Nội dung sách', category='Quản lý đọc sách', endpoint='add_book_content'))
admin.add_view(RevenueStatsView(name="Thống kê bán sách",category = 'Thống kê - Báo cáo', endpoint="revenue_stats"))
admin.add_view(LogoutView(name='Đăng xuất'))