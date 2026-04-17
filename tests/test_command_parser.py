import unittest
from unittest.mock import patch

from flask import Flask

from database import db
from database.models import Contact, Draft
from modules.command_parser import parse_command


class CommandParserTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add(Contact(name="Asha", email="asha@example.com", relationship_type="client"))
        db.session.add(Draft(from_email="asha@example.com", from_name="Asha", subject="Hi", drafted_reply="Draft text", status="pending"))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    @patch("modules.command_parser.send_whatsapp", return_value=True)
    @patch("modules.command_parser.gmail_handler.send_email", return_value=True)
    def test_send_command_sends_latest_draft(self, _mock_send_email, _mock_wa):
        result = parse_command("SEND", "whatsapp:+911", "whatsapp:+911")
        self.assertIn("Draft sent", result)
        draft = Draft.query.first()
        self.assertEqual(draft.status, "sent")

    def test_rejects_unauthorized_sender(self):
        result = parse_command("SEND", "whatsapp:+999", "whatsapp:+911")
        self.assertEqual(result, "unauthorized")


if __name__ == "__main__":
    unittest.main()
