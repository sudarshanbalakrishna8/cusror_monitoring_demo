import hmac
import json
import secrets
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from metrics import MetricState, collect, listening_ports, read_meminfo, read_netdev, read_stat
from servers import (
    EMPTY_PROMPT,
    NOT_THIS_HOST,
    add_server,
    find_server,
    host_label,
    load_servers,
    local_names,
    remove_server,
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.json"
DEFAULT_SERVERS_PATH = BASE_DIR / "servers.json"
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
        if not isinstance(data.get(key), str) or not data.get(key).strip()
    ]
    if missing:
        raise ConfigError("config.json is missing username, password_hash, or secret_key")
    if data["username"].strip() != "admin":
        raise ConfigError("username must be admin")
    return data


def create_app(config_path=None, servers_path=None):
    settings = load_config(config_path or DEFAULT_CONFIG_PATH)
    app = Flask(__name__)
    app.secret_key = settings["secret_key"]
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["ADMIN_USERNAME"] = "admin"
    app.config["PASSWORD_HASH"] = settings["password_hash"]
    app.config["SERVERS_PATH"] = str(servers_path or DEFAULT_SERVERS_PATH)
    app.jinja_env.autoescape = True
    app.extensions["metric_state"] = MetricState()

    def names():
        override = app.config.get("LOCAL_NAMES")
        if override is not None:
            return set(override)
        return local_names()

    def signed_in():
        return session.get("user") == "admin"

    def ensure_csrf():
        token = session.get("csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        return token

    def csrf_ok():
        expected = session.get("csrf_token", "")
        sent = request.form.get("csrf_token", "")
        if not expected or not sent or len(expected) != len(sent):
            return False
        return hmac.compare_digest(expected, sent)

    def require_sign_in():
        if not signed_in():
            return redirect(url_for("sign_in"))
        return None

    def rows():
        return [
            {**server, "status": host_label(server["address"], names())}
            for server in load_servers(app.config["SERVERS_PATH"])
        ]

    @app.context_processor
    def template_context():
        return {
            "signed_in": signed_in(),
            "csrf_token": session.get("csrf_token", ""),
        }

    @app.route("/", methods=["GET", "POST"])
    def sign_in():
        if signed_in():
            return redirect(url_for("servers"))
        error = None
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            username_ok = username == "admin"
            password_ok = check_password_hash(app.config["PASSWORD_HASH"], password)
            if username_ok and password_ok:
                session.clear()
                session["user"] = "admin"
                ensure_csrf()
                return redirect(url_for("servers"))
            error = SIGN_IN_ERROR
        return render_template("sign_in.html", error=error)

    @app.get("/servers")
    def servers():
        blocked = require_sign_in()
        if blocked:
            return blocked
        ensure_csrf()
        return render_template(
            "servers.html",
            servers=rows(),
            empty_prompt=EMPTY_PROMPT,
            error=None,
        )

    @app.post("/servers")
    def add_server_route():
        blocked = require_sign_in()
        if blocked:
            return blocked
        if not csrf_ok():
            abort(400)
        _, error = add_server(
            app.config["SERVERS_PATH"],
            request.form.get("name", ""),
            request.form.get("address", ""),
        )
        if error:
            return (
                render_template(
                    "servers.html",
                    servers=rows(),
                    empty_prompt=EMPTY_PROMPT,
                    error=error,
                ),
                400,
            )
        return redirect(url_for("servers"))

    @app.post("/servers/remove")
    def remove_server_route():
        blocked = require_sign_in()
        if blocked:
            return blocked
        if not csrf_ok():
            abort(400)
        remove_server(app.config["SERVERS_PATH"], request.form.get("id", ""))
        return redirect(url_for("servers"))

    @app.get("/servers/<server_id>")
    def server_detail(server_id):
        blocked = require_sign_in()
        if blocked:
            return blocked
        server = find_server(app.config["SERVERS_PATH"], server_id)
        if server is None:
            return redirect(url_for("servers"))
        status = host_label(server["address"], names())
        metrics = None
        if status == "This host":
            metrics = _live_metrics(app)
        return render_template(
            "server.html",
            server=server,
            status=status,
            message=NOT_THIS_HOST,
            metrics=metrics,
        )

    @app.get("/servers/<server_id>/metrics")
    def server_metrics(server_id):
        blocked = require_sign_in()
        if blocked:
            return blocked
        server = find_server(app.config["SERVERS_PATH"], server_id)
        if server is None:
            return redirect(url_for("servers"))
        if host_label(server["address"], names()) != "This host":
            return jsonify({"message": NOT_THIS_HOST})
        return jsonify(_live_metrics(app))

    @app.post("/sign-out")
    def sign_out():
        session.clear()
        return redirect(url_for("sign_in"))

    return app


def _live_metrics(app):
    return collect(
        app.extensions["metric_state"],
        read_stat=read_stat,
        read_meminfo=read_meminfo,
        read_netdev=read_netdev,
        read_ports=listening_ports,
        now=_monotonic(),
    )


def _monotonic():
    import time

    return time.monotonic()


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8765)
