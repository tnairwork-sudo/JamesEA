import unittest
from unittest.mock import patch

from flask import Flask

from database import db
from routes.webhook import bp as webhook_bp


class WhatsAppWebhookTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        self.app.register_blueprint(webhook_bp)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    @patch("modules.command_parser.send_whatsapp", return_value=True)
    def test_whatsapp_returns_twiml_xml(self, _mock_wa):
        response = self.client.post(
            "/webhook/whatsapp",
            data={"From": "whatsapp:+911", "Body": "CALL REPORT"},
            environ_base={"TUSHAAR_WHATSAPP": "whatsapp:+911"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response.content_type)
        data = response.data.decode()
        self.assertIn("<Response>", data)
        self.assertIn("<Message>", data)

    @patch("modules.command_parser.send_whatsapp", return_value=True)
    def test_whatsapp_default_message_when_result_empty(self, _mock_wa):
        with patch("routes.webhook.parse_command", return_value=""):
            response = self.client.post(
                "/webhook/whatsapp",
                data={"From": "whatsapp:+911", "Body": "UNKNOWN"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.data.decode()
        self.assertIn("Command received.", data)

    @patch("modules.command_parser.send_whatsapp", return_value=True)
    def test_whatsapp_default_message_when_result_none(self, _mock_wa):
        with patch("routes.webhook.parse_command", return_value=None):
            response = self.client.post(
                "/webhook/whatsapp",
                data={"From": "whatsapp:+911", "Body": "UNKNOWN"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.data.decode()
        self.assertIn("Command received.", data)

    def test_gmail_webhook_returns_200(self):
        response = self.client.post("/webhook/gmail")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
