from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:id>/',views.student_enrollment,name="enrollment"),
   
]
