import unittest

from servers import EMPTY_PROMPT, NOT_THIS_HOST, host_label, load_servers
from tests.helpers import build_client, csrf, sign_in

LOCAL = {"localhost", "127.0.0.1", "::1", "demo-host", "10.1.1.1"}


class ServerListTests(unittest.TestCase):
    def test_signed_in_user_sees_empty_prompt(self):
        client, password, _ = build_client(self, local_names=LOCAL)
        sign_in(client, password)
        page = client.get("/servers")
        self.assertEqual(page.status_code, 200)
        self.assertIn(EMPTY_PROMPT.encode(), page.data)
        self.assertIn(b"Sign out", page.data)

    def test_missing_field(self):
        client, password, path = build_client(self, local_names=LOCAL)
        sign_in(client, password)
        client.get("/servers")
        response = client.post(
            "/servers",
            data={"csrf_token": csrf(client), "name": "", "address": "127.0.0.1"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Display name and address are required.", response.data)
        self.assertEqual(load_servers(path), [])

    def test_successful_add(self):
        client, password, path = build_client(self, local_names=LOCAL)
        sign_in(client, password)
        client.get("/servers")
        response = client.post(
            "/servers",
            data={
                "csrf_token": csrf(client),
                "name": "Lab <box>",
                "address": "127.0.0.1",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Lab &lt;box&gt;", response.data)
        self.assertIn(b"127.0.0.1", response.data)
        self.assertIn(b"This host", response.data)
        saved = load_servers(path)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["name"], "Lab <box>")
        self.assertEqual(saved[0]["address"], "127.0.0.1")

    def test_remove_unknown_and_reload(self):
        client, password, path = build_client(self, local_names=LOCAL)
        sign_in(client, password)
        client.get("/servers")
        client.post(
            "/servers",
            data={"csrf_token": csrf(client), "name": "Local", "address": "demo-host"},
        )
        server_id = load_servers(path)[0]["id"]
        unknown = client.post(
            "/servers/remove",
            data={"csrf_token": csrf(client), "id": "missing"},
            follow_redirects=True,
        )
        self.assertIn(b"Local", unknown.data)
        self.assertEqual(len(load_servers(path)), 1)
        removed = client.post(
            "/servers/remove",
            data={"csrf_token": csrf(client), "id": server_id},
            follow_redirects=True,
        )
        self.assertIn(EMPTY_PROMPT.encode(), removed.data)
        self.assertEqual(load_servers(path), [])

        client.post(
            "/servers",
            data={"csrf_token": csrf(client), "name": "Kept", "address": "10.1.1.1"},
        )
        again = build_client(self, local_names=LOCAL)
        del again
        reloaded = load_servers(path)
        self.assertEqual(reloaded[0]["name"], "Kept")

    def test_list_survives_new_app(self):
        client, password, path = build_client(self, local_names=LOCAL)
        sign_in(client, password)
        client.get("/servers")
        client.post(
            "/servers",
            data={"csrf_token": csrf(client), "name": "Kept", "address": "192.0.2.10"},
        )
        from app import create_app

        app = create_app(path.parent / "config.json", path)
        app.config["LOCAL_NAMES"] = set(LOCAL)
        fresh = app.test_client()
        sign_in(fresh, password)
        page = fresh.get("/servers")
        self.assertIn(b"Kept", page.data)
        self.assertIn(b"Not this host", page.data)

    def test_host_labels(self):
        self.assertEqual(host_label("127.0.0.1", LOCAL), "This host")
        self.assertEqual(host_label("LocalHost", LOCAL), "This host")
        self.assertEqual(host_label("192.0.2.10", LOCAL), "Not this host")

    def test_server_page_each_status(self):
        client, password, path = build_client(self, local_names=LOCAL)
        sign_in(client, password)
        client.get("/servers")
        client.post(
            "/servers",
            data={"csrf_token": csrf(client), "name": "Here", "address": "10.1.1.1"},
        )
        client.post(
            "/servers",
            data={"csrf_token": csrf(client), "name": "Away", "address": "192.0.2.10"},
        )
        saved = {server["name"]: server["id"] for server in load_servers(path)}
        here = client.get(f"/servers/{saved['Here']}")
        self.assertIn(b"Here", here.data)
        self.assertIn(b"10.1.1.1", here.data)
        self.assertIn(b"This host", here.data)
        self.assertIn(b"CPU", here.data)
        self.assertIn(b"Memory", here.data)
        self.assertIn(b"Network", here.data)
        self.assertIn(b"Ports", here.data)
        self.assertIn(b'data-refresh="5000"', here.data)
        away = client.get(f"/servers/{saved['Away']}")
        self.assertIn(NOT_THIS_HOST.encode(), away.data)
        self.assertNotIn(b"CPU", away.data)
        self.assertNotIn(b'data-refresh="5000"', away.data)
        missing = client.get("/servers/not-a-real-server", follow_redirects=False)
        self.assertEqual(missing.status_code, 302)
        self.assertTrue(missing.headers["Location"].endswith("/servers"))

    def test_not_this_host_metrics_skip_collection(self):
        client, password, path = build_client(self, local_names=LOCAL)
        sign_in(client, password)
        client.get("/servers")
        client.post(
            "/servers",
            data={"csrf_token": csrf(client), "name": "Away", "address": "192.0.2.10"},
        )
        server_id = load_servers(path)[0]["id"]
        response = client.get(f"/servers/{server_id}/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["message"], NOT_THIS_HOST)
        self.assertNotIn("cpu", response.get_json())


if __name__ == "__main__":
    unittest.main()
