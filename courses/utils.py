from .models import Course

def get_courses_by_user(user):
    if user.role == user.ADMIN:
        return Course.objects.all().order_by("-id")
    elif user.role == user.TEACHER:
        return Course.objects.filter(instructor=user).order_by("-id")
    return Course.objects.filter(status="published").order_by("-id")


def can_view_course(user, course):
    # Students keep access to a course that went back to draft after they enrolled.
    if user.role == user.ADMIN or course.status == "published":
        return True
    if user.role == user.TEACHER:
        return course.instructor_id == user.id
    return course.enrollments.filter(student=user, status__in=["active", "completed"]).exists()