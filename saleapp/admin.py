from saleapp import db, app, dao
from dao import revenue_by_category, book_frequency_by_month
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from saleapp.models import Category, Book, User, UserRole, ManageRule
from flask_login import current_user, logout_user
from flask_admin import BaseView, expose
from flask import redirect, request, flash
from datetime import  datetime


# tùy chỉnh trang admin
class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        return self.render('admin/index.html', cates=dao.stats_books())


# tạo trang chủ admin
admin = Admin(app, name='404 NOT FOUND', template_mode='bootstrap4', index_view=MyAdminIndexView(name='Trang chủ'))


# kiểm tra đăng nhập vai trò admin
class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role.__eq__(UserRole.ADMIN)


# tùy chỉnh trang thể loại
class CategoryView(AuthenticatedView):
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
class BookView(AuthenticatedView):
    column_list = ['name','quantity','price']
    column_searchable_list = ['name']
    can_view_details = True
    can_export = True
    column_labels = {
        'name': 'Sách',
        'quantity': 'Số lượng',
        'price':'Giá'
    }

    def is_accessible(self):
        return current_user.is_authenticated and (
                current_user.user_role == UserRole.ADMIN or current_user.user_role == UserRole.MANAGER
        )


class UserView(AuthenticatedView):
    column_list = ['name','username','user_role']
    column_searchable_list = ['name', 'user_role']
    can_view_details = True
    can_export = True
    column_labels = {
        'name': 'Tên',
        'username': 'Tên tài khoản',
        'user_role':'Quyền'
    }


# truy cập được khi đã đăng nhập
class MyView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated


# đăng xuất
class LogoutView(MyView):
    @expose("/")
    def index(self):
        logout_user()
        return redirect('/admin')


# chức năng thống kê
class StatsView(MyView):
    @expose('/')
    def default_view(self):
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)

        # Lấy dữ liệu thống kê
        revenue_stats = revenue_by_category(month, year)
        book_frequency_stats = book_frequency_by_month(month, year)

        # Tổng doanh thu
        total_revenue = sum([r[1] for r in revenue_stats]) if revenue_stats else 0

        return self.render(
            'admin/stats.html',month=month,year=year,revenue_stats=revenue_stats,book_frequency_stats=book_frequency_stats,total_revenue=total_revenue,enumerate=enumerate
        )


# chức năng thay đổi quy định
class ManageRuleView(MyView):
    @expose('/', methods=['GET', 'POST'])
    def manage_view(self):
        rule = ManageRule.query.first()  # Lấy quy định đầu tiên (vì có thể chỉ cần một bản ghi)

        if request.method == 'POST':  # Nếu phương thức là POST, cập nhật quy định
            import_quantity_min = int(request.form.get('import_quantity_min', 0))
            quantity_min = int(request.form.get('quantity_min', 0))
            cancel_time = int(request.form.get('cancel_time', 0))

            if not rule:  # Nếu chưa tồn tại quy định, tạo mới
                rule = ManageRule(
                    import_quantity_min=import_quantity_min,
                    quantity_min=quantity_min,
                    cancel_time=cancel_time,
                    updated_date=datetime.now()
                )
                db.session.add(rule)
            else:  # Cập nhật quy định hiện có
                rule.import_quantity_min = import_quantity_min
                rule.quantity_min = quantity_min
                rule.cancel_time = cancel_time
                rule.updated_date = datetime.now()

            db.session.commit()
            flash("Cập nhật quy định thành công!", "success")
            # return self.render('admin/manage_rules.html')

        return self.render('admin/manage_rules.html', rule=rule)


class AddStaffView(MyView):
    @expose('/', methods=['GET', 'POST'])
    def add_staff(self):
        err_msg = ''
        if request.method.__eq__('POST'):
            password = request.form.get('password')
            confirm = request.form.get('confirm')

            if password.__eq__(confirm):
                data = request.form.copy()
                del data['confirm']


                dao.add_user( **data)
                err_msg = 'Thêm tài khoản thành công !!!'

            else:
                err_msg = 'Mật khẩu không khớp!'

        return self.render('admin/add_staff.html', err_msg=err_msg)


admin.add_view(CategoryView(Category, db.session, name ='Thể loại'))
admin.add_view(BookView(Book, db.session, name='Sách'))
admin.add_view(UserView(User, db.session,name='Tài khoản'))
admin.add_view(StatsView(name='Thống kê - báo cáo'))
admin.add_view(ManageRuleView(name='Quy định'))
admin.add_view(AddStaffView(name='Thêm tài khoản nhân viên'))
admin.add_view(LogoutView(name='Đăng xuất'))