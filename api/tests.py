from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from accounts.models import User
from categories.models import Category
from courses.models import Course
from .views import CourseDeleteAPIView, CoursePaginationAPIView, CourseRetrieveAPIView


class CourseApiTestData(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="admin1", email="admin1@test.com", password="pass12345!", role=User.ADMIN)
        cls.teacher = User.objects.create_user(username="teacher1", email="teacher1@test.com", password="pass12345!", role=User.TEACHER)
        cls.other_teacher = User.objects.create_user(username="teacher2", email="teacher2@test.com", password="pass12345!", role=User.TEACHER)
        cls.student = User.objects.create_user(username="student1", email="student1@test.com", password="pass12345!", role=User.STUDENT)
        cls.category = Category.objects.create(category="Programming", description="Programming courses")
        cls.other_category = Category.objects.create(category="Design", description="Design courses")
        cls.published = cls.make_course("Published T1", cls.teacher, "published")
        cls.draft = cls.make_course("Draft T1", cls.teacher, "draft")
        cls.other_published = cls.make_course("Published T2", cls.other_teacher, "published", cls.other_category)
        cls.other_draft = cls.make_course("Draft T2", cls.other_teacher, "draft")

    @classmethod
    def make_course(cls, title, instructor, status, category=None):
        return Course.objects.create(
            title=title,
            category=category or cls.category,
            instructor=instructor,
            short_description="short",
            full_description="full",
            price=100,
            status=status,
        )

    def client_for(self, user=None):
        client = APIClient()
        if user:
            client.force_authenticate(user)
        return client

    def titles(self, response):
        data = response.json()
        items = data["results"] if isinstance(data, dict) else data
        return sorted(item["title"] for item in items)


class CourseApiAuthenticationTests(CourseApiTestData):

    def test_anonymous_user_gets_401(self):
        client = self.client_for()
        self.assertEqual(client.get(reverse("courseApi")).status_code, 401)
        self.assertEqual(client.get(reverse("course_filter")).status_code, 401)
        self.assertEqual(client.post(reverse("course-create"), {}).status_code, 401)

    def test_token_authentication_is_accepted(self):
        token = Token.objects.create(user=self.student)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = client.get(reverse("courseApi"))
        self.assertEqual(response.status_code, 200)

    def test_session_login_without_token_is_rejected(self):
        client = APIClient()
        client.force_login(self.student)
        self.assertEqual(client.get(reverse("courseApi")).status_code, 401)


