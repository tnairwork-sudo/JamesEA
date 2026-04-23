import unittest
import os
import runpy
from pathlib import Path
from unittest.mock import MagicMock, patch


APP_FILE = Path(__file__).resolve().parents[1] / "app.py"


class AppStartupTests(unittest.TestCase):
    def test_app_run_uses_port_from_environment(self):
        with patch.dict(os.environ, {"PORT": "6100", "AUTO_OPEN_BROWSER": "0", "SECRET_KEY": "test", "DATABASE_URL": "sqlite:///:memory:"}, clear=False):
            with patch("modules.scheduler.start_scheduler"), patch("flask.app.Flask.run") as mock_run, patch("threading.Timer") as mock_timer:
                mock_timer.return_value = MagicMock()
                runpy.run_path(str(APP_FILE), run_name="__main__")
                self.assertEqual(mock_run.call_args.kwargs["port"], 6100)

    def test_open_browser_skips_on_railway(self):
        with patch.dict(os.environ, {"AUTO_OPEN_BROWSER": "1", "RAILWAY_ENVIRONMENT": "production", "SECRET_KEY": "test", "DATABASE_URL": "sqlite:///:memory:"}, clear=False):
            with patch("modules.scheduler.start_scheduler"):
                namespace = runpy.run_path(str(APP_FILE))
            with patch("webbrowser.get") as mock_get, patch("webbrowser.open_new") as mock_open_new:
                namespace["_open_browser"]()
                mock_get.assert_not_called()
                mock_open_new.assert_not_called()


if __name__ == "__main__":
    unittest.main()
