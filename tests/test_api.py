import unittest

from flask import Flask

from database import db
from database.models import PersonalTask
from routes.api import bp as api_bp


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        self.app.register_blueprint(api_bp)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add(PersonalTask(description="Follow up", status="pending"))
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_patch_task_done(self):
        task = PersonalTask.query.first()
        response = self.client.patch(f"/api/tasks/{task.id}", json={"status": "done"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        updated = PersonalTask.query.get(task.id)
        self.assertEqual(updated.status, "done")


if __name__ == "__main__":
    unittest.main()
