from django.shortcuts import render,get_object_or_404,redirect
from .forms import LessonForm
from .models import Lesson,Course
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from courses.utils import get_courses_by_user
from enrollments.models import Enrollment




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
            return redirect('lesson_list',lesson.course_id)
    else:
        form = LessonForm(user=request.user)
    return render(request,"lesson_create.html",{'form':form})

def lesson_edit(request,id):
    get_course_id = get_object_or_404(Lesson,id=id)
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
            return redirect('lesson_list',get_course_id.course.id)
    else:
        form=LessonForm(instance=lesson,user=request.user)
    return render(request,'lesson_update.html',{'form':form})

@login_required
def lesson_detail(request,id):
    lesson = get_object_or_404(Lesson,id=id)
    if request.user.role == request.user.ADMIN:

        lesson = get_object_or_404(
            Lesson,
            id=id
        )

    elif request.user.role == request.user.TEACHER:

        lesson = get_object_or_404(
            Lesson,
            id=id,
            instructor=request.user
        )

    elif request.user.role == request.user.STUDENT:

        is_enrolled = Enrollment.objects.filter(
            course=lesson.course,
            student=request.user,
            status="active"
        ).exists()

        if not is_enrolled:
            messages.error(
            request,
                "You are unable to access this course. Please enroll first."
            )
            return redirect("lesson_list",lesson.course.id)

        lesson = get_object_or_404(
            Lesson,
            id=id,
            status="published"
        )
    return render(
        request,
        "lesson_detail.html",
        {
            "lesson": lesson
        }
    )


def lesson_list(request,course_id):
    if request.user.role == "teacher":
        all_lesson = Lesson.objects.filter(instructor=request.user,course=course_id).order_by('order_number')
    elif request.user.role == "student":
        all_lesson = Lesson.objects.filter(status="published",course=course_id).order_by('order_number')
    else:
        all_lesson = Lesson.objects.filter(course=course_id).order_by('order_number')
        
    paginator = Paginator(all_lesson, 5) 
        
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"lesson_list.html",{'page_obj':page_obj})

def lesson_delete(request,id):
   
    get_course_id = get_object_or_404(Lesson,id=id)    
    if request.method != "POST":
        return redirect("lesson_list",get_course_id.course.id)

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

    return redirect("lesson_list",get_course_id.course.id)

def lesson_search(request):

    query = request.GET.get("search", "")
    course = request.GET.get("course", "")
    status = request.GET.get("status", "")

    # --------------------------------
    # Base queryset based on role
    # --------------------------------

    if request.user.role == request.user.ADMIN:

        courses = Course.objects.all().order_by("-created_at")

        search_lesson = Lesson.objects.all()

    elif request.user.role == request.user.TEACHER:

        courses = Course.objects.filter(
            instructor=request.user
        ).order_by("-created_at")

        search_lesson = Lesson.objects.filter(
            instructor=request.user
        )

    elif request.user.role == request.user.STUDENT:

        courses = Course.objects.all().order_by("-created_at")

        search_lesson = Lesson.objects.filter(
            status="published"
        )

    else:
        return redirect("login")

    # --------------------------------
    # Search
    # --------------------------------

    if query:
        search_lesson = search_lesson.filter(
            Q(title__icontains=query) |
            Q(course__title__icontains=query)
        )

    # --------------------------------
    # Course filter
    # --------------------------------

    if course:
        search_lesson = search_lesson.filter(
            course_id=course
        )

    # --------------------------------
    # Status filter
    # --------------------------------

    # Students must NEVER be able to
    # change this and see drafts.
    if request.user.role != request.user.STUDENT:

        if status:
            search_lesson = search_lesson.filter(
                status=status
            )

    # --------------------------------
    # Ordering
    # --------------------------------

    search_lesson = search_lesson.order_by(
        "order_number"
    )

    # --------------------------------
    # Pagination
    # --------------------------------

    paginator = Paginator(
        search_lesson,
        5
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(
        page_number
    )

    # --------------------------------
    # Response
    # --------------------------------

    return render(
        request,
        "lesson_search.html",
        {
            "page_obj": page_obj,
            "courses": courses,
            "course": course,
            "query": query,
            "status": status,
        }
    )