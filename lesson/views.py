from django.shortcuts import render,get_object_or_404,redirect
from .forms import LessonForm
from .models import Lesson,Course
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q



# Create your views here.
def lesson_create(request):
    if request.method == "POST":
        form = LessonForm(request.POST,request.FILES,user=request.user)
        if form.is_valid():
            form.save()
            return redirect('lesson_list')
    else:
        form = LessonForm(user=request.user)
    return render(request,"lesson_create.html",{'form':form})

def lesson_edit(request,id):
    lesson_id = get_object_or_404(Lesson,id=id)
    if request.method == "POST":
        form = LessonForm(request.POST,request.FILES,instance=lesson_id,user=request.user)
        if form.is_valid():
            form.save()
            return redirect('lesson_list')
    else:
        form=LessonForm(instance=lesson_id,user=request.user)
    return render(request,'lesson_update.html',{'form':form})

def lesson_detail(request,id):
    lesson_id = get_object_or_404(Lesson,id=id)
    return render(request,"lesson_detail.html",{'lesson':lesson_id})


def lesson_list(request):
    all_lesson = Lesson.objects.all().order_by('order_number')
   

    if request.user:
        if request.user.role == request.user.TEACHER:
            courses = Course.objects.filter(instructor=request.user.id)
            all_lesson = Lesson.objects.filter(instructor=request.user.id).order_by('order_number')
        else:
            courses = Course.objects.all()
    paginator = Paginator(all_lesson, 5) 
        
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"lesson_list.html",{'page_obj':page_obj,'courses':courses})

def lesson_delete(request,id):
    get_lesson = get_object_or_404(Lesson,id=id)
    get_lesson.delete()
    messages.success(request, "Course deleted successfully.")
    return redirect('lesson_list')

def lesson_search(request):
    
    query  = request.GET.get("search","")
    course = request.GET.get("course","")
    status = request.GET.get("status","")

    if request.user:
        if request.user.role == request.user.TEACHER:
            courses = Course.objects.filter(instructor=request.user.id)
            search_lesson = Lesson.objects.filter(instructor=request.user.id).order_by('order_number')

        else:
            courses = Course.objects.all()
            search_lesson = Lesson.objects.all()

    
    # Start with all lessons

    if query :
        search_lesson = search_lesson.filter(Q (title__icontains = query ) | 
                                          Q (course__title__icontains = query ))
    if course:
        search_lesson = search_lesson.filter(course_id=course,)
  
    if status:
        search_lesson = search_lesson.filter(status=status)

    paginator = Paginator(search_lesson, 5)  
     
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"lesson_search.html",{
        'page_obj':page_obj,
        'courses' : courses,
        'course':course,
        "query": query,
        "status":status,
        })
    

