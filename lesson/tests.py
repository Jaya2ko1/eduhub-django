from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from categories.models import Category
from courses.models import Course
from enrollments.models import Enrollment
from .forms import LessonForm
from .models import Lesson, LessonProgress


class LessonTestData(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="admin1", email="admin1@test.com", password="pass12345!", role=User.ADMIN)
        cls.teacher = User.objects.create_user(username="teacher1", email="teacher1@test.com", password="pass12345!", role=User.TEACHER)
        cls.other_teacher = User.objects.create_user(username="teacher2", email="teacher2@test.com", password="pass12345!", role=User.TEACHER)
        cls.student = User.objects.create_user(username="student1", email="student1@test.com", password="pass12345!", role=User.STUDENT)
        cls.category = Category.objects.create(category="Programming", description="Programming courses")
        cls.course = cls.make_course("Python Basics", cls.teacher)
        cls.other_course = cls.make_course("Java Basics", cls.other_teacher)
        cls.lesson = Lesson.objects.create(
            title="Intro",
            course=cls.course,
            content="content",
            order_number=1,
            status="published",
            instructor=cls.teacher,
        )

    @classmethod
    def make_course(cls, title, instructor):
        return Course.objects.create(
            title=title,
            category=cls.category,
            instructor=instructor,
            short_description="short",
            full_description="full",
            price=100,
            status="published",
        )

    def lesson_data(self, course, **overrides):
        data = {
            "course": course.id,
            "title": "New Lesson",
            "lesson_type": "reading",
            "content": "Lesson content",
            "video_url": "",
            "order_number": 2,
            "status": "published",
        }
        data.update(overrides)
        return data


class LessonCreateTests(LessonTestData):

    # Anonymous and student access

    def test_anonymous_user_cannot_create_lesson(self):
        for method in ("get", "post"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse("lesson_create"), self.lesson_data(self.course))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)
        self.assertFalse(Lesson.objects.filter(title="New Lesson").exists())

    def test_student_cannot_open_create_page(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("lesson_create"))
        self.assertRedirects(response, reverse("student_dashboard"))

    def test_student_cannot_create_lesson(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("lesson_create"), self.lesson_data(self.course))
        self.assertRedirects(response, reverse("student_dashboard"))
        self.assertFalse(Lesson.objects.filter(title="New Lesson").exists())

    # Teacher

    def test_teacher_can_open_create_page(self):
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse("lesson_create")).status_code, 200)

    def test_teacher_creates_lesson_in_own_course(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("lesson_create"), self.lesson_data(self.course))
        self.assertRedirects(response, reverse("lesson_list", args=[self.course.id]))
        lesson = Lesson.objects.get(title="New Lesson")
        self.assertEqual(lesson.course, self.course)
        self.assertEqual(lesson.instructor, self.teacher)

    def test_teacher_cannot_create_lesson_in_another_teachers_course(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("lesson_create"), self.lesson_data(self.other_course))
        self.assertEqual(response.status_code, 200)
        self.assertIn("course", response.context["form"].errors)
        self.assertFalse(Lesson.objects.filter(title="New Lesson").exists())

    # Admin

    def test_admin_creates_lesson_in_any_teachers_course(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("lesson_create"), self.lesson_data(self.other_course, order_number=1))
        self.assertRedirects(response, reverse("lesson_list", args=[self.other_course.id]))
        lesson = Lesson.objects.get(title="New Lesson")
        self.assertEqual(lesson.course, self.other_course)
        self.assertEqual(lesson.instructor, self.other_teacher)

    def test_course_teacher_can_edit_lesson_created_by_admin(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("lesson_create"), self.lesson_data(self.course))
        lesson = Lesson.objects.get(title="New Lesson")
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse("lesson_edit", args=[lesson.id])).status_code, 200)

    # Invalid input

    def test_invalid_course_ids_are_rejected(self):
        self.client.force_login(self.admin)
        for course_id in ("99999", "abc", ""):
            with self.subTest(course_id=course_id):
                data = self.lesson_data(self.course)
                data["course"] = course_id
                response = self.client.post(reverse("lesson_create"), data)
                self.assertEqual(response.status_code, 200)
                self.assertIn("course", response.context["form"].errors)
        self.assertFalse(Lesson.objects.filter(title="New Lesson").exists())

    def test_duplicate_order_number_in_course_is_rejected(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("lesson_create"), self.lesson_data(self.course, order_number=1))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Lesson.objects.filter(course=self.course).count(), 1)


