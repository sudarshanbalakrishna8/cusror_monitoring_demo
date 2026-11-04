# Server monitor

Local demo for a read-only view of this Linux machine: CPU, memory, network, and listening ports.

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
| `secret_key` | Signs the session cookie. The app refuses to start when this is missing or empty |

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

Open http://127.0.0.1:8765/ and sign in as `admin`. The server list opens only after sign-in.

Port 5000 is already in use on this machine. The demo listens on 8765.

GitHub Actions runs the unit tests on push and pull request. Start the app on this machine.

## Server list

An empty list shows: “No servers yet. Add a server to begin.”

Add a server with a display name and an address. Both are required. Entries are stored in `servers.json`.

Remove deletes that entry from `servers.json` only. The host is left unchanged.

These addresses count as this host: `localhost`, `127.0.0.1`, `::1`, this machine’s hostname, and its interface addresses. Any other address is “Not this host.”

## Server page

“This host” shows CPU, memory, network, and ports. The page refreshes those cards every 5 seconds.

“Not this host” shows “This demo only monitors the machine it is running on.” and no metric cards.

| Card | Fields |
| --- | --- |
| CPU | Total CPU use, in percent |
| Memory | Total, used, and available memory in MiB, plus used percent |
| Network | Interface name, bytes received, bytes sent, and the rate in bytes/s since the last refresh |
| Ports | Listening TCP and UDP ports from a read-only `ss` command: protocol, local address, port, process name, and process id |

A card shows “Unavailable” when its read fails. The other cards still update.

## Tests

```bash
python -m unittest discover
```
