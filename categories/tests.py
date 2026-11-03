from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Course
from lesson.models import Lesson
from .models import Category


class CategoryViewPermissionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="admin1", email="admin1@test.com", password="pass12345!", role=User.ADMIN)
        cls.teacher = User.objects.create_user(username="teacher1", email="teacher1@test.com", password="pass12345!", role=User.TEACHER)
        cls.student = User.objects.create_user(username="student1", email="student1@test.com", password="pass12345!", role=User.STUDENT)
        cls.category = Category.objects.create(category="Programming", description="Programming courses")

    def category_data(self, **overrides):
        data = {
            "category": "Design",
            "description": "Design courses",
            "status": "on",
        }
        data.update(overrides)
        return data

    def messages_for(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    # Authentication

    def test_anonymous_user_is_redirected_to_login(self):
        urls = [
            reverse("list_category"),
            reverse("search"),
            reverse("create_category"),
            reverse("edit_category", args=[self.category.id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    def test_anonymous_user_cannot_delete_category(self):
        for method in ("get", "post"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse("delete_category", args=[self.category.id]))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)
                self.assertTrue(Category.objects.filter(id=self.category.id).exists())

    # Student restrictions

    def test_student_cannot_open_create_page(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("create_category"))
        self.assertRedirects(response, reverse("list_category"))
        self.assertIn("Only teachers and admins can create categories.", self.messages_for(response))

    def test_student_cannot_create_category(self):
        self.client.force_login(self.student)
        self.client.post(reverse("create_category"), self.category_data())
        self.assertFalse(Category.objects.filter(category="Design").exists())

    def test_student_cannot_open_edit_page(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("edit_category", args=[self.category.id]))
        self.assertRedirects(response, reverse("list_category"))
        self.assertIn("Only teachers and admins can edit categories.", self.messages_for(response))

    def test_student_cannot_edit_category(self):
        self.client.force_login(self.student)
        self.client.post(reverse("edit_category", args=[self.category.id]), self.category_data(category="Hacked"))
        self.category.refresh_from_db()
        self.assertEqual(self.category.category, "Programming")

    def test_student_cannot_delete_category(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("delete_category", args=[self.category.id]))
        self.assertRedirects(response, reverse("list_category"))
        self.assertIn("Only admins can delete categories.", self.messages_for(response))
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())

    # Teacher permissions

    def test_teacher_can_create_category(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("create_category"), self.category_data())
        self.assertRedirects(response, reverse("list_category"))
        self.assertTrue(Category.objects.filter(category="Design").exists())

    def test_teacher_can_edit_category(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("edit_category", args=[self.category.id]),
            self.category_data(category="Programming Updated"),
        )
        self.assertRedirects(response, reverse("list_category"))
        self.category.refresh_from_db()
        self.assertEqual(self.category.category, "Programming Updated")

    def test_teacher_cannot_delete_category(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("delete_category", args=[self.category.id]))
        self.assertRedirects(response, reverse("list_category"))
        self.assertIn("Only admins can delete categories.", self.messages_for(response))
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())

    # Admin permissions

    def test_admin_can_create_category(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("create_category"), self.category_data())
        self.assertRedirects(response, reverse("list_category"))
        self.assertTrue(Category.objects.filter(category="Design").exists())

    def test_admin_can_edit_category(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("edit_category", args=[self.category.id]),
            self.category_data(category="Admin Edit"),
        )
        self.assertRedirects(response, reverse("list_category"))
        self.category.refresh_from_db()
        self.assertEqual(self.category.category, "Admin Edit")

    def test_admin_can_delete_empty_category(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("delete_category", args=[self.category.id]))
        self.assertRedirects(response, reverse("list_category"))
        self.assertIn("Category deleted successfully.", self.messages_for(response))
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())

    # POST-only deletion

    def test_delete_with_get_is_not_allowed(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("delete_category", args=[self.category.id]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())

    # Missing ids

    def test_edit_missing_category_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("edit_category", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_missing_category_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("delete_category", args=[99999]))
        self.assertEqual(response.status_code, 404)

    # Cascade guard

    def test_admin_cannot_delete_category_with_courses(self):
        course = Course.objects.create(
            title="Python Basics",
            category=self.category,
            instructor=self.teacher,
            short_description="short",
            full_description="full",
            price=100,
            status="published",
        )
        Lesson.objects.create(title="Intro", course=course, content="content", order_number=1, instructor=self.teacher)
        self.client.force_login(self.admin)
        response = self.client.post(reverse("delete_category", args=[self.category.id]))
        self.assertRedirects(response, reverse("list_category"))
        self.assertIn(
            "Cannot delete a category that still has courses. Move or delete its courses first.",
            self.messages_for(response),
        )
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())
        self.assertTrue(Course.objects.filter(id=course.id).exists())
        self.assertEqual(Lesson.objects.filter(course=course).count(), 1)

    # Listing, search and pagination still work

    def test_all_roles_can_list_and_search_categories(self):
        for user in (self.admin, self.teacher, self.student):
            self.client.force_login(user)
            with self.subTest(role=user.role):
                self.assertEqual(self.client.get(reverse("list_category")).status_code, 200)
                self.assertEqual(self.client.get(reverse("search")).status_code, 200)

    def test_list_is_paginated_by_five(self):
        for i in range(6):
            Category.objects.create(category=f"Category {i}", description="d")
        self.client.force_login(self.student)
        first_page = self.client.get(reverse("list_category"))
        second_page = self.client.get(reverse("list_category"), {"page": 2})
        self.assertEqual(len(first_page.context["page_obj"]), 5)
        self.assertEqual(len(second_page.context["page_obj"]), 2)

    def test_search_filters_by_text_and_category(self):
        design = Category.objects.create(category="Design", description="UI and UX")
        self.client.force_login(self.student)
        by_text = self.client.get(reverse("search"), {"search": "UX"})
        by_id = self.client.get(reverse("search"), {"category": self.category.id})
        self.assertEqual(list(by_text.context["page_obj"]), [design])
        self.assertEqual(list(by_id.context["page_obj"]), [self.category])

    # Templates

    def test_admin_sees_delete_as_post_form(self):
        self.client.force_login(self.admin)
        delete_url = reverse("delete_category", args=[self.category.id])
        for url in (reverse("list_category"), reverse("search")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, f'action="{delete_url}"')
                self.assertNotContains(response, f'href="{delete_url}"')

    def test_teacher_sees_edit_but_not_delete(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("list_category"))
        self.assertContains(response, reverse("edit_category", args=[self.category.id]))
        self.assertNotContains(response, reverse("delete_category", args=[self.category.id]))

    def test_student_sees_neither_edit_nor_delete(self):
        self.client.force_login(self.student)
        for url in (reverse("list_category"), reverse("search")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertNotContains(response, reverse("edit_category", args=[self.category.id]))
                self.assertNotContains(response, reverse("delete_category", args=[self.category.id]))


class CategorySearchInputValidationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="admin1", email="admin1@test.com", password="pass12345!", role=User.ADMIN)
        cls.active = Category.objects.create(category="Programming", description="d", status=True)
        cls.inactive = Category.objects.create(category="Archived", description="d", status=False)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_invalid_status_and_category_are_ignored(self):
        for params in ({"status": "abc"}, {"category": "abc"}):
            with self.subTest(params=params):
                response = self.client.get(reverse("search"), params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.context["page_obj"]), 2)

    def test_inactive_filter_returns_inactive_and_keeps_option_selected(self):
        response = self.client.get(reverse("search"), {"status": "False"})
        self.assertEqual(list(response.context["page_obj"]), [self.inactive])
        self.assertRegex(response.content.decode(), r'value="False"\s+selected')

    def test_active_filter_returns_active(self):
        response = self.client.get(reverse("search"), {"status": "True"})
        self.assertEqual(list(response.context["page_obj"]), [self.active])
