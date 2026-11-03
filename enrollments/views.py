from django.shortcuts import redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from enrollments.models import Enrollment
from courses.models import Course
from django.contrib import messages
from django.utils import timezone


# Create your views here.
@login_required
def student_enrollment(request,id):
    if request.method == "POST":
        if request.user.role == request.user.STUDENT:

            course = get_object_or_404(Course,id=id,status="published")
            enrollment, created = Enrollment.objects.get_or_create(
                course=course,
                student=request.user,
                defaults={"status": "active"},
            )

            if created:
                messages.success(request, "Successfully enrolled in the course.")
            # Conditional UPDATE: only a cancelled enrollment is reactivated.
            elif Enrollment.objects.filter(pk=enrollment.pk, status="cancelled").update(
                status="active", updated_at=timezone.now()
            ):
                messages.success(request, "Your enrollment has been reactivated.")
            else:
                messages.error(request, "You are already enrolled in this course.")
            return redirect('list_course')
                
        else:
            messages.error(request, "User must be a student to enroll the course")
            return redirect('list_course')

    else:
        messages.error(request, "Access denied.")
        return redirect('list_course')
        
