from datetime import timedelta

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from categories.models import Category
from courses.models import Course
from lesson.models import Lesson, LessonProgress
from .models import Enrollment
from .services import complete_enrollment_if_finished


COURSE_COMPLETED_MESSAGE = "Congratulations! You have completed this course."


class EnrollmentCompletionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(username="teacher1", email="teacher1@test.com", password="pass12345!", role=User.TEACHER)
        cls.student = User.objects.create_user(username="student1", email="student1@test.com", password="pass12345!", role=User.STUDENT)
        cls.other_student = User.objects.create_user(username="student2", email="student2@test.com", password="pass12345!", role=User.STUDENT)
        cls.category = Category.objects.create(category="Programming", description="Programming courses")
        cls.course = cls.make_course("Python Basics")
        cls.lessons = [cls.make_lesson(cls.course, i) for i in range(1, 6)]

    @classmethod
    def make_course(cls, title):
        return Course.objects.create(
            title=title,
            category=cls.category,
            instructor=cls.teacher,
            short_description="short",
            full_description="full",
            price=100,
            status="published",
        )

    @classmethod
    def make_lesson(cls, course, order_number, status="published"):
        return Lesson.objects.create(
            title=f"{course.title} lesson {order_number}",
            course=course,
            content="content",
            order_number=order_number,
            status=status,
            instructor=cls.teacher,
        )

    def enroll(self, student=None, course=None, status="active"):
        return Enrollment.objects.create(student=student or self.student, course=course or self.course, status=status)

    def record_progress(self, lessons, student=None):
        for lesson in lessons:
            LessonProgress.objects.create(student=student or self.student, lesson=lesson, is_completed=True)

    def complete_via_view(self, lesson):
        return self.client.post(reverse("lesson_complete", args=[lesson.id]))

    def status_of(self, enrollment):
        enrollment.refresh_from_db()
        return enrollment.status

    def messages_for(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    # Cancelled enrollments

    def test_cancelled_enrollment_with_all_lessons_done_stays_cancelled(self):
        enrollment = self.enroll(status="cancelled")
        self.record_progress(self.lessons)
        self.client.force_login(self.student)
        self.client.get(reverse("view_course", args=[self.course.id]))
        self.assertFalse(complete_enrollment_if_finished(enrollment))
        self.assertEqual(self.status_of(enrollment), "cancelled")

    def test_cancelled_enrollment_stays_cancelled_after_last_lesson_is_unpublished(self):
        enrollment = self.enroll(status="cancelled")
        self.record_progress(self.lessons[:4])
        self.lessons[4].status = "draft"
        self.lessons[4].save()
        self.client.force_login(self.student)
        self.client.get(reverse("view_course", args=[self.course.id]))
        self.assertFalse(complete_enrollment_if_finished(enrollment))
        self.assertEqual(self.status_of(enrollment), "cancelled")

    def test_cancelled_enrollment_cannot_complete_another_lesson(self):
        enrollment = self.enroll(status="cancelled")
        self.record_progress(self.lessons[:4])
        self.client.force_login(self.student)
        self.complete_via_view(self.lessons[4])
        self.assertFalse(LessonProgress.objects.filter(student=self.student, lesson=self.lessons[4]).exists())
        self.assertEqual(self.status_of(enrollment), "cancelled")

    # Completion through lesson_complete

    def test_completing_final_lesson_completes_enrollment_immediately(self):
        enrollment = self.enroll()
        self.record_progress(self.lessons[:4])
        self.client.force_login(self.student)
        response = self.complete_via_view(self.lessons[4])
        self.assertRedirects(response, reverse("lesson_detail", args=[self.lessons[4].id]))
        self.assertEqual(self.status_of(enrollment), "completed")
        self.assertIn(COURSE_COMPLETED_MESSAGE, self.messages_for(response))

    def test_completion_updates_updated_at(self):
        enrollment = self.enroll()
        old_timestamp = timezone.now() - timedelta(days=1)
        Enrollment.objects.filter(pk=enrollment.pk).update(updated_at=old_timestamp)
        self.record_progress(self.lessons)
        self.assertTrue(complete_enrollment_if_finished(enrollment))
        enrollment.refresh_from_db()
        self.assertGreater(enrollment.updated_at, old_timestamp)

    def test_partial_progress_keeps_enrollment_active(self):
        enrollment = self.enroll()
        self.client.force_login(self.student)
        for lesson in self.lessons[:3]:
            response = self.complete_via_view(lesson)
            self.assertNotIn(COURSE_COMPLETED_MESSAGE, self.messages_for(response))
        self.assertEqual(LessonProgress.objects.filter(student=self.student).count(), 3)
        self.assertEqual(self.status_of(enrollment), "active")

    def test_empty_course_does_not_auto_complete(self):
        empty_course = self.make_course("Empty Course")
        enrollment = self.enroll(course=empty_course)
        self.assertFalse(complete_enrollment_if_finished(enrollment))
        self.client.force_login(self.student)
        self.client.get(reverse("view_course", args=[empty_course.id]))
        self.assertEqual(self.status_of(enrollment), "active")

    def test_one_students_progress_does_not_affect_another(self):
        enrollment = self.enroll()
        other_enrollment = self.enroll(student=self.other_student)
        self.record_progress(self.lessons[:4])
        self.client.force_login(self.student)
        self.complete_via_view(self.lessons[4])
        self.assertEqual(self.status_of(enrollment), "completed")
        self.assertEqual(self.status_of(other_enrollment), "active")
        self.assertEqual(LessonProgress.objects.filter(student=self.other_student).count(), 0)
        self.assertFalse(complete_enrollment_if_finished(other_enrollment))

    def test_completed_enrollment_can_view_but_not_complete_more_lessons(self):
        enrollment = self.enroll(status="completed")
        self.client.force_login(self.student)
        response = self.client.get(reverse("lesson_detail", args=[self.lessons[0].id]))
        self.assertEqual(response.status_code, 200)
        self.complete_via_view(self.lessons[0])
        self.assertFalse(LessonProgress.objects.filter(student=self.student).exists())
        self.assertEqual(self.status_of(enrollment), "completed")

    # What counts towards completion

    def test_draft_lessons_are_excluded_from_completion(self):
        self.make_lesson(self.course, 6, status="draft")
        enrollment = self.enroll()
        self.record_progress(self.lessons[:4])
        self.client.force_login(self.student)
        self.complete_via_view(self.lessons[4])
        self.assertEqual(self.status_of(enrollment), "completed")

    def test_progress_from_other_courses_is_excluded(self):
        other_course = self.make_course("Java Basics")
        other_lessons = [self.make_lesson(other_course, i) for i in range(1, 6)]
        enrollment = self.enroll()
        self.record_progress(other_lessons)
        self.record_progress(self.lessons[:4])
        self.assertFalse(complete_enrollment_if_finished(enrollment))
        self.assertEqual(self.status_of(enrollment), "active")

    # view_course is read-only

    def test_view_course_get_does_not_change_enrollment_status(self):
        enrollment = self.enroll()
        self.record_progress(self.lessons)
        self.client.force_login(self.student)
        response = self.client.get(reverse("view_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.status_of(enrollment), "active")

    def test_view_course_progress_counts_and_percentage(self):
        self.make_lesson(self.course, 6, status="draft")
        self.enroll()
        self.record_progress(self.lessons[:3])
        self.record_progress(self.lessons, student=self.other_student)
        self.client.force_login(self.student)
        response = self.client.get(reverse("view_course", args=[self.course.id]))
        self.assertEqual(response.context["completed_lessons"], 3)
        self.assertEqual(response.context["total_lessons"], 5)
        self.assertEqual(response.context["progress_percentage"], 60)
        self.assertTrue(response.context["enrolled"])
        self.assertContains(response, "3 of 5 lessons completed")
