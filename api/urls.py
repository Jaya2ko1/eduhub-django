from django.urls import path 
from . import views


urlpatterns = [
    path("courseApi/",views.CourseApi.as_view(),name="courseApi"),
    path('courses/create/', views.CourseCreateAPIView.as_view(), name='course-create'),
    path("courses/filter/",views.CourseFilterAPIView.as_view(),name="course_filter"),
]
