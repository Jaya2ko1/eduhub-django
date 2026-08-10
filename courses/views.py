from django.shortcuts import render,redirect,get_object_or_404

from .models import Category
from .forms import CourseForm
from .models import Course
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .utils import get_courses_by_user



# Create your views here.

def create_course(request):
    if request.method == "POST":
        form = CourseForm(request.POST,request.FILES,user=request.user)
        if form.is_valid():
            form.save()
            return redirect('list_course')
    else:
        form = CourseForm(user=request.user)
    return render(request,"courses/course_create.html",{'form':form})

def edit_course(request,id):
    get_course = get_object_or_404(Course,id=id)
    if request.method == "POST":
        form = CourseForm(request.POST,request.FILES,instance=get_course)
        if form.is_valid():
            form.save()
            return redirect('list_course')
    else:
        form=CourseForm(instance=get_course)
    return render(request,"courses/course_update.html",{'form':form})

def view_course(request,id):
    get_course = get_object_or_404(Course,id=id)
    form=CourseForm(instance=get_course)
    return render(request,"courses/course_view.html",{'form':form})

def list_course(request):
    get_course = get_courses_by_user(request.user)

    paginator = Paginator(get_course, 5)  
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"courses/course_list.html",{'page_obj':page_obj})

def delete_course(request,id):
    get_course = get_object_or_404(Course,id=id)
    get_course.delete() 
    messages.success(request, "Course deleted successfully.") 
    return redirect('list_course') 

from django.db.models import Q

def search_course(request):
    categories = Category.objects.all()
    courses = get_courses_by_user(request.user)

    query = request.GET.get("search")
    category = request.GET.get("category")
    status = request.GET.get("status")

    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(price__icontains=query)
        )

    if category:
        courses = courses.filter(category_id=category)

    if status:
        courses = courses.filter(status=status)

    return render(request, "courses/course_search.html", {
        "courses": courses,
        "categories": categories,
        "query": query,
        "category": category,
        "status": status,
    })
   



       