import shutil
import tempfile
from io import BytesIO

from PIL import Image
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from categories.models import Category
from enrollments.models import Enrollment
from .models import Course


class CourseViewPermissionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="admin1", email="admin1@test.com", password="pass12345!", role=User.ADMIN)
        cls.teacher = User.objects.create_user(username="teacher1", email="teacher1@test.com", password="pass12345!", role=User.TEACHER)
        cls.other_teacher = User.objects.create_user(username="teacher2", email="teacher2@test.com", password="pass12345!", role=User.TEACHER)
        cls.student = User.objects.create_user(username="student1", email="student1@test.com", password="pass12345!", role=User.STUDENT)
        cls.category = Category.objects.create(category="Programming", description="Programming courses")
        cls.course = Course.objects.create(
            title="Python Basics",
            category=cls.category,
            instructor=cls.teacher,
            short_description="short",
            full_description="full",
            price=100,
            status="published",
        )

    def course_data(self, **overrides):
        data = {
            "title": "Python Basics Updated",
            "category": self.category.id,
            "instructor": self.teacher.id,
            "short_description": "short",
            "full_description": "full",
            "price": "100.00",
            "status": "published",
        }
        data.update(overrides)
        return data

    # Authentication

    def test_anonymous_user_is_redirected_to_login(self):
        urls = [
            reverse("list_course"),
            reverse("search_course"),
            reverse("create_course"),
            reverse("edit_course", args=[self.course.id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    def test_anonymous_user_cannot_delete_course(self):
        response = self.client.post(reverse("delete_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    # Role restrictions

    def test_student_cannot_open_create_page(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("create_course"))
        self.assertRedirects(response, reverse("list_course"))

    def test_student_cannot_create_course(self):
        self.client.force_login(self.student)
        self.client.post(reverse("create_course"), self.course_data(title="Student Course"))
        self.assertFalse(Course.objects.filter(title="Student Course").exists())

    def test_student_cannot_edit_course(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("edit_course", args=[self.course.id]), self.course_data(title="Hacked"))
        self.assertRedirects(response, reverse("list_course"))
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, "Python Basics")

    def test_student_cannot_delete_course(self):
        self.client.force_login(self.student)
        self.client.post(reverse("delete_course", args=[self.course.id]))
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    # Ownership

    def test_teacher_cannot_edit_another_teachers_course(self):
        self.client.force_login(self.other_teacher)
        response = self.client.post(reverse("edit_course", args=[self.course.id]), self.course_data(title="Hacked"))
        self.assertEqual(response.status_code, 404)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, "Python Basics")

    def test_teacher_cannot_delete_another_teachers_course(self):
        self.client.force_login(self.other_teacher)
        response = self.client.post(reverse("delete_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    def test_teacher_cannot_reassign_own_course_to_another_teacher(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("edit_course", args=[self.course.id]),
            self.course_data(instructor=self.other_teacher.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("instructor", response.context["form"].errors)
        self.course.refresh_from_db()
        self.assertEqual(self.course.instructor, self.teacher)

    def test_teacher_can_edit_own_course(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("edit_course", args=[self.course.id]), self.course_data())
        self.assertRedirects(response, reverse("list_course"))
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, "Python Basics Updated")

    def test_teacher_can_delete_own_course(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("delete_course", args=[self.course.id]))
        self.assertRedirects(response, reverse("list_course"))
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

    def test_admin_can_edit_any_course(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("edit_course", args=[self.course.id]), self.course_data(title="Admin Edit"))
        self.assertRedirects(response, reverse("list_course"))
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, "Admin Edit")

    def test_admin_can_delete_any_course(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("delete_course", args=[self.course.id]))
        self.assertRedirects(response, reverse("list_course"))
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

    # POST-only deletion

    def test_delete_with_get_is_not_allowed(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("delete_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    # Pages still work for allowed users

    def test_logged_in_users_can_list_and_search_courses(self):
        for user in (self.admin, self.teacher, self.student):
            self.client.force_login(user)
            with self.subTest(role=user.role):
                self.assertEqual(self.client.get(reverse("list_course")).status_code, 200)
                self.assertEqual(self.client.get(reverse("search_course")).status_code, 200)

    def test_teacher_can_open_create_page(self):
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse("create_course")).status_code, 200)

    def test_course_list_renders_delete_as_post_form(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("list_course"))
        delete_url = reverse("delete_course", args=[self.course.id])
        self.assertContains(response, f'action="{delete_url}"')
        self.assertNotContains(response, f'href="{delete_url}"')

    # Additional cases from the Step 1 review

    def test_teacher_cannot_open_edit_page_of_another_teachers_course(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse("edit_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 404)

    def test_student_cannot_open_edit_page(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("edit_course", args=[self.course.id]))
        self.assertRedirects(response, reverse("list_course"))

    def test_delete_nonexistent_course_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("delete_course", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_get_delete_redirects_to_login(self):
        response = self.client.get(reverse("delete_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    def test_teachers_only_see_their_own_courses_in_list_and_search(self):
        other_course = Course.objects.create(
            title="Java Basics",
            category=self.category,
            instructor=self.other_teacher,
            short_description="short",
            full_description="full",
            price=50,
            status="published",
        )
        self.client.force_login(self.teacher)
        listed = list(self.client.get(reverse("list_course")).context["page_obj"])
        searched = list(self.client.get(reverse("search_course")).context["courses"])
        self.assertEqual(listed, [self.course])
        self.assertEqual(searched, [self.course])

        self.client.force_login(self.admin)
        listed = list(self.client.get(reverse("list_course")).context["page_obj"])
        self.assertCountEqual(listed, [self.course, other_course])

    def test_course_search_renders_delete_as_post_form(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("search_course"))
        delete_url = reverse("delete_course", args=[self.course.id])
        self.assertContains(response, f'action="{delete_url}"')
        self.assertNotContains(response, f'href="{delete_url}"')

    def test_denied_actions_show_error_messages(self):
        self.client.force_login(self.student)
        cases = [
            ("get", reverse("create_course"), "Only teachers and admins can create courses."),
            ("get", reverse("edit_course", args=[self.course.id]), "Only teachers and admins can edit courses."),
            ("post", reverse("delete_course", args=[self.course.id]), "Only teachers and admins can delete courses."),
        ]
        for method, url, expected in cases:
            with self.subTest(url=url):
                response = getattr(self.client, method)(url)
                self.assertIn(expected, [str(m) for m in get_messages(response.wsgi_request)])


MEDIA_ROOT_FOR_TESTS = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT_FOR_TESTS)
class CourseCreateTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="admin1", email="admin1@test.com", password="pass12345!", role=User.ADMIN)
        cls.teacher = User.objects.create_user(username="teacher1", email="teacher1@test.com", password="pass12345!", role=User.TEACHER)
        cls.other_teacher = User.objects.create_user(username="teacher2", email="teacher2@test.com", password="pass12345!", role=User.TEACHER)
        cls.category = Category.objects.create(category="Programming", description="Programming courses")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT_FOR_TESTS, ignore_errors=True)

    def course_data(self, **overrides):
        image = BytesIO()
        Image.new("RGB", (1, 1)).save(image, "PNG")
        data = {
            "title": "New Course",
            "category": self.category.id,
            "short_description": "short",
            "full_description": "full",
            "price": "10.00",
            "status": "draft",
            "thumbnail": SimpleUploadedFile("thumb.png", image.getvalue(), content_type="image/png"),
        }
        data.update(overrides)
        return data

    def test_teacher_creates_course_for_themself(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("create_course"), self.course_data(instructor=self.teacher.id))
        self.assertRedirects(response, reverse("list_course"))
        self.assertEqual(Course.objects.get(title="New Course").instructor, self.teacher)

    def test_teacher_cannot_create_course_for_another_teacher(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("create_course"), self.course_data(instructor=self.other_teacher.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn("instructor", response.context["form"].errors)
        self.assertFalse(Course.objects.filter(title="New Course").exists())

    def test_admin_creates_course_for_selected_teacher(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("create_course"), self.course_data(instructor=self.other_teacher.id))
        self.assertRedirects(response, reverse("list_course"))
        self.assertEqual(Course.objects.get(title="New Course").instructor, self.other_teacher)


class CourseVisibilityTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="admin1", email="admin1@test.com", password="pass12345!", role=User.ADMIN)
        cls.teacher = User.objects.create_user(username="teacher1", email="teacher1@test.com", password="pass12345!", role=User.TEACHER)
        cls.other_teacher = User.objects.create_user(username="teacher2", email="teacher2@test.com", password="pass12345!", role=User.TEACHER)
        cls.student = User.objects.create_user(username="student1", email="student1@test.com", password="pass12345!", role=User.STUDENT)
        cls.category = Category.objects.create(category="Programming", description="Programming courses")
        cls.published = cls.make_course("Published Course", "published")
        cls.draft = cls.make_course("Draft Course", "draft")

    @classmethod
    def make_course(cls, title, status):
        return Course.objects.create(
            title=title,
            category=cls.category,
            instructor=cls.teacher,
            short_description="short",
            full_description="full",
            price=100,
            status=status,
        )

    def view_status(self, user, course_id):
        self.client.force_login(user)
        return self.client.get(reverse("view_course", args=[course_id])).status_code

    def test_student_can_view_published_course(self):
        self.assertEqual(self.view_status(self.student, self.published.id), 200)

    def test_student_cannot_view_draft_course(self):
        self.assertEqual(self.view_status(self.student, self.draft.id), 404)

    def test_enrolled_student_can_view_course_that_became_draft(self):
        for status in ("active", "completed"):
            with self.subTest(enrollment=status):
                Enrollment.objects.update_or_create(student=self.student, course=self.draft, defaults={"status": status})
                self.assertEqual(self.view_status(self.student, self.draft.id), 200)

    def test_cancelled_student_cannot_view_draft_course(self):
        Enrollment.objects.create(student=self.student, course=self.draft, status="cancelled")
        self.assertEqual(self.view_status(self.student, self.draft.id), 404)

    def test_teacher_can_view_own_draft_and_published_courses(self):
        self.assertEqual(self.view_status(self.teacher, self.draft.id), 200)
        self.assertEqual(self.view_status(self.other_teacher, self.published.id), 200)

    def test_teacher_cannot_view_another_teachers_draft(self):
        self.assertEqual(self.view_status(self.other_teacher, self.draft.id), 404)

    def test_admin_can_view_all_courses(self):
        self.assertEqual(self.view_status(self.admin, self.draft.id), 200)
        self.assertEqual(self.view_status(self.admin, self.published.id), 200)

    def test_missing_course_returns_404(self):
        self.assertEqual(self.view_status(self.admin, 99999), 404)


class CourseSearchInputValidationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="admin1", email="admin1@test.com", password="pass12345!", role=User.ADMIN)
        cls.teacher = User.objects.create_user(username="teacher1", email="teacher1@test.com", password="pass12345!", role=User.TEACHER)
        cls.category = Category.objects.create(category="Programming", description="Programming courses")
        for title, status in (("Published Course", "published"), ("Draft Course", "draft")):
            Course.objects.create(
                title=title,
                category=cls.category,
                instructor=cls.teacher,
                short_description="short",
                full_description="full",
                price=100,
                status=status,
            )

    def test_non_numeric_category_is_ignored(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("search_course"), {"category": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 2)

    def test_valid_category_filter_still_works(self):
        other_category = Category.objects.create(category="Design", description="Design courses")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("search_course"), {"category": other_category.id})
        self.assertEqual(list(response.context["courses"]), [])
