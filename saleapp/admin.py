from saleapp import db, app, dao
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from saleapp.models import Category, Book, User, UserRole
from flask_login import current_user, logout_user
from flask_admin import BaseView, expose
from flask import redirect, request, flash, url_for
from datetime import  datetime
from sqlalchemy.exc import SQLAlchemyError


# tùy chỉnh trang admin
class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        return self.render('admin/index.html', cates=dao.stats_books())


# tạo trang chủ admin
admin = Admin(app, name='404 NOT FOUND', template_mode='bootstrap4', index_view=MyAdminIndexView(name='Trang chủ'))


class MyAdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class AdminView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


# tùy chỉnh trang thể loại
class CategoryView(MyAdminView):
    can_export = True
    column_searchable_list = ['name']
    # column_filters = ['name']
    can_view_details = True
    column_list = ['name', 'books']
    column_labels = {
        'name': 'Thể loại',
        'books': 'Sách'
    }


#  tùy chỉnh trang sách
class BookView(MyAdminView):
    column_list = ['name','quantity','price_physical']
    column_searchable_list = ['name']
    can_view_details = True
    can_export = True
    can_edit = True
    column_labels = {
        'name': 'Tên sách',
        'quantity': 'Số lượng',
        'price_physical':'Giá'
    }


class UserView(MyAdminView):
    column_list = ['name','username','user_role']
    column_searchable_list = ['name', 'user_role']
    can_view_details = True
    can_export = True
    column_labels = {
        'name': 'Tên',
        'username': 'Tên tài khoản',
        'user_role':'Quyền'
    }


# đăng xuất
class LogoutView(BaseView):
    @expose("/")
    def index(self):
        logout_user()
        return redirect('/login')

#
# # chức năng thống kê
# class StatsView(AdminView):
#     @expose('/')
#     def stats_view(self):
#         month = request.args.get('month', datetime.now().month, type=int)
#         year = request.args.get('year', datetime.now().year, type=int)
#
#         # Lấy dữ liệu thống kê
#         revenue_stats = revenue_by_category(month, year)
#         book_frequency_stats = book_frequency_by_month(month, year)
#
#         # Tổng doanh thu
#         total_revenue = sum([r[1] for r in revenue_stats]) if revenue_stats else 0
#
#         return self.render(
#             'admin/stats.html',month=month,year=year,revenue_stats=revenue_stats,book_frequency_stats=book_frequency_stats,total_revenue=total_revenue,enumerate=enumerate
#         )


# chức năng thay đổi quy định
# class ManageRuleView(AdminView):
#     @expose('/', methods=['GET', 'POST'])
#     def manage_view(self):
#         rule = ManageRule.query.first()  # Lấy quy định đầu tiên (vì có thể chỉ cần một bản ghi)
#
#         if request.method == 'POST':  # Nếu phương thức là POST, cập nhật quy định
#             import_quantity_min = int(request.form.get('import_quantity_min', 0))
#             quantity_min = int(request.form.get('quantity_min', 0))
#             cancel_time = int(request.form.get('cancel_time', 0))
#
#             if not rule:  # Nếu chưa tồn tại quy định, tạo mới
#                 rule = ManageRule(
#                     import_quantity_min=import_quantity_min,
#                     quantity_min=quantity_min,
#                     cancel_time=cancel_time,
#                     updated_date=datetime.now()
#                 )
#                 db.session.add(rule)
#             else:  # Cập nhật quy định hiện có
#                 rule.import_quantity_min = import_quantity_min
#                 rule.quantity_min = quantity_min
#                 rule.cancel_time = cancel_time
#                 rule.updated_date = datetime.now()
#
#             db.session.commit()
#             flash("Cập nhật quy định thành công!", "success")
#             # return self.render('admin/manage_rules.html')
#
#         return self.render('admin/manage_rules.html', rule=rule)


# thêm tài khoản
class AddStaffView(AdminView):
    @expose('/', methods=['GET', 'POST'])
    def add_staff(self):
        err_msg = ''  # Biến lưu thông báo lỗi
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            confirm = request.form.get('confirm')

            # Kiểm tra mật khẩu và username
            if password == confirm:
                if dao.check_username_exists(username):
                    err_msg = 'Thêm KHÔNG thành công, username đã tồn tại!!!'
                else:
                    data = request.form.copy()
                    del data['confirm']

                    dao.add_user(**data)
                    err_msg = 'Thêm tài khoản thành công!'
            else:
                err_msg = 'Mật khẩu không khớp!'

        # Truyền err_msg sang giao diện
        return self.render('admin/add_staff.html', err_msg=err_msg)


