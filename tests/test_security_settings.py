import os
from importlib import reload
from unittest.mock import patch

from django.test import SimpleTestCase

import doccure.settings as settings_module


class SecuritySettingsTests(SimpleTestCase):
    def reload_settings(self, allowed_hosts="localhost,127.0.0.1", trusted_origins=""):
        with patch.dict(
            os.environ,
            {
                "ALLOWED_HOSTS": allowed_hosts,
                "CSRF_TRUSTED_ORIGINS": trusted_origins,
            },
            clear=False,
        ):
            return reload(settings_module)

    def test_csrf_trusted_origins_use_explicit_env_values(self):
        settings = self.reload_settings(
            allowed_hosts="localhost,127.0.0.1",
            trusted_origins="https://example.com,https://api.example.com",
        )

        self.assertEqual(
            settings.CSRF_TRUSTED_ORIGINS,
            ["https://example.com", "https://api.example.com"],
        )

    def test_csrf_trusted_origins_default_to_https_for_allowed_hosts(self):
        settings = self.reload_settings(allowed_hosts="https://doccure.kverty.com,localhost")

        self.assertIn("https://doccure.kverty.com", settings.CSRF_TRUSTED_ORIGINS)
