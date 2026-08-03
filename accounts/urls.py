from django.urls import path
from . import views

urlpatterns = [
    path("register/",views.register,name="register"),
    path("login/",views.auth_login,name="login"),
    path("logout/",views.auth_logout,name="logout"),
    path("admin_dashboard/",views.admin_dashboard,name="admin_dashboard"),
    path("student_dashboard/",views.student_dashboard,name="student_dashboard"),
    path("instructor_dashboard/",views.instructor_dashboard,name="instructor_dashboard"),
]