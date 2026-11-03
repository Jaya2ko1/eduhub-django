import json
import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase


SETTINGS_PROBE = """
import json
from django.conf import settings
print(json.dumps({
    "DEBUG": settings.DEBUG,
    "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
    "USES_DEV_KEY": settings.SECRET_KEY.startswith("django-insecure-local-development"),
    "CSRF_TRUSTED_ORIGINS": settings.CSRF_TRUSTED_ORIGINS,
    "SECURE_SSL_REDIRECT": settings.SECURE_SSL_REDIRECT,
    "SESSION_COOKIE_SECURE": settings.SESSION_COOKIE_SECURE,
    "CSRF_COOKIE_SECURE": settings.CSRF_COOKIE_SECURE,
    "SECURE_PROXY_SSL_HEADER": settings.SECURE_PROXY_SSL_HEADER,
    "SECURE_HSTS_SECONDS": settings.SECURE_HSTS_SECONDS,
    "SECURE_HSTS_INCLUDE_SUBDOMAINS": settings.SECURE_HSTS_INCLUDE_SUBDOMAINS,
    "STATIC_ROOT": str(settings.STATIC_ROOT),
    "LOG_LEVEL": settings.LOGGING["root"]["level"],
    "REQUEST_LOG_LEVEL": settings.LOGGING["loggers"]["django.request"]["level"],
}))
"""

TEST_SECRET_KEY = "test-only-secret-key-for-settings-tests-0123456789"


class EnvironmentSettingsTests(SimpleTestCase):
    """Settings load once per process, so each case runs in a fresh Python process."""

    def load_settings(self, **env_vars):
        env = {key: value for key, value in os.environ.items() if not key.startswith("DJANGO_")}
        env["DJANGO_SETTINGS_MODULE"] = "eduhub.settings"
        env.update(env_vars)
        return subprocess.run(
            [sys.executable, "-c", SETTINGS_PROBE],
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def loaded(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_missing_secret_key_with_debug_off_fails_clearly(self):
        for key_value in (None, "", "   "):
            with self.subTest(key=repr(key_value)):
                env = {"DJANGO_DEBUG": "False"}
                if key_value is not None:
                    env["DJANGO_SECRET_KEY"] = key_value
                result = self.load_settings(**env)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ImproperlyConfigured", result.stderr)
                self.assertIn("Set the DJANGO_SECRET_KEY environment variable", result.stderr)

    def test_debug_defaults_to_false_and_parses_values(self):
        self.assertFalse(self.loaded(self.load_settings(DJANGO_SECRET_KEY=TEST_SECRET_KEY))["DEBUG"])
        for value, expected in (("True", True), ("1", True), ("on", True), ("false", False), ("0", False), ("No", False)):
            with self.subTest(DJANGO_DEBUG=value):
                result = self.load_settings(DJANGO_DEBUG=value, DJANGO_SECRET_KEY=TEST_SECRET_KEY)
                self.assertEqual(self.loaded(result)["DEBUG"], expected)

        result = self.load_settings(DJANGO_DEBUG="maybe", DJANGO_SECRET_KEY=TEST_SECRET_KEY)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_DEBUG must be one of", result.stderr)
        self.assertNotIn(TEST_SECRET_KEY, result.stderr + result.stdout)

    def test_debug_on_without_secret_key_uses_local_fallback(self):
        data = self.loaded(self.load_settings(DJANGO_DEBUG="True"))
        self.assertTrue(data["DEBUG"])
        self.assertTrue(data["USES_DEV_KEY"])

        data = self.loaded(self.load_settings(DJANGO_DEBUG="True", DJANGO_SECRET_KEY=TEST_SECRET_KEY))
        self.assertFalse(data["USES_DEV_KEY"])

    def test_allowed_hosts_are_parsed_from_comma_separated_list(self):
        result = self.load_settings(
            DJANGO_SECRET_KEY=TEST_SECRET_KEY,
            DJANGO_ALLOWED_HOSTS=" eduhub.example.com, www.eduhub.example.com ,,",
        )
        self.assertEqual(self.loaded(result)["ALLOWED_HOSTS"], ["eduhub.example.com", "www.eduhub.example.com"])
        self.assertEqual(self.loaded(self.load_settings(DJANGO_SECRET_KEY=TEST_SECRET_KEY))["ALLOWED_HOSTS"], [])


class ProductionSettingsTests(SimpleTestCase):
    """HTTPS, cookie, static and logging settings driven by environment variables."""

    load_settings = EnvironmentSettingsTests.load_settings
    loaded = EnvironmentSettingsTests.loaded

    def test_https_and_cookie_security_on_by_default_when_debug_off(self):
        data = self.loaded(self.load_settings(DJANGO_SECRET_KEY=TEST_SECRET_KEY))
        self.assertTrue(data["SECURE_SSL_REDIRECT"])
        self.assertTrue(data["SESSION_COOKIE_SECURE"])
        self.assertTrue(data["CSRF_COOKIE_SECURE"])
        self.assertEqual(data["SECURE_HSTS_SECONDS"], 0)
        self.assertIsNone(data["SECURE_PROXY_SSL_HEADER"])

    def test_https_and_cookie_security_off_for_local_debug(self):
        data = self.loaded(self.load_settings(DJANGO_DEBUG="True"))
        self.assertFalse(data["SECURE_SSL_REDIRECT"])
        self.assertFalse(data["SESSION_COOKIE_SECURE"])
        self.assertFalse(data["CSRF_COOKIE_SECURE"])

    def test_security_settings_can_be_overridden(self):
        data = self.loaded(self.load_settings(
            DJANGO_SECRET_KEY=TEST_SECRET_KEY,
            DJANGO_SECURE_SSL_REDIRECT="False",
            DJANGO_SECURE_PROXY_SSL_HEADER="True",
            DJANGO_SECURE_HSTS_SECONDS="3600",
            DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS="True",
            DJANGO_CSRF_TRUSTED_ORIGINS="https://eduhub.example.com, https://www.eduhub.example.com",
        ))
        self.assertFalse(data["SECURE_SSL_REDIRECT"])
        self.assertEqual(data["SECURE_PROXY_SSL_HEADER"], ["HTTP_X_FORWARDED_PROTO", "https"])
        self.assertEqual(data["SECURE_HSTS_SECONDS"], 3600)
        self.assertTrue(data["SECURE_HSTS_INCLUDE_SUBDOMAINS"])
        self.assertEqual(data["CSRF_TRUSTED_ORIGINS"], ["https://eduhub.example.com", "https://www.eduhub.example.com"])

    def test_invalid_hsts_seconds_fails_clearly(self):
        result = self.load_settings(DJANGO_SECRET_KEY=TEST_SECRET_KEY, DJANGO_SECURE_HSTS_SECONDS="one year")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECURE_HSTS_SECONDS must be a whole number of seconds", result.stderr)

    def test_static_root_and_logging(self):
        data = self.loaded(self.load_settings(DJANGO_SECRET_KEY=TEST_SECRET_KEY))
        self.assertEqual(data["STATIC_ROOT"], str(settings.BASE_DIR / "staticfiles"))
        self.assertEqual(data["LOG_LEVEL"], "WARNING")
        self.assertEqual(data["REQUEST_LOG_LEVEL"], "ERROR")
        self.assertEqual(self.loaded(self.load_settings(DJANGO_DEBUG="True"))["LOG_LEVEL"], "INFO")
        self.assertEqual(
            self.loaded(self.load_settings(DJANGO_SECRET_KEY=TEST_SECRET_KEY, DJANGO_LOG_LEVEL="error"))["LOG_LEVEL"],
            "ERROR",
        )
