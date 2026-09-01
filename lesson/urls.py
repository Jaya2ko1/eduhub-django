from django.urls import path
from . import views

urlpatterns = [
    path('create/',views.lesson_create,name="lesson_create"),
    path('edit/<int:id>',views.lesson_edit,name="lesson_edit"),
    path('detail/<int:id>',views.lesson_detail,name="lesson_detail"),
    path('list/',views.lesson_list,name="lesson_list"),
    path('search/',views.lesson_search,name="lesson_search"),
    path('delete/<int:id>',views.lesson_delete,name="lesson_delete"),
]