class CourseListVisibilityTests(CourseApiTestData):

    def test_student_sees_only_published_courses(self):
        client = self.client_for(self.student)
        expected = ["Published T1", "Published T2"]
        self.assertEqual(self.titles(client.get(reverse("courseApi"))), expected)
        self.assertEqual(self.titles(client.get(reverse("course_filter"))), expected)

    def test_student_cannot_list_drafts_with_status_filter(self):
        client = self.client_for(self.student)
        response = client.get(reverse("course_filter"), {"status": "draft"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.titles(response), [])

    def test_student_instructor_filter_returns_only_published(self):
        client = self.client_for(self.student)
        response = client.get(reverse("course_filter"), {"instructor": self.other_teacher.id})
        self.assertEqual(self.titles(response), ["Published T2"])

    def test_student_paginated_count_excludes_drafts(self):
        response = self.client_for(self.student).get(reverse("courseApi"))
        self.assertEqual(response.json()["count"], 2)

    def test_teacher_sees_published_courses_and_own_drafts(self):
        client = self.client_for(self.teacher)
        expected = ["Draft T1", "Published T1", "Published T2"]
        self.assertEqual(self.titles(client.get(reverse("courseApi"))), expected)
        self.assertEqual(self.titles(client.get(reverse("course_filter"))), expected)

    def test_teacher_draft_filter_returns_only_own_drafts(self):
        response = self.client_for(self.teacher).get(reverse("course_filter"), {"status": "draft"})
        self.assertEqual(self.titles(response), ["Draft T1"])

    def test_teacher_cannot_see_another_teachers_draft(self):
        response = self.client_for(self.teacher).get(reverse("course_filter"), {"instructor": self.other_teacher.id})
        self.assertEqual(self.titles(response), ["Published T2"])

    def test_admin_sees_all_courses(self):
        client = self.client_for(self.admin)
        expected = ["Draft T1", "Draft T2", "Published T1", "Published T2"]
        self.assertEqual(self.titles(client.get(reverse("courseApi"))), expected)
        self.assertEqual(self.titles(client.get(reverse("course_filter"))), expected)

    def test_admin_draft_filter_returns_all_drafts(self):
        response = self.client_for(self.admin).get(reverse("course_filter"), {"status": "draft"})
        self.assertEqual(self.titles(response), ["Draft T1", "Draft T2"])


class CourseListBehaviourTests(CourseApiTestData):

    def test_pagination_structure_and_page_size(self):
        for i in range(4):
            self.make_course(f"Extra {i}", self.teacher, "published")
        response = self.client_for(self.student).get(reverse("courseApi"))
        data = response.json()
        self.assertEqual(set(data.keys()), {"count", "next", "previous", "results"})
        self.assertEqual(data["count"], 6)
        self.assertEqual(len(data["results"]), 5)
        self.assertIsNotNone(data["next"])
        self.assertIsNone(data["previous"])

        second_page = self.client_for(self.student).get(reverse("courseApi"), {"page": 2}).json()
        self.assertEqual(len(second_page["results"]), 1)
        self.assertNotIn("Draft T1", [item["title"] for item in data["results"] + second_page["results"]])

    def test_category_filter(self):
        response = self.client_for(self.admin).get(reverse("course_filter"), {"category": self.other_category.id})
        self.assertEqual(self.titles(response), ["Published T2"])

    def test_search_filter(self):
        response = self.client_for(self.student).get(reverse("course_filter"), {"search": "t1"})
        self.assertEqual(self.titles(response), ["Published T1"])


class UnroutedViewVisibilityTests(CourseApiTestData):

    def setUp(self):
        self.factory = APIRequestFactory()

    def retrieve(self, user, course):
        request = self.factory.get(f"/courses/{course.id}/")
        force_authenticate(request, user=user)
        return CourseRetrieveAPIView.as_view()(request, pk=course.id)

    def test_student_cannot_retrieve_draft(self):
        self.assertEqual(self.retrieve(self.student, self.draft).status_code, 404)
        self.assertEqual(self.retrieve(self.student, self.published).status_code, 200)

    def test_teacher_retrieves_own_draft_but_not_another_teachers(self):
        self.assertEqual(self.retrieve(self.teacher, self.draft).status_code, 200)
        self.assertEqual(self.retrieve(self.teacher, self.other_draft).status_code, 404)
        self.assertEqual(self.retrieve(self.teacher, self.other_published).status_code, 200)

    def test_admin_retrieves_any_course(self):
        for course in (self.published, self.draft, self.other_published, self.other_draft):
            with self.subTest(course=course.title):
                self.assertEqual(self.retrieve(self.admin, course).status_code, 200)

    def test_pagination_view_hides_drafts_from_students(self):
        request = self.factory.get("/courses/")
        force_authenticate(request, user=self.student)
        response = CoursePaginationAPIView.as_view()(request)
        response.render()
        self.assertEqual(sorted(item["title"] for item in response.data), ["Published T1", "Published T2"])


class CourseCreateApiTests(CourseApiTestData):

    def course_payload(self, **overrides):
        data = {
            "title": "API Course",
            "category": self.category.id,
            "short_description": "short",
            "full_description": "full",
            "price": "10.00",
            "status": "draft",
        }
        data.update(overrides)
        return data

    def test_teacher_creates_course_as_instructor(self):
        response = self.client_for(self.teacher).post(reverse("course-create"), self.course_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Course.objects.get(title="API Course").instructor, self.teacher)

    def test_teacher_cannot_create_course_for_another_teacher(self):
        response = self.client_for(self.teacher).post(
            reverse("course-create"),
            self.course_payload(instructor=self.other_teacher.id),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("instructor", response.json())
        self.assertFalse(Course.objects.filter(title="API Course").exists())

    def test_admin_creates_course_for_selected_teacher(self):
        response = self.client_for(self.admin).post(
            reverse("course-create"),
            self.course_payload(instructor=self.other_teacher.id),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Course.objects.get(title="API Course").instructor, self.other_teacher)

    def test_admin_must_select_instructor(self):
        response = self.client_for(self.admin).post(reverse("course-create"), self.course_payload(), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("instructor", response.json())

    def test_student_cannot_create_course(self):
        response = self.client_for(self.student).post(reverse("course-create"), self.course_payload(), format="json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Course.objects.filter(title="API Course").exists())


class CourseFilterInputValidationTests(CourseApiTestData):

    def test_non_numeric_category_or_instructor_returns_400(self):
        client = self.client_for(self.admin)
        for name in ("category", "instructor"):
            with self.subTest(param=name):
                response = client.get(reverse("course_filter"), {name: "abc"})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), {name: ["Must be an integer."]})

    def test_valid_numeric_filters_still_work(self):
        response = self.client_for(self.admin).get(reverse("course_filter"), {"instructor": self.other_teacher.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.titles(response), ["Draft T2", "Published T2"])


class CourseDeleteViewOwnershipTests(CourseApiTestData):

    def delete(self, user, course):
        request = APIRequestFactory().delete(f"/courses/{course.id}/")
        force_authenticate(request, user=user)
        return CourseDeleteAPIView.as_view()(request, pk=course.id)

    def test_teacher_cannot_delete_another_teachers_course(self):
        self.assertEqual(self.delete(self.teacher, self.other_published).status_code, 404)
        self.assertTrue(Course.objects.filter(id=self.other_published.id).exists())

    def test_teacher_can_delete_own_course(self):
        self.assertEqual(self.delete(self.teacher, self.draft).status_code, 204)
        self.assertFalse(Course.objects.filter(id=self.draft.id).exists())

    def test_admin_can_delete_any_course(self):
        self.assertEqual(self.delete(self.admin, self.other_draft).status_code, 204)

    def test_student_cannot_delete(self):
        self.assertEqual(self.delete(self.student, self.published).status_code, 403)
        self.assertTrue(Course.objects.filter(id=self.published.id).exists())


class TokenObtainTests(CourseApiTestData):

    def setUp(self):
        cache.clear()

    def test_valid_credentials_return_token_that_works(self):
        response = APIClient().post(
            reverse("api-token"), {"username": "student1@test.com", "password": "pass12345!"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        token = response.json()["token"]
        self.assertEqual(Token.objects.get(user=self.student).key, token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(client.get(reverse("courseApi")).status_code, 200)

    def test_wrong_password_returns_400_without_token(self):
        response = APIClient().post(
            reverse("api-token"), {"username": "student1@test.com", "password": "wrong"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("token", response.json())
        self.assertFalse(Token.objects.filter(user=self.student).exists())

    def test_get_is_not_allowed(self):
        self.assertEqual(APIClient().get(reverse("api-token")).status_code, 405)


class TokenThrottleTests(CourseApiTestData):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_token_endpoint_blocks_after_five_attempts_per_minute(self):
        client = APIClient()
        statuses = [
            client.post(reverse("api-token"), {"username": "student1@test.com", "password": f"wrong{i}"}, format="json").status_code
            for i in range(6)
        ]
        self.assertEqual(statuses[:5], [400] * 5)
        self.assertEqual(statuses[5], 429)

        response = client.post(reverse("api-token"), {"username": "student1@test.com", "password": "pass12345!"}, format="json")
        self.assertEqual(response.status_code, 429)
        self.assertFalse(Token.objects.filter(user=self.student).exists())

    def test_default_throttles_are_configured(self):
        from django.conf import settings
        rest = settings.REST_FRAMEWORK
        self.assertIn("rest_framework.throttling.AnonRateThrottle", rest["DEFAULT_THROTTLE_CLASSES"])
        self.assertIn("rest_framework.throttling.UserRateThrottle", rest["DEFAULT_THROTTLE_CLASSES"])
        self.assertEqual(rest["DEFAULT_THROTTLE_RATES"]["token"], "5/min")
