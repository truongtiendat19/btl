import cloudinary.uploader
from sqlalchemy import extract
from flask_admin import Admin, AdminIndexView, BaseView, expose
from saleapp.models import *
from flask_login import current_user
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from flask import request, redirect, url_for, jsonify
from PIL import Image


# trang chủ
class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        books = db.session.query(Book.id, Book.name, Book.quantity).all()

        return self.render('admin/index.html', books=books, current_user=current_user)


admin = Admin(app, index_view=MyAdminIndexView(name='Trang chủ'))


# kiểm tra quyền
class AdminView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

class StaffView(BaseView):
    def is_accessible(self):
        return (current_user.is_authenticated and
                current_user.user_role == UserRole.ADMIN or current_user.user_role == UserRole.STAFF)


# trang sách
class BookAdminView(StaffView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        books = Book.query.all()
        authors = Author.query.all()
        categories = Category.query.all()

        if request.method == 'POST':
            book_id = request.form.get('book_id')

            if book_id:
                book = Book.query.get(book_id)

                # kiểm tra tên trùng
                duplicate = Book.query.filter(
                    Book.name == request.form['name'],
                    Book.id != int(book_id)
                ).first()

                if duplicate:
                    headcontent = 'Thất bại'
                    content = 'Tên sách đã tồn tại.'
                    return self.render('admin/book_custom_view.html', books=books,
                                       authors=authors, categories=categories, show_modal=True,
                                       headcontent=headcontent, content=content)

            else:
                existing_book = Book.query.filter_by(name=request.form['name']).first()
                if existing_book:
                    headcontent = 'Thất bại'
                    content = 'Tên sách đã tồn tại.'
                    return self.render('admin/book_custom_view.html', books=books,
                                       authors=authors, categories=categories, show_modal=True,
                                       headcontent=headcontent, content=content)

                book = Book()
                db.session.add(book)

            book.name = request.form['name']
            book.author_id = request.form['author_id']
            book.category_id = request.form['category_id']
            book.price_physical = float(request.form.get('price_physical', 0))
            book.is_digital_avaible = 'is_digital_avaible' in request.form
            book.is_active = 'is_active' in request.form
            book.description = request.form.get('description')

            # xử lí, kiểm tra ảnh
            image_file = request.files.get('image')
            if image_file and image_file.filename != '':
                try:
                    image = Image.open(image_file.stream)
                    image.verify()
                    image_file.stream.seek(0)
                except (IOError, SyntaxError):
                    headcontent = 'Thất bại'
                    content = 'File ảnh không hợp lệ.'
                    return self.render('admin/book_custom_view.html', books=books,
                                       authors=authors, categories=categories, show_modal=True,
                                       headcontent=headcontent, content=content)

                result = cloudinary.uploader.upload(image_file, folder="book_images")
                book.image = result['secure_url']

            db.session.commit()
            headcontent = 'Thành công'
            content = 'Sách đã được cập nhật.' if book_id else 'Sách đã được thêm.'

            return self.render('admin/book_custom_view.html', books=books,
                               authors=authors, categories=categories, show_modal=True,
                               headcontent=headcontent, content=content)

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
            'is_active': book.is_active,
            'description': book.description
        })


# trang thể loại
class CategoryAdminView(StaffView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):

        if request.method == 'POST':
            category_id = request.form.get('category_id')
            name = request.form['name'].strip()

            # sửa
            if category_id:
                duplicate = Category.query.filter(
                    Category.name == name,
                    Category.id != int(category_id)
                ).first()

                if duplicate:
                    headcontent = 'Thất bại'
                    content = 'Tên thể loại đã tồn tại.'
                else:
                    category = Category.query.get(category_id)
                    if category:
                        category.name = name
                        db.session.commit()
                        headcontent = 'Thành công'
                        content = 'Tên thể loại đã được sửa.'
                    else:
                        headcontent = 'Thất bại'
                        content = 'Không tìm thấy thể loại để sửa.'
            else:
                # thêm mới
                if Category.query.filter_by(name=name).first():
                    headcontent = 'Thất bại'
                    content = 'Tên thể loại đã tồn tại.'
                else:
                    category = Category(name=name)
                    db.session.add(category)
                    db.session.commit()
                    headcontent = 'Thành công'
                    content = 'Đã thêm thể loại mới.'

            categories = Category.query.all()

            return self.render('admin/category_custom_view.html',
                               categories=categories, show_modal=True,
                               headcontent=headcontent, content=content)
        categories = Category.query.all()
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
            headcontent = 'Thất bại'
            content = 'Không thể xóa, đang có sách thuộc thể loại này. '
        else:
            db.session.delete(category)
            db.session.commit()
            headcontent = 'Thành công'
            content = 'Thể loại đã được xóa.'

        categories = Category.query.all()
        return self.render('admin/category_custom_view.html',
                           categories=categories, show_modal=True,
                           headcontent=headcontent, content=content)


