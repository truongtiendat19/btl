from saleapp import db, app, dao
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from saleapp.models import Category, Book, User, UserRole
from flask_login import current_user, logout_user
from flask_admin import BaseView, expose
from flask import redirect

# tùy chỉnh trang admin
class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        return self.render('admin/index.html', cates=dao.stats_books())

# tạo trang chủ admin
admin = Admin(app, name='404 NOT FOUND', template_mode='bootstrap4', index_view=MyAdminIndexView())

# kiểm tra đăng nhập vai trò admin
class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role.__eq__(UserRole.ADMIN)

# tùy chỉnh trang thể loại
class CategoryView(AuthenticatedView):
    can_export = True
    column_searchable_list = ['id', 'name']
    column_filters = ['id', 'name']
    can_view_details = True
    column_list = ['name', 'books']

#  tùy chỉnh trang sách
class BookView(AuthenticatedView):
    column_list = ['name','category_id','author_id','quantity']

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

# tạo chức năng thống kê
class StatsView(MyView):
    @expose("/")
    def index(self):
        # lấy dữ liệu
        stats = dao.revenue_stats()
        stats2 = dao.period_stats()
        return self.render('admin/stats.html', stats=stats, stats2=stats2)


admin.add_view(CategoryView(Category, db.session))
admin.add_view(BookView(Book, db.session))
admin.add_view(AuthenticatedView(User, db.session))
admin.add_view(StatsView(name='Thống kê - báo cáo'))
admin.add_view(LogoutView(name='Đăng xuất'))