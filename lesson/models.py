from django.db import models
from courses.models import Course,User

# Create your models here.
class Lesson(models.Model):
    LESSON_CHOICE = [
        ('video','VIDEO'),
        ('reading','READING',),
        ('pdf','PDF')
    ]
    STATUS_CHOICE = [
        ('draft','DRAFT'),
        ('published','PUBLISHED')

    ]
    title = models.CharField(max_length=150)
    course = models.ForeignKey(Course,on_delete=models.CASCADE,related_name="lessons")
    lesson_type = models.CharField(max_length=100,choices=LESSON_CHOICE,default='pdf')
    content = models.TextField(max_length=5000)
    video_url = models.URLField(max_length=500, blank=True, null=True)
    pdf_file = models.FileField(upload_to="lesson_pdf/",blank=True,null=True)
    order_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20,choices=STATUS_CHOICE,default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    instructor = models.ForeignKey(User,on_delete=models.PROTECT,related_name="lessons",limit_choices_to={"role": User.TEACHER},null=True,blank=True)


    class Meta:
        ordering = ['order_number']
        constraints = [
            models.UniqueConstraint(
                fields=['course', 'order_number'],
                name='unique_lesson_order_per_course'
            )
        ]
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"

    def __str__(self):
        return self.title 

class LessonProgress(models.Model):
    student = models.ForeignKey(User,on_delete=models.PROTECT,related_name="lesson_progress",limit_choices_to={"role": User.STUDENT})
    lesson = models.ForeignKey(Lesson,on_delete=models.CASCADE,related_name="lesson_progress")
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
            ordering = ['-created_at']
            constraints = [
                models.UniqueConstraint(
                    fields=['student', 'lesson'],
                    name='unique_lesson_per_student'
                )
            ]
            verbose_name = "LessonProgress"
            verbose_name_plural = "LessonsProgress"
    
    def __str__(self):
        return f"{self.student.email} - {self.lesson}" 

    
