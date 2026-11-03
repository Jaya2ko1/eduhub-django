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