# trang tác giả
class AuthorAdminView(StaffView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):

        if request.method == 'POST':
            author_id = request.form.get('author_id')
            name = request.form['name'].strip()

            # sửa
            if author_id:
                duplicate = Author.query.filter(
                    Author.name == name,
                    Author.id != int(author_id)
                ).first()

                if duplicate:
                    headcontent = 'Thất bại'
                    content = 'Tên tác giả đã tồn tại.'
                else:
                    author = Author.query.get(author_id)
                    if author:
                        author.name = name
                        db.session.commit()
                        headcontent = 'Thành công'
                        content = 'Tên tác giả đã được sửa.'
                    else:
                        headcontent = 'Thất bại'
                        content = 'Không tìm thấy tác giả để sửa.'
            else:
                # thêm mới
                if Author.query.filter_by(name=name).first():
                    headcontent = 'Thất bại'
                    content = 'Tên thể loại đã tồn tại.'
                else:
                    author = Author(name=name)
                    db.session.add(author)
                    db.session.commit()
                    headcontent = 'Thành công'
                    content = 'Đã thêm thể loại mới.'

            authors = Author.query.all()

            return self.render('admin/author_custom_view.html',
                               authors=authors, show_modal=True,
                               headcontent=headcontent, content=content)
        authors = Author.query.all()
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
            headcontent = 'Thất bại'
            content = 'Không thể xóa, đang có sách của tác giả này. '
        else:
            db.session.delete(author)
            db.session.commit()
            headcontent = 'Thành công'
            content = 'Tác giả đã được xóa.'

        authors = author.query.all()
        return self.render('admin/author_custom_view.html',
                           authors=authors, show_modal=True,
                           headcontent=headcontent, content=content)


# trang nhập sách
class ImportBooksView(StaffView):
    @expose('/', methods=['GET', 'POST'])
    def import_books(self):
        current_datetime = datetime.now()
        headcontent = None
        content = None

        if request.method == 'POST':
            books = request.form.getlist('book')
            quantities = request.form.getlist('quantity')
            prices = request.form.getlist('unit_price')
            note = request.form.get("note")

            errors, success = [], []
            total_amount = 0

            try:
                receipt = ImportReceipt(
                    import_date=current_datetime,
                    user_id=current_user.id,
                    total_amount=0,
                    note=note
                )
                db.session.add(receipt)

                for book_name, quantity_str, price_str in zip(books, quantities, prices):
                    book = Book.query.filter_by(name=book_name).first()
                    if not book:
                        errors.append(f"Không tìm thấy sách '{book_name}'.")
                        continue

                    try:
                        quantity = int(quantity_str)
                        price = float(price_str)

                        if quantity < 1 or price < 0:
                            raise ValueError
                    except ValueError:
                        errors.append(
                            f"Sai định dạng dữ liệu cho '{book_name}': SL={quantity_str}, ĐG={price_str}")
                        continue

                    total_amount += quantity * price
                    book.quantity += quantity

                    detail = ImportReceiptDetail(
                        book_id=book.id,
                        quantity=quantity,
                        unit_price=price,
                        import_receipt=receipt
                    )
                    db.session.add(detail)
                    success.append(book.name)

                if success:
                    receipt.total_amount = total_amount
                    db.session.commit()
                    headcontent = "Thành công"
                    content = f"Đã nhập thành công {len(success)} sách."
                else:
                    db.session.rollback()
                    headcontent = "Thất bại"
                    content = errors[0] if errors else "Không thể nhập sách."

            except SQLAlchemyError as e:
                db.session.rollback()
                headcontent = "Thất bại"
                content = f"Lỗi hệ thống: {str(e)}"

        books = Book.query.all()
        books_data = [{
            "name": book.name,
            "category": {"name": book.category.name},
            "author": {"name": book.author.name}
        } for book in books]

        return self.render('admin/import_books.html',
                           books=books,
                           books_data=books_data,
                           show_modal=headcontent is not None,
                           headcontent=headcontent,
                           content=content)


# trang in phiếu nhập
class ImportReceiptHistoryView(StaffView):
    @expose('/')
    def import_receipt_history(self):
        receipts = ImportReceipt.query.order_by(ImportReceipt.import_date.desc()).all()
        return self.render("admin/import_receipt_history.html", receipts=receipts)


