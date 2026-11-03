import json
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.json"
SIGN_IN_ERROR = "Invalid username or password."


class ConfigError(Exception):
    """config.json is missing or incomplete."""


def load_config(path):
    config_path = Path(path)
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError("config.json is missing") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError("config.json is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ConfigError("config.json must contain an object")
    missing = [
        key
        for key in ("username", "password_hash", "secret_key")
        if not isinstance(data.get(key), str) or not data.get(key)
    ]
    if missing:
        raise ConfigError("config.json is missing username, password_hash, or secret_key")
    if data["username"] != "admin":
        raise ConfigError("username must be admin")
    return data


def create_app(config_path=None):
    settings = load_config(config_path or DEFAULT_CONFIG_PATH)
    app = Flask(__name__)
    app.secret_key = settings["secret_key"]
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["ADMIN_USERNAME"] = settings["username"]
    app.config["PASSWORD_HASH"] = settings["password_hash"]

    @app.route("/", methods=["GET", "POST"])
    def sign_in():
        if session.get("user") == "admin":
            return redirect(url_for("servers"))
        error = None
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            username_ok = (
                username == "admin" and app.config["ADMIN_USERNAME"] == "admin"
            )
            password_ok = check_password_hash(app.config["PASSWORD_HASH"], password)
            if username_ok and password_ok:
                session.clear()
                session["user"] = "admin"
                return redirect(url_for("servers"))
            error = SIGN_IN_ERROR
        return render_template("sign_in.html", error=error)

    @app.get("/servers")
    def servers():
        if session.get("user") != "admin":
            return redirect(url_for("sign_in"))
        return render_template("servers.html")

    @app.post("/sign-out")
    def sign_out():
        session.clear()
        return redirect(url_for("sign_in"))

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8765)
