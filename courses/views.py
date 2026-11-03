from django.shortcuts import render,redirect,get_object_or_404
from django.http import Http404

from .models import Category
from .forms import CourseForm
from .models import Course
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .utils import get_courses_by_user, can_view_course
from enrollments.models import Enrollment
from django.db.models import OuterRef, Subquery
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST




def can_manage_courses(user):
    return user.role in (user.ADMIN, user.TEACHER)


def get_manageable_course(user, id):
    # Teachers can only manage their own courses; admins can manage any course.
    if user.role == user.TEACHER:
        return get_object_or_404(Course, id=id, instructor=user)
    return get_object_or_404(Course, id=id)


# Create your views here.

@login_required
def create_course(request):
    if not can_manage_courses(request.user):
        messages.error(request, "Only teachers and admins can create courses.")
        return redirect('list_course')
    if request.method == "POST":
        form = CourseForm(request.POST,request.FILES,user=request.user)
        if form.is_valid():
            form.save()
            return redirect('list_course')
    else:
        form = CourseForm(user=request.user)
    return render(request,"courses/course_create.html",{'form':form})

@login_required
def edit_course(request,id):
    if not can_manage_courses(request.user):
        messages.error(request, "Only teachers and admins can edit courses.")
        return redirect('list_course')
    get_course = get_manageable_course(request.user, id)
    if request.method == "POST":
        form = CourseForm(request.POST,request.FILES,instance=get_course,user=request.user)
        if form.is_valid():
            form.save()
            return redirect('list_course')
    else:
        form=CourseForm(instance=get_course,user=request.user)
    return render(request,"courses/course_update.html",{'form':form})


@login_required
def view_course(request, id):
    course = get_object_or_404(Course, id=id)
    if not can_view_course(request.user, course):
        raise Http404

    enrollment = course.enrollments.filter(
        student=request.user
    ).first()

    enrollment_status = enrollment.status if enrollment else None
    enrolled = enrollment_status in ("active", "completed")
    
    completed_lessons = course.lessons.filter(
        lesson_progress__is_completed=True,
        status="published",
        lesson_progress__student=request.user
    ).values("id").distinct().count()

    total_lessons = course.lessons.filter(
        status="published"
    ).count()

    progress_percentage = (
        round(completed_lessons / total_lessons * 100)
        if total_lessons > 0 else 0
    )

    form = CourseForm(instance=course)

    return render(request, "courses/course_view.html", {
        "form": form,
        "course": course,
        "enrolled": enrolled,
        "enrollment_status": enrollment_status,
        "progress_percentage": progress_percentage,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
    })

@login_required
def list_course(request):
    # Each course carries the current user's own enrollment status (or None).
    my_enrollment = Enrollment.objects.filter(course=OuterRef("pk"), student=request.user)
    get_course = get_courses_by_user(request.user).select_related("category", "instructor").annotate(
        my_enrollment_status=Subquery(my_enrollment.values("status")[:1])
    )

    paginator = Paginator(get_course, 5)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"courses/course_list.html",{'page_obj':page_obj})

@login_required
@require_POST
def delete_course(request,id):
    if not can_manage_courses(request.user):
        messages.error(request, "Only teachers and admins can delete courses.")
        return redirect('list_course')
    get_course = get_manageable_course(request.user, id)
    get_course.delete() 
    messages.success(request, "Course deleted successfully.") 
    return redirect('list_course') 



@login_required
def search_course(request):
    categories = Category.objects.all()
    courses = get_courses_by_user(request.user).select_related("category", "instructor")

    query = request.GET.get("search")
    category = request.GET.get("category")
    status = request.GET.get("status")

    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(price__icontains=query)
        )

    # Ignore non-numeric ids instead of crashing with a 500.
    if category and category.isdigit():
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
   



       