class LessonFormCourseChoicesTests(LessonTestData):

    def test_teacher_sees_only_own_courses(self):
        form = LessonForm(user=self.teacher)
        self.assertEqual(list(form.fields["course"].queryset), [self.course])

    def test_admin_sees_all_courses(self):
        form = LessonForm(user=self.admin)
        self.assertCountEqual(form.fields["course"].queryset, [self.course, self.other_course])

    def test_student_sees_no_courses(self):
        form = LessonForm(user=self.student)
        self.assertEqual(list(form.fields["course"].queryset), [])

    def test_create_page_lists_only_teachers_courses(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("lesson_create"))
        self.assertContains(response, "Python Basics")
        self.assertNotContains(response, "Java Basics")


class ExistingLessonFunctionalityTests(LessonTestData):

    def test_owner_can_edit_lesson(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("lesson_edit", args=[self.lesson.id]),
            self.lesson_data(self.course, title="Intro Updated", order_number=1),
        )
        self.assertRedirects(response, reverse("lesson_list", args=[self.course.id]))
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "Intro Updated")

    def test_other_teacher_cannot_edit_lesson(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse("lesson_edit", args=[self.lesson.id]))
        self.assertEqual(response.status_code, 404)

    def test_student_cannot_edit_lesson(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("lesson_edit", args=[self.lesson.id]))
        self.assertRedirects(response, reverse("student_dashboard"))

    def test_owner_and_enrolled_student_can_view_lesson_detail(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        for user in (self.teacher, self.admin, self.student):
            self.client.force_login(user)
            with self.subTest(role=user.role):
                response = self.client.get(reverse("lesson_detail", args=[self.lesson.id]))
                self.assertEqual(response.status_code, 200)

    def test_unenrolled_student_cannot_view_lesson_detail(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("lesson_detail", args=[self.lesson.id]))
        self.assertRedirects(response, reverse("lesson_list", args=[self.course.id]))

    def test_owner_can_delete_lesson_with_post(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("lesson_delete", args=[self.lesson.id]))
        self.assertRedirects(response, reverse("lesson_list", args=[self.course.id]))
        self.assertFalse(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_delete_with_get_does_not_delete(self):
        self.client.force_login(self.teacher)
        self.client.get(reverse("lesson_delete", args=[self.lesson.id]))
        self.assertTrue(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_other_teacher_cannot_delete_lesson(self):
        self.client.force_login(self.other_teacher)
        response = self.client.post(reverse("lesson_delete", args=[self.lesson.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_enrolled_student_can_complete_lesson(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.force_login(self.student)
        response = self.client.post(reverse("lesson_complete", args=[self.lesson.id]))
        self.assertRedirects(response, reverse("lesson_detail", args=[self.lesson.id]))
        self.assertTrue(LessonProgress.objects.filter(student=self.student, lesson=self.lesson, is_completed=True).exists())

    def test_unenrolled_student_cannot_complete_lesson(self):
        self.client.force_login(self.student)
        self.client.post(reverse("lesson_complete", args=[self.lesson.id]))
        self.assertFalse(LessonProgress.objects.filter(student=self.student).exists())

    def test_list_and_search_work_for_all_roles(self):
        for user in (self.admin, self.teacher, self.student):
            self.client.force_login(user)
            with self.subTest(role=user.role):
                self.assertEqual(self.client.get(reverse("lesson_list", args=[self.course.id])).status_code, 200)
                self.assertEqual(self.client.get(reverse("lesson_search")).status_code, 200)


class LessonVisibilityTests(LessonTestData):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.draft_course = Course.objects.create(
            title="Secret Draft Course",
            category=cls.category,
            instructor=cls.other_teacher,
            short_description="short",
            full_description="full",
            price=100,
            status="draft",
        )
        cls.draft_course_lesson = Lesson.objects.create(
            title="Hidden Draft Lesson",
            course=cls.draft_course,
            content="content",
            order_number=1,
            status="published",
            instructor=cls.other_teacher,
        )

    def list_status(self, user, course_id):
        self.client.force_login(user)
        return self.client.get(reverse("lesson_list", args=[course_id])).status_code

    def test_student_cannot_list_lessons_of_draft_course(self):
        self.assertEqual(self.list_status(self.student, self.draft_course.id), 404)

    def test_enrolled_student_can_list_lessons_of_course_that_became_draft(self):
        Enrollment.objects.create(student=self.student, course=self.draft_course, status="active")
        self.client.force_login(self.student)
        response = self.client.get(reverse("lesson_list", args=[self.draft_course.id]))
        self.assertContains(response, "Hidden Draft Lesson")

    def test_teacher_cannot_list_lessons_of_another_teachers_draft(self):
        self.assertEqual(self.list_status(self.teacher, self.draft_course.id), 404)
        self.assertEqual(self.list_status(self.other_teacher, self.draft_course.id), 200)

    def test_admin_can_list_lessons_of_any_course(self):
        self.assertEqual(self.list_status(self.admin, self.draft_course.id), 200)

    def test_missing_course_returns_404_in_lesson_list(self):
        self.assertEqual(self.list_status(self.admin, 99999), 404)

    def test_student_search_hides_draft_courses_and_their_lessons(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("lesson_search"))
        self.assertNotContains(response, "Secret Draft Course")
        self.assertNotContains(response, "Hidden Draft Lesson")
        self.assertContains(response, "Python Basics")

        response = self.client.get(reverse("lesson_search"), {"course": self.draft_course.id})
        self.assertNotContains(response, "Hidden Draft Lesson")

    def test_owner_teacher_search_still_shows_own_draft_course(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse("lesson_search"))
        self.assertContains(response, "Hidden Draft Lesson")


class LessonOwnershipByCourseTests(LessonTestData):
    """A lesson belongs to its course's teacher, even if its instructor field says otherwise."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.legacy_lesson = Lesson.objects.create(
            title="Legacy Admin Lesson",
            course=cls.course,
            content="content",
            order_number=5,
            status="published",
            instructor=cls.admin,
        )

    def test_course_teacher_can_edit_view_and_list_legacy_lesson(self):
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse("lesson_edit", args=[self.legacy_lesson.id])).status_code, 200)
        self.assertEqual(self.client.get(reverse("lesson_detail", args=[self.legacy_lesson.id])).status_code, 200)
        self.assertContains(self.client.get(reverse("lesson_list", args=[self.course.id])), "Legacy Admin Lesson")
        self.assertContains(self.client.get(reverse("lesson_search")), "Legacy Admin Lesson")

    def test_course_teacher_can_delete_legacy_lesson(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("lesson_delete", args=[self.legacy_lesson.id]))
        self.assertRedirects(response, reverse("lesson_list", args=[self.course.id]))
        self.assertFalse(Lesson.objects.filter(id=self.legacy_lesson.id).exists())

    def test_other_teacher_still_cannot_manage_lesson(self):
        self.client.force_login(self.other_teacher)
        self.assertEqual(self.client.get(reverse("lesson_edit", args=[self.legacy_lesson.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse("lesson_detail", args=[self.legacy_lesson.id])).status_code, 404)
        self.assertEqual(self.client.post(reverse("lesson_delete", args=[self.legacy_lesson.id])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("lesson_search")), "Legacy Admin Lesson")

    def test_lesson_whose_instructor_is_teacher_but_course_is_not_is_not_theirs(self):
        stray = Lesson.objects.create(
            title="Stray Lesson",
            course=self.other_course,
            content="content",
            order_number=7,
            status="published",
            instructor=self.teacher,
        )
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse("lesson_edit", args=[stray.id])).status_code, 404)


class LessonSearchInputValidationTests(LessonTestData):

    def test_non_numeric_course_is_ignored(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("lesson_search"), {"course": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Intro")

    def test_valid_course_filter_still_works(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("lesson_search"), {"course": self.other_course.id})
        self.assertNotContains(response, "Intro")
