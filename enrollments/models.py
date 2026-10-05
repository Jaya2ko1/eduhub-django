from django.db import models
from accounts.models import User
from courses.models import Course

# Create your models here.
class Enrollment(models.Model):
    ENROLLED_STATUS = [
        ('active' , 'ACTIVE'),
        ('cancelled' , 'CANCELLED'),
        ('completed' , 'COMPLETED'),
    ]
    student = models.ForeignKey(User,on_delete=models.PROTECT,related_name="enrollments",limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course,on_delete=models.CASCADE,related_name="enrollments")
    status = models.CharField(max_length=50,choices=ENROLLED_STATUS,default='active')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-enrolled_at']
        constraints = [
                    models.UniqueConstraint(
                        fields=['course', 'student'],
                        name='unique_student_enrollment_per_course'
                    )
                ]
        verbose_name = "enrollment"
        verbose_name_plural = "enrollments"

    def __str__(self):
        return f"{self.student.email} - {self.course.title}"
    