# trang thêm gói đọc sách
class AddDigitalPricingView(StaffView):
    @expose('/', methods=['GET', 'POST'])
    def add_digital_pricing(self):
        books = Book.query.all()
        pricings = DigitalPricing.query.all()

        if request.method == 'POST':
            pricing_id = request.form.get('pricing_id')
            book_ids = request.form.getlist('book_ids')
            access_type = request.form.get('access_type')
            price = request.form.get('price')
            is_active = 'is_active' in request.form
            duration = request.form.get('duration')

            if not access_type or not price or not duration:
                headcontent = 'Thất bại'
                content = 'Nhập thiếu thông tin.'
                pricings = DigitalPricing.query.all()
                return self.render('admin/add_digital_pricing.html',
                                   books=books, pricings=pricings, headcontent=headcontent,
                                   content=content, show_modal=True)

            if pricing_id:
                pricing = DigitalPricing.query.get(pricing_id)
                if not pricing:
                    return redirect(url_for('.index'))
            else:
                pricing = DigitalPricing()
                db.session.add(pricing)

            pricing.access_type = access_type
            pricing.price = float(price)
            pricing.duration_day = int(duration)
            pricing.is_active = is_active

            if book_ids:
                books_selected = Book.query.filter(Book.id.in_(book_ids)).all()
                pricing.books = books_selected
            else:
                pricing.books = []

            db.session.commit()
            headcontent = 'Thành công'
            content = 'Lưu gói đọc thành công.'

            pricings = DigitalPricing.query.all()
            return self.render('admin/add_digital_pricing.html',
                               books=books, pricings=pricings, headcontent=headcontent,
                               content=content, show_modal=True)

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


# trang thêm nội dung sách
class AddBookContentView(StaffView):
    @expose('/', methods=['GET', 'POST'])
    def add_book_content(self):
        all_books = Book.query.all()

        book_ids_with_content = db.session.query(BookContent.book_id).distinct().all()
        book_ids_with_content = [b[0] for b in book_ids_with_content]
        books_with_content = Book.query.filter(Book.id.in_(book_ids_with_content)).all()

        selected_book = None
        contents = []

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

            return redirect(url_for('.add_book_content', success='1'))

        book_id = request.args.get('book_id')
        success = request.args.get('success')

        if book_id:
            selected_book = Book.query.get(book_id)
            contents = BookContent.query.filter_by(book_id=book_id).order_by(BookContent.page_number).all()

        headcontent = 'Thành công' if success == '1' else None
        content = 'Nội dung sách đã được lưu.' if success == '1' else None
        show_modal = success == '1'

        return self.render('admin/add_book_content.html',
                           all_books=all_books,
                           books_with_content=books_with_content,
                           selected_book=selected_book,
                           contents=contents,
                           headcontent=headcontent,
                           content=content,
                           show_modal=show_modal)


# trang báo cáo bán sách
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

        stats = db.session.query(
            Category.name,
            func.sum(OrderDetail.quantity * OrderDetail.unit_price)
        ).join(Book, Book.category_id == Category.id) \
            .join(OrderDetail, OrderDetail.book_id == Book.id) \
            .join(Order, Order.id == OrderDetail.order_id) \
            .filter(
            extract('month', Order.order_date) == month,
            extract('year', Order.order_date) == year
        ).group_by(Category.id).all()

        return self.render('admin/stats.html',
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           total_cost=total_cost,
                           profit=profit,
                           stats=stats,
                           month=month,
                           year=year,
                           now=now)


# trang báo cáo đọc sách
class RevenueDigitalStatsView(BaseView):
    @expose('/')
    def index(self):
        now = datetime.now()
        month = int(request.args.get('month', now.month))
        year = int(request.args.get('year', now.year))

        total_orders = db.session.query(Purchase).filter(
            extract('month', Purchase.create_date) == month,
            extract('year', Purchase.create_date) == year,
            Purchase.status == 'COMPLETED'
        ).count()

        total_revenue = db.session.query(
            func.sum(Purchase.unit_price)
        ).filter(
            extract('month', Purchase.create_date) == month,
            extract('year', Purchase.create_date) == year,
            Purchase.status == 'COMPLETED'
        ).scalar() or 0

        stats = db.session.query(
            Book.name,
            func.sum(Purchase.unit_price)
        ).join(Book, Book.id == Purchase.book_id)\
         .filter(
            extract('month', Purchase.create_date) == month,
            extract('year', Purchase.create_date) == year,
            Purchase.status == 'COMPLETED'
        ).group_by(Book.id).all()

        return self.render('admin/stats_digital.html',
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           stats=stats,
                           month=month,
                           year=year,
                           now=now)


admin.add_view(CategoryAdminView(endpoint='categories'))
admin.add_view(AuthorAdminView(endpoint='authors'))
admin.add_view(BookAdminView(endpoint='books'))
admin.add_view(ImportBooksView(endpoint='import_books'))
admin.add_view(ImportReceiptHistoryView(endpoint='import_receipts_history'))
admin.add_view(AddDigitalPricingView(endpoint='add_digital_pricing'))
admin.add_view(AddBookContentView(endpoint='add_book_content'))
admin.add_view(RevenueStatsView(endpoint="revenue_stats"))
admin.add_view(RevenueDigitalStatsView(endpoint='stats_digital'))
