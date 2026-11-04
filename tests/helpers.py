import json
import tempfile
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import create_app


def build_client(testcase, password="correct-horse", local_names=None):
    directory = tempfile.TemporaryDirectory()
    testcase.addCleanup(directory.cleanup)
    root = Path(directory.name)
    config_path = root / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "username": "admin",
                "password_hash": generate_password_hash(password),
                "secret_key": "test-secret",
            }
        ),
        encoding="utf-8",
    )
    servers_path = root / "servers.json"
    app = create_app(config_path, servers_path)
    if local_names is not None:
        app.config["LOCAL_NAMES"] = set(local_names)
    return app.test_client(), password, servers_path


def sign_in(client, password):
    return client.post("/", data={"username": "admin", "password": password})


def csrf(client):
    with client.session_transaction() as sess:
        return sess["csrf_token"]
