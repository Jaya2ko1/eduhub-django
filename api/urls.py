from django.urls import path 
from rest_framework.authtoken.views import obtain_auth_token
from . import views


urlpatterns = [
    path("courseApi/",views.CourseApi.as_view(),name="courseApi"),
    path('courses/create/', views.CourseCreateAPIView.as_view(), name='course-create'),
    path("courses/filter/",views.CourseFilterAPIView.as_view(),name="course_filter"),
    path("token/", obtain_auth_token, name="api-token"),
]
