from django.shortcuts import render,get_object_or_404,redirect
from .forms import LessonForm
from .models import Lesson,Course
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required



@login_required
def get_next_order_number(request):
    course_id = request.GET.get("course_id")
    if not course_id:
        return JsonResponse({"order_number": 1})

    last_lesson = (
        Lesson.objects
        .filter(course_id=course_id)
        .order_by("-order_number")
        .first()
    )

    if last_lesson:
        next_order = last_lesson.order_number + 1
    else:
        next_order = 1

    return JsonResponse({
        "order_number": next_order
    })



# Create your views here.
def lesson_create(request):
    if request.method == "POST":
        form = LessonForm(request.POST,request.FILES,user=request.user)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.instructor = request.user
            lesson.save()
            return redirect('lesson_list')
    else:
        form = LessonForm(user=request.user)
    return render(request,"lesson_create.html",{'form':form})

def lesson_edit(request,id):
    if request.user.role == request.user.ADMIN:
        lesson = get_object_or_404(Lesson, id=id)
    elif request.user.role == request.user.TEACHER:
        lesson = get_object_or_404(
            Lesson,
            id=id,
            instructor=request.user
        )

    else:
        return redirect('student_dashboard')
    if request.method == "POST":
        form = LessonForm(request.POST,request.FILES,instance=lesson,user=request.user)
        if form.is_valid():
            form.save()
            return redirect('lesson_list')
    else:
        form=LessonForm(instance=lesson,user=request.user)
    return render(request,'lesson_update.html',{'form':form})

def lesson_detail(request,id):
    if request.user.role == request.user.ADMIN:
            lesson = get_object_or_404(Lesson, id=id)
    
    elif request.user.role == request.user.TEACHER:
        lesson = get_object_or_404(
            Lesson,
            id=id,
            instructor=request.user
        )

    else:
        return redirect("student_dashboard")
    return render(request,"lesson_detail.html",{'lesson':lesson})


def lesson_list(request):
    courses = Course.objects.all().order_by("-created_at")
    if request.user.role == "teacher":
        courses = Course.objects.filter(instructor=request.user)
        all_lesson = Lesson.objects.filter(instructor=request.user).order_by('order_number')
    elif request.user.role == "student":
        all_lesson = Lesson.objects.filter(status="published").order_by('order_number')
    else:
        all_lesson = Lesson.objects.all().order_by('order_number')
        
    paginator = Paginator(all_lesson, 5) 
        
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"lesson_list.html",{'page_obj':page_obj,'courses':courses})

def lesson_delete(request, id):

    if request.method != "POST":
        return redirect("lesson_list")

    if request.user.role == request.user.ADMIN:
        lesson = get_object_or_404(Lesson, id=id)

    elif request.user.role == request.user.TEACHER:
        lesson = get_object_or_404(
            Lesson,
            id=id,
            instructor=request.user
        )

    else:
        return redirect("student_dashboard")

    lesson.delete()
    messages.success(request, "Lesson deleted successfully.")

    return redirect("lesson_list")
def lesson_search(request):
    
    query  = request.GET.get("search","")
    course = request.GET.get("course","")
    status = request.GET.get("status","")

    if request.user:
        if request.user.role == request.user.TEACHER:
            courses = Course.objects.filter(instructor=request.user)
            search_lesson = Lesson.objects.filter(instructor=request.user).order_by('order_number')

        elif request.user.role == request.user.ADMIN:
            courses = Course.objects.all()
            search_lesson = Lesson.objects.all()

        else:
            return redirect("student_dashboard")


    
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
    

