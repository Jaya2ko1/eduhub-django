from django.utils import timezone

from lesson.models import LessonProgress
from .models import Enrollment


def complete_enrollment_if_finished(enrollment):
    """Mark an active enrollment as completed once every published lesson is done."""
    published_lessons = enrollment.course.lessons.filter(status="published")
    total = published_lessons.count()
    if total == 0:
        return False

    completed = LessonProgress.objects.filter(
        student=enrollment.student,
        lesson__in=published_lessons,
        is_completed=True,
    ).count()
    if completed < total:
        return False

    # Conditional UPDATE: only an active enrollment can become completed,
    # so a cancellation saved at the same moment is never overwritten.
    updated = Enrollment.objects.filter(pk=enrollment.pk, status="active").update(
        status="completed",
        updated_at=timezone.now(),
    )
    return updated == 1
