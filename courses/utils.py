from .models import Course

def get_courses_by_user(user):
    if user.role == "admin":
        return Course.objects.all().order_by("-id")
    elif user.role == "teacher":
        return Course.objects.filter(instructor=user).order_by("-id")
    return Course.objects.filter(status="published").order_by("-id")