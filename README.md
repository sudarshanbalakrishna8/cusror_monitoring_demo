# Server monitor

Local demo. It serves a sign-in page and a placeholder server list on this Linux machine.

## Run locally

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `config.json` in the project directory. The app reads three fields:

| Field | Purpose |
| --- | --- |
| `username` | Must be `admin` |
| `password_hash` | Werkzeug hash of the sign-in password |
| `secret_key` | Signs the session cookie |

```json
{
  "username": "admin",
  "password_hash": "<hash>",
  "secret_key": "<long random string>"
}
```

Generate `<hash>` with the password you will type at sign-in. Store the hash, not the password:

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

`config.json` stays on this machine. It is listed in `.gitignore`.

```bash
flask --app app run --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765/ and sign in as `admin`.

Port 5000 is already in use on this machine. The demo listens on 8765.

## Tests

```bash
python -m unittest discover
```
