from django.urls import path
from . import views

urlpatterns = [
    path("create/",views.create_category,name="create_category"),
    path("edit/<int:id>",views.edit_category,name="edit_category"),
    path("delete/<int:id>",views.delete_category,name="delete_category"),
    path("list/",views.list_category,name="list_category"),
    path("search/",views.search,name="search"),
]
