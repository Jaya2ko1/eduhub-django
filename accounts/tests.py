from django.test import TestCase
from django.urls import reverse

from .models import User


class DashboardAccessTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="admin1", email="admin1@test.com", password="pass12345!", role=User.ADMIN)
        cls.teacher = User.objects.create_user(username="teacher1", email="teacher1@test.com", password="pass12345!", role=User.TEACHER)
        cls.student = User.objects.create_user(username="student1", email="student1@test.com", password="pass12345!", role=User.STUDENT)

    def test_admin_dashboard_is_admin_only(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("admin_dashboard")).status_code, 200)
        for user, own_dashboard in ((self.teacher, "instructor_dashboard"), (self.student, "student_dashboard")):
            with self.subTest(role=user.role):
                self.client.force_login(user)
                response = self.client.get(reverse("admin_dashboard"))
                self.assertRedirects(response, reverse(own_dashboard))

    def test_instructor_dashboard_is_teacher_only(self):
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse("instructor_dashboard")).status_code, 200)
        for user, own_dashboard in ((self.admin, "admin_dashboard"), (self.student, "student_dashboard")):
            with self.subTest(role=user.role):
                self.client.force_login(user)
                response = self.client.get(reverse("instructor_dashboard"))
                self.assertRedirects(response, reverse(own_dashboard))

    def test_dashboards_require_login(self):
        for name in ("admin_dashboard", "instructor_dashboard", "student_dashboard"):
            with self.subTest(dashboard=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)


class SuperuserRoleTests(TestCase):

    def test_new_superuser_gets_admin_role(self):
        superuser = User.objects.create_superuser(username="root", email="root@test.com", password="pass12345!")
        superuser.refresh_from_db()
        self.assertEqual(superuser.role, User.ADMIN)

    def test_existing_superuser_with_wrong_role_is_corrected_on_save(self):
        superuser = User.objects.create_superuser(username="root", email="root@test.com", password="pass12345!")
        User.objects.filter(pk=superuser.pk).update(role=User.STUDENT)
        superuser.refresh_from_db()
        superuser.save()
        superuser.refresh_from_db()
        self.assertEqual(superuser.role, User.ADMIN)

    def test_existing_superuser_is_corrected_on_login(self):
        superuser = User.objects.create_superuser(username="root", email="root@test.com", password="pass12345!")
        User.objects.filter(pk=superuser.pk).update(role=User.STUDENT)
        self.assertTrue(self.client.login(username="root@test.com", password="pass12345!"))
        superuser.refresh_from_db()
        self.assertEqual(superuser.role, User.ADMIN)

    def test_superuser_can_manage_courses(self):
        superuser = User.objects.create_superuser(username="root", email="root@test.com", password="pass12345!")
        self.client.force_login(superuser)
        self.assertEqual(self.client.get(reverse("create_course")).status_code, 200)

    def test_regular_users_keep_their_role(self):
        for role in (User.TEACHER, User.STUDENT, User.ADMIN):
            with self.subTest(role=role):
                user = User.objects.create_user(username=f"u_{role}", email=f"{role}@test.com", password="pass12345!", role=role)
                user.save()
                user.refresh_from_db()
                self.assertEqual(user.role, role)
