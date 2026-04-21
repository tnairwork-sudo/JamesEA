import unittest
from pathlib import Path


APP_FILE = Path(__file__).resolve().parents[1] / "app.py"


class AppStartupTests(unittest.TestCase):
    def test_app_run_uses_dynamic_port(self):
        source = APP_FILE.read_text()
        self.assertIn('app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=False)', source)

    def test_open_browser_skips_railway_and_uses_env_port(self):
        source = APP_FILE.read_text()
        self.assertIn('if os.getenv("RAILWAY_ENVIRONMENT")', source)
        self.assertIn('url = f"http://localhost:{os.getenv(\'PORT\', \'5001\')}"', source)


if __name__ == "__main__":
    unittest.main()
