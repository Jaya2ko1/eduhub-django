from django.shortcuts import redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from enrollments.models import Enrollment
from courses.models import Course
from django.contrib import messages


# Create your views here.
@login_required
def student_enrollment(request,id):
    if request.method == "POST":
        if request.user.role == request.user.STUDENT:

            course = get_object_or_404(Course,id=id,status="published")
            enroll = Enrollment.objects.filter(course=course,student=request.user).exists()
    
            if enroll:
                messages.error(request, "You are already enrolled in this course.")
                return redirect('list_course')
                
            else:
                enrollment = Enrollment.objects.create(
                student=request.user,   
                course=course,
                status="active"
                )
                messages.success(request, "Successfully enrolled in the course.")
                return redirect('list_course')
                
        else:
            messages.error(request, "User must be a student to enroll the course")
            return redirect('list_course')

    else:
        messages.error(request, "Access denied.")
        return redirect('list_course')
        