# # nhập sách
# class ImportBooksView(ManagerView):
#     @expose('/', methods=['GET', 'POST'])
#     def import_books(selt):
#         rule = ManageRule.query.first()
#         current_datetime = datetime.now()
#         db.session.refresh(rule)
#         if request.method == 'POST':
#             date_import = request.form.get('date_import', datetime.now().strftime('%Y-%m-%d'))
#             books = request.form.getlist('book')
#             categories = request.form.getlist('category')
#             authors = request.form.getlist('author')
#             quantities = request.form.getlist('quantity')
#
#             errors = []
#             success = []
#
#             try:
#                 import_receipt = ImportReceipt(date_import=date_import, user_id=current_user.id)
#                 db.session.add(import_receipt)
#
#                 for book_name, category_name, author_name, quantity_str in zip(books, categories, authors, quantities):
#                     try:
#                         book = Book.query.filter_by(name=book_name).first()
#                         if not book:
#                             errors.append(f"Không tìm thấy đầu sách '{book_name}' trong kho")
#                             continue
#
#                         try:
#                             quantity = int(quantity_str)
#                         except ValueError:
#                             errors.append(f"Số lượng '{quantity_str}' không hợp lệ cho sách '{book_name}'!")
#                             continue
#
#                         # Kiểm tra số lượng nhập tối thiểu
#                         if quantity < rule.import_quantity_min:
#                             errors.append(
#                                 f"Số lượng nhập cho sách '{book_name}' phải lớn hơn hoặc bằng {rule.import_quantity_min}!"
#                             )
#                             continue
#
#                         if book.quantity > rule.quantity_min:
#                             errors.append(
#                                 f"Số lượng sách '{book_name}' trong kho lớn hơn '{rule.quantity_min}' cuốn!"
#                             )
#                             continue
#                         else:
#                             book.quantity += quantity
#
#                         # Thêm chi tiết hóa đơn nhập
#                         receipt_detail = ImportReceiptDetails(
#                             quantity=quantity,
#                             book_id=book.id,
#                             import_receipt=import_receipt
#                         )
#                         db.session.add(receipt_detail)
#                         success.append(f"Nhập thành công sách '{book_name}' với số lượng {quantity}!")
#
#
#                     except ValueError:
#                         errors.append(f"Số lượng '{quantity_str}' không hợp lệ cho sách '{book_name}'!")
#                     except SQLAlchemyError as e:
#                         errors.append(f"Lỗi cơ sở dữ liệu khi nhập sách '{book_name}': {str(e)}")
#
#                 db.session.commit()
#
#                 if success:
#                     flash(" ".join(success), "success")
#                 if errors:
#                     flash(" ".join(errors), "danger")
#
#             except SQLAlchemyError as e:
#                 db.session.rollback()
#                 flash(f"Lỗi khi tạo hóa đơn nhập: {str(e)}", "danger")
#
#             # Dùng class name hoặc route chính xác của view
#             return redirect(url_for('importbooksview.import_books'))
#
#         # Lấy dữ liệu sách
#         books = Book.query.all()
#         books_data = [{
#             "name": book.name,
#             "category": {"name": book.category.name},
#             "author": {"name": book.author.name}
#         } for book in books]
#
#         return selt.render('admin/import_books.html', current_datetime=current_datetime, rule=rule, books=books, books_data=books_data)

#
# admin.add_view(CategoryView(Category, db.session, name ='Thể loại'))
# admin.add_view(BookView(Book, db.session, name='Sách'))
admin.add_view(UserView(User, db.session,name='Tài khoản'))
# admin.add_view(StatsView(name='Thống kê - báo cáo'))
# admin.add_view(ManageRuleView(name='Quy định'))
# admin.add_view(AddStaffView(name='Thêm tài khoản nhân viên'))
# admin.add_view(ImportBooksView(name='Nhập sách'))
admin.add_view(LogoutView(name='Đăng xuất'))