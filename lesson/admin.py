from django.contrib import admin
from .models import LessonProgress

# Register your models here.
@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = (
            'student',
            'lesson',
            'is_completed',
            'completed_at',
            'created_at',
            'updated_at',
        )
    search_fields = (
             'student__email',
             'student__username',
             'lesson__title',
             'lesson__course__title'
         )
    list_filter = (
        'is_completed',
        'completed_at',
    )
    ordering = (
        '-created_at',
    )
