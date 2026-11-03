import json
import tempfile
import unittest
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import SIGN_IN_ERROR, ConfigError, create_app


class AuthTests(unittest.TestCase):
    def test_missing_config(self):
        missing = Path(tempfile.gettempdir()) / "missing-server-monitor-config.json"
        if missing.exists():
            missing.unlink()
        with self.assertRaises(ConfigError):
            create_app(missing)

    def test_wrong_password(self):
        password = "correct-horse"
        with self._app(password) as client:
            response = client.post(
                "/",
                data={"username": "admin", "password": "wrong-password"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data.count(SIGN_IN_ERROR.encode()), 1)
            self.assertIn(b"Sign in", response.data)
            self.assertNotIn(b"wrong-password", response.data)
            with client.session_transaction() as sess:
                self.assertNotIn("user", sess)

            other = client.post(
                "/",
                data={"username": "root", "password": password},
            )
            self.assertEqual(other.status_code, 200)
            self.assertEqual(other.data.count(SIGN_IN_ERROR.encode()), 1)
            with client.session_transaction() as sess:
                self.assertNotIn("user", sess)

    def test_correct_password(self):
        password = "correct-horse"
        with self._app(password) as client:
            response = client.post(
                "/",
                data={"username": "admin", "password": password},
                follow_redirects=False,
            )
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.headers["Location"].endswith("/servers"))
            cookie = response.headers["Set-Cookie"]
            self.assertIn("HttpOnly", cookie)
            self.assertIn("SameSite=Strict", cookie)
            self.assertNotIn(password, cookie)
            page = client.get("/servers")
            self.assertEqual(page.status_code, 200)
            self.assertIn(b"Server list placeholder.", page.data)
            self.assertNotIn(password.encode(), page.data)

    def test_sign_out(self):
        password = "correct-horse"
        with self._app(password) as client:
            client.post("/", data={"username": "admin", "password": password})
            response = client.post("/sign-out", follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.headers["Location"].endswith("/"))
            with client.session_transaction() as sess:
                self.assertNotIn("user", sess)
            page = client.get("/")
            self.assertEqual(page.status_code, 200)
            self.assertIn(b"Sign in", page.data)
            self.assertNotIn(SIGN_IN_ERROR.encode(), page.data)

    def _app(self, password):
        self._temp = tempfile.TemporaryDirectory()
        path = Path(self._temp.name) / "config.json"
        path.write_text(
            json.dumps(
                {
                    "username": "admin",
                    "password_hash": generate_password_hash(password),
                    "secret_key": "test-secret",
                }
            ),
            encoding="utf-8",
        )
        app = create_app(path)
        self.addCleanup(self._temp.cleanup)
        return app.test_client()


if __name__ == "__main__":
    unittest.main()
