from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from courses.models import Course
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated

from rest_framework.generics import CreateAPIView,ListAPIView,UpdateAPIView,RetrieveAPIView,DestroyAPIView
from .serializers import CourseSerializer
from .permissions import IsTeacherOrAdmin
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination


def get_visible_courses(user):
    """Courses this user may read through the API."""
    if user.role == user.ADMIN:
        return Course.objects.all()
    if user.role == user.TEACHER:
        return Course.objects.filter(Q(status="published") | Q(instructor=user))
    return Course.objects.filter(status="published")






# Create your views here.

class CourseApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        courses = get_visible_courses(request.user)
        paginator = PageNumberPagination()
        paginator.page_size = 5
        paginated_courses = paginator.paginate_queryset(
            courses,
            request
        )
        serializer = CourseSerializer(
            paginated_courses,
            many=True
        )
        return paginator.get_paginated_response(serializer.data)


   
    # def post(self,request):
    #     serializer = CourseSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)    
    #     # serializer.save()
    #     return Response({"message": "Data is created"},status=status.HTTP_201_CREATED)

class CourseCreateAPIView(CreateAPIView):

    queryset = Course.objects.all()

    serializer_class = CourseSerializer

    permission_classes = [
        IsAuthenticated,
        IsTeacherOrAdmin
    ]

    def perform_create(self, serializer):

        user = self.request.user

        if user.role == 'teacher':
            serializer.save(instructor=user)

        else:
            serializer.save()

class CourseUpdateAPIView(UpdateAPIView):

    queryset = Course.objects.all()

    serializer_class = CourseSerializer

    permission_classes = [
        IsAuthenticated,
        IsTeacherOrAdmin
    ]
    def get_queryset(self):
    
        user = self.request.user

        if user.role == 'teacher':
            return Course.objects.filter(instructor=user)

        return Course.objects.all()


class CourseFilterAPIView(ListAPIView):
    queryset = Course.objects.all()
    
    serializer_class = CourseSerializer

    permission_classes = [
        IsAuthenticated,
    ]
    def get_queryset(self):

        courses = get_visible_courses(self.request.user)
         
        course_status = self.request.query_params.get("status")
        category = self.request.query_params.get("category")
        instructor = self.request.query_params.get("instructor")
        query = self.request.query_params.get("search")


        if course_status:
            courses = courses.filter(status=course_status)
        if category:
            courses = courses.filter(category_id=category)
        if instructor:
            courses = courses.filter(instructor_id=instructor)
        if query:
            courses = courses.filter(title__icontains=query)   
            
        return courses

class CoursePaginationAPIView(ListAPIView):
    queryset = Course.objects.all()
    
    serializer_class = CourseSerializer

    permission_classes = [
        IsAuthenticated,
    ]
    def get_queryset(self):
        return get_visible_courses(self.request.user)

    


        

class CourseRetrieveAPIView(RetrieveAPIView):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_visible_courses(self.request.user)


class CourseDeleteAPIView(DestroyAPIView):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated,IsTeacherOrAdmin]
