import cloudinary.uploader
from sqlalchemy import extract
from flask_admin import Admin, AdminIndexView, BaseView, expose
from docx import Document
from saleapp.models import *
from saleapp.dao import *
from flask_login import current_user
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from flask import request, redirect, url_for, jsonify
from PIL import Image

PAGE_SIZE = 12


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
        return current_user.is_authenticated and (
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
            books = Book.query.all()
            authors = Author.query.all()
            categories = Category.query.all()
            return self.render('admin/book_custom_view.html', books=books,
                               authors=authors, categories=categories, show_modal=True,
                               headcontent=headcontent, content=content)
        books = Book.query.all()
        authors = Author.query.all()
        categories = Category.query.all()
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
        error = request.args.get('error')
        return self.render('admin/category_custom_view.html', categories=categories, error=error)

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
            return redirect(url_for('.index', error="Không thể xóa vì thể loại đã có sách."))
        else:
            db.session.delete(category)
            db.session.commit()

        return redirect(url_for('.index'))


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
                    content = 'Tên tác giả đã tồn tại.'
                else:
                    author = Author(name=name)
                    db.session.add(author)
                    db.session.commit()
                    headcontent = 'Thành công'
                    content = 'Đã thêm tác giả mới.'

            authors = Author.query.all()

            return self.render('admin/author_custom_view.html',
                               authors=authors, show_modal=True,
                               headcontent=headcontent, content=content)
        authors = Author.query.all()
        error = request.args.get('error')
        return self.render('admin/author_custom_view.html', authors=authors, error=error)

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
            return redirect(url_for('.index', error="Không thể xóa vì tác giả đã có sách."))
        else:
            db.session.delete(author)
            db.session.commit()

        return redirect(url_for('.index'))


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

    @expose('/receipt/<int:receipt_id>/print')
    def print_import_receipt(self, receipt_id):
        receipt = ImportReceipt.query.get_or_404(receipt_id)

        items = (db.session.query(
            Book.name.label('book_name'),
            ImportReceiptDetail.quantity,
            ImportReceiptDetail.unit_price)
                 .join(Book, Book.id == ImportReceiptDetail.book_id)
                 .filter(ImportReceiptDetail.import_receipt_id == receipt_id)
                 .all())

        return self.render('admin/print_receipt.html', receipt=receipt, items=items, now=datetime.now())

    @expose('/detail/<int:receipt_id>')
    def receipt_detail(self, receipt_id):
        receipt = ImportReceipt.query.get_or_404(receipt_id)
        return jsonify({
            "receipt": {
                "id": receipt.id,
                "user_name": receipt.user.name,
                "import_date": receipt.import_date.strftime('%d/%m/%Y %H:%M:%S'),
                "note": receipt.note,
                "total_amount": receipt.total_amount,
                "details": [
                    {
                        "book_name": d.book.name,
                        "unit_price": d.unit_price,
                        "quantity": d.quantity
                    } for d in receipt.import_receipt_detail
                ]
            }
        })


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
            word_file = request.files.get('word_file')

            # Xóa nội dung cũ
            BookContent.query.filter_by(book_id=book_id).delete()

            if word_file and word_file.filename.endswith('.docx'):
                doc = Document(word_file)
                all_paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

                full_text = "\n".join(all_paragraphs)
                pages = split_text_by_chars(full_text, chars_per_page=1000)

                for i, page_content in enumerate(pages, start=1):
                    db.session.add(BookContent(
                        book_id=book_id,
                        page_number=i,
                        content=page_content
                    ))
                db.session.commit()

            else:
                page_numbers = request.form.getlist('page_number[]')
                content_texts = request.form.getlist('content[]')
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


class OrderSellerView(StaffView):
    @expose('/', methods=['GET'])
    def index(self):
        q = (request.args.get('q') or '').strip()
        status = (request.args.get('status') or '').strip()
        pay = (request.args.get('pay') or '').strip()
        page = int(request.args.get('page', 1))

        query = (db.session.query(
            Order.id, Order.order_id, Order.order_date, Order.status,
            Order.payment_status, Order.payment_method, Order.total_amount,
            User.name.label('customer_name'), User.username.label('customer_username'))
                 .join(User, User.id == Order.user_id))

        if q:
            like = f"%{q}%"
            query = query.filter(
                (Order.order_id.ilike(like)) |
                (User.name.ilike(like)) |
                (User.username.ilike(like))
            )
        if status:
            query = query.filter(Order.status == status)
        if pay:
            query = query.filter(Order.payment_status == pay)

        total_records = query.count()
        orders = (query.order_by(Order.order_date.desc())
                  .limit(PAGE_SIZE)
                  .offset((page - 1) * PAGE_SIZE)
                  .all())
        total_pages = (total_records + PAGE_SIZE - 1) // PAGE_SIZE

        return self.render('admin/order_seller.html',
                           orders=orders, page=page, total_pages=total_pages,
                           total_records=total_records, q=q, status=status, pay_status=pay)

    # Chi tiết đơn
    @expose('/detail/<int:order_id>')
    def detail(self, order_id):
        od = (db.session.query(
            Order.id, Order.order_id, Order.order_date, Order.status,
            Order.payment_status, Order.payment_method, Order.total_amount,
            User.name.label('customer_name'), User.username.label('customer_username'),
            User.email, User.phone, Order.shipping_address)
              .join(User, User.id == Order.user_id)
              .filter(Order.id == order_id)
              .first_or_404())

        items = (db.session.query(
            Book.name.label('book_name'),
            OrderDetail.quantity, OrderDetail.unit_price)
                 .join(Book, Book.id == OrderDetail.book_id)
                 .filter(OrderDetail.order_id == order_id)
                 .all())

        return jsonify({
            'order': {
                'id': od.id,
                'order_id': od.order_id,
                'order_date': od.order_date.strftime('%d/%m/%Y %H:%M'),
                'status': od.status,
                'payment_status': od.payment_status,
                'payment_method': od.payment_method,
                'total_amount': od.total_amount,
                'customer_name': od.customer_name,
                'customer_username': od.customer_username,
                'email': od.email,
                'phone': od.phone,
                'shipping_address': od.shipping_address
            },
            'items': [{'book_name': it.book_name,
                       'quantity': it.quantity,
                       'unit_price': it.unit_price,
                       'line_total': it.quantity * it.unit_price}
                      for it in items]
        })

    # Hủy đơn
    @expose('/cancel', methods=['POST'])
    def cancel(self):
        oid = request.form.get('id')

        order = Order.query.get_or_404(oid)

        if order.status in ('COMPLETED', 'CANCELLED'):
            return jsonify({'ok': False, 'msg': 'Không thể hủy đơn này.'}), 400

        order.status = 'CANCELLED'
        db.session.commit()
        return jsonify({'ok': True})

    # Trang in hoá đơn
    @expose('/invoice/<int:order_id>')
    def invoice(self, order_id):
        od = (db.session.query(
            Order.id, Order.order_id, Order.order_date, Order.status,
            Order.payment_status, Order.payment_method, Order.total_amount,
            User.name.label('customer_name'), User.username.label('customer_username'),
            User.email, User.phone, Order.shipping_address)
              .join(User, User.id == Order.user_id)
              .filter(Order.id == order_id)
              .first_or_404())

        items = (db.session.query(
            Book.name.label('book_name'),
            OrderDetail.quantity, OrderDetail.unit_price)
                 .join(Book, Book.id == OrderDetail.book_id)
                 .filter(OrderDetail.order_id == order_id)
                 .all())

        # render template hoá đơn để in
        return self.render('admin/invoice_print.html', order=od, items=items, now=datetime.now())

    @expose('/update_status', methods=['POST'])
    def update_status(self):
        order_id = request.form.get('id', type=int)
        status = request.form.get('status', type=str)
        payment_status = request.form.get('payment_status', type=str)

        order = Order.query.get_or_404(order_id)

        if status:
            order.status = status
        if payment_status:
            order.payment_status = payment_status

        db.session.commit()
        return jsonify({'ok': True})


# trang thêm tài khoản nv
class AddStaffView(AdminView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if request.method == 'POST':
            staff_id = request.form.get('staff_id')
            name = (request.form.get('name') or '').strip()
            username = (request.form.get('username') or '').strip()
            password = (request.form.get('password') or '').strip()
            is_active = True if request.form.get('is_active') == 'on' else False

            if not username or not name or (not staff_id and not password):
                headcontent = 'Thất bại'
                content = 'Vui lòng nhập đủ Họ tên, Username và Mật khẩu (khi thêm mới).'
                staffs = User.query.filter_by(user_role=UserRole.STAFF).all()
                return self.render('admin/add_staff_user.html',
                                   staffs=staffs, show_modal=True,
                                   headcontent=headcontent, content=content)

            try:
                if staff_id:
                    # sửa
                    duplicate = User.query.filter(
                        User.username == username,
                        User.id != int(staff_id)
                    ).first()
                    if duplicate:
                        headcontent = 'Thất bại'
                        content = 'Username đã tồn tại.'
                    else:
                        staff = User.query.filter_by(id=staff_id, user_role=UserRole.STAFF).first()
                        if staff:
                            staff.name = name
                            staff.username = username
                            staff.is_active = is_active
                            if password:  # chỉ cập nhật nếu nhập mật khẩu mới
                                staff.password = hashlib.md5(password.encode('utf-8')).hexdigest()
                            db.session.commit()
                            headcontent = 'Thành công'
                            content = 'Thông tin nhân viên đã được cập nhật.'
                        else:
                            headcontent = 'Thất bại'
                            content = 'Không tìm thấy nhân viên để sửa.'
                else:
                    # --------- THÊM MỚI ----------
                    if User.query.filter_by(username=username).first():
                        headcontent = 'Thất bại'
                        content = 'Username đã tồn tại.'
                    else:
                        staff = User(
                            name=name,
                            username=username,
                            password=hashlib.md5(password.encode('utf-8')).hexdigest(),
                            user_role=UserRole.STAFF,
                            is_active=is_active
                        )
                        db.session.add(staff)
                        db.session.commit()
                        headcontent = 'Thành công'
                        content = 'Đã thêm nhân viên mới.'
            except Exception as ex:
                db.session.rollback()
                headcontent = 'Thất bại'
                content = f'Có lỗi xảy ra: {ex}'

            staffs = User.query.filter_by(user_role=UserRole.STAFF).all()
            return self.render('admin/add_staff_user.html',
                               staffs=staffs, show_modal=True,
                               headcontent=headcontent, content=content)

        staffs = User.query.filter_by(user_role=UserRole.STAFF).all()
        return self.render('admin/add_staff_user.html', staffs=staffs)

    @expose('/<int:staff_id>')
    def get_staff(self, staff_id):
        staff = User.query.filter_by(id=staff_id, user_role=UserRole.STAFF).first_or_404()
        return jsonify({
            'id': staff.id,
            'name': staff.name,
            'username': staff.username,
            'is_active': staff.is_active
        })


# trang tài khoản khách hàng
class CustomerAccountsView(StaffView):
    @expose('/', methods=['GET'])
    def index(self):
        new_threshold = datetime.utcnow() - timedelta(days=7)

        q = (
            db.session.query(
                User.id,
                User.name,
                User.username,
                User.email,
                User.phone,
                User.created_at,
                func.count(Order.id).label('total_orders'),
                func.coalesce(func.sum(Order.total_amount), 0).label('total_spent')
            )
            .outerjoin(Order, Order.user_id == User.id)
            .filter(User.user_role == UserRole.CUSTOMER)
            .group_by(User.id)
            .order_by(User.created_at.desc())
        )

        customers = q.all()

        total_accounts = len(customers)
        total_new_accounts = sum(1 for c in customers if c.created_at and c.created_at >= new_threshold)

        return self.render(
            'admin/customer_accounts.html',
            customers=customers,
            new_threshold=new_threshold,
            total_accounts=total_accounts,
            total_new_accounts=total_new_accounts
        )


# trang báo cáo bình luận
class ReviewCommentView(AdminView):
    @expose('/', methods=['GET'])
    def index(self):
        days = request.args.get('days', type=int, default=30)
        date_from = datetime.utcnow() - timedelta(days=days)

        # Bình luận mới nhất kèm thông tin sách
        latest_comments = (
            db.session.query(Review)
            .join(OrderDetail, Review.order_detail_id == OrderDetail.id)
            .join(Book, OrderDetail.book_id == Book.id)
            .filter(Review.created_date >= date_from)
            .order_by(Review.created_date.desc())
            .limit(20)
            .all()
        )

        return self.render(
            'admin/stats_comment.html',
            days=days,
            latest_comments=latest_comments
        )


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
            extract('year', Order.order_date) == year,
            Order.payment_status == 'PAID'
        ).scalar() or 0

        # Tổng đơn hàng
        total_orders = db.session.query(Order).filter(
            extract('month', Order.order_date) == month,
            extract('year', Order.order_date) == year,
            Order.payment_status == 'PAID'
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
            extract('year', Order.order_date) == year,
            Order.payment_status == 'PAID'
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
        ).join(Book, Book.id == Purchase.book_id) \
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
admin.add_view(OrderSellerView(endpoint='orders_seller'))
admin.add_view(AddStaffView(endpoint='add_staff'))
admin.add_view(CustomerAccountsView(endpoint='customer_accounts'))
admin.add_view(ReviewCommentView(endpoint="comment_stats"))
admin.add_view(RevenueStatsView(endpoint="revenue_stats"))
admin.add_view(RevenueDigitalStatsView(endpoint='stats_digital'))
