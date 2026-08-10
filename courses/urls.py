from django.urls import path
from . import views

urlpatterns = [
    path("create/",views.create_course,name="create_course"),
    path("edit/<int:id>/",views.edit_course,name="edit_course"),
    path("view/<int:id>/",views.view_course,name="view_course"),
    path("delete/<int:id>/",views.delete_course,name="delete_course"),
    path("list/",views.list_course,name="list_course"),
    path("search_course/",views.search_course,name="search_course"),

]