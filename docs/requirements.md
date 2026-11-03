# Demo Monitoring Infrastructure — Requirements

Local demo for internal teams who need a quick, read-only view of CPU, memory, network, and listening ports. The app runs on the Linux machine where Cursor is running and reads that machine only.

## Problem

L1, L2, and L3 engineers currently sign in to servers to check live memory, CPU, network, and port usage. This demo gives them those facts in one browser page on the machine they already have open.

## Users

Internal infrastructure and application teams (L1, L2, and L3). Everyone uses the same demo account. The app does not separate roles.

## Demo limits

- Deploy and use the app on this Linux machine.
- Collect metrics from this machine with `/proc` and standard local Linux commands.
- Show current values and refresh them every 5 seconds. The demo keeps no history.
- Treat the monitored host as read-only: no shell, no restarts, and no configuration changes on the machine.
- Users can add and remove server entries in the app. Those entries are labels in the demo. Metrics load only when the entry points at this machine (`localhost`, `127.0.0.1`, `::1`, this host’s name, or one of its interface addresses). Any other entry stays in the list with the status “Not this host.”

## Features

### 1. Read-only monitoring UI

A signed-in user opens a server and sees live CPU, memory, network, and listening-port data. The page refreshes every 5 seconds. Metric pages have no actions that change the host.

### 2. Sign in

The sign-in form accepts the username `admin`. The password is checked against a hash in a local config file. A wrong password shows an error and stays on the sign-in page. There is no password-change screen.

### 3. Server list

A signed-in user can add a Linux server (display name and address) and can remove an entry. The list shows each server’s name, address, and whether it is this host. Choosing a server opens its metric page.

## Requirements

### Sign in

- Unauthenticated visitors see only the sign-in page.
- The accepted username is `admin`.
- The password matches the hash in the local config file. The app stores and logs only the hash, never the password.
- A successful sign-in opens the server list. The session ends when the user signs out, or when the browser session ends.

### Server list

- The list is empty on first use, with a short prompt to add a server.
- Add asks for a display name and an address (hostname or IP). Both are required.
- Remove deletes that entry from the demo list and does nothing to the host.
- Entries are saved in a local data file so they remain after a restart.
- An entry that refers to this machine is marked “This host.” Any other address is marked “Not this host.”

### Metrics (this host only)

When the open server is this host, the page shows:

| Area | What the page shows |
| --- | --- |
| CPU | Total CPU use as a percentage |
| Memory | Total, used, and available memory, plus used percent |
| Network | For each interface: name, bytes received, bytes sent, and the rate since the previous refresh |
| Ports | Each listening TCP and UDP port: protocol, local address, port, process name, and process id |

- Values refresh every 5 seconds while the page is open.
- The page reads `/proc` and local read-only tools (such as `ss` for listeners). It does not run commands typed by the user.
- If a metric cannot be read, that card shows “Unavailable” and the rest of the page still loads.
- If the open server is not this host, the page shows the name and address and the message “This demo only monitors the machine it is running on.” It does not attempt a remote connection.

### Read-only

- The metric view has no control that changes files, services, processes, or network settings on the host.
- Adding and removing rows in the demo server list is the only write action in the UI.

## Pages

1. **Sign in** — username, password, and a single sign-in action.
2. **Servers** — list, add form, remove control, and a link to each server.
3. **Server** — name, address, status, metric cards, and the listening-port table.

Layout: one column on a narrow window, cards in a row on a wide window. Large numbers, plain labels, and units (percent, MiB, bytes, bytes/s). Use a calm, high-contrast style that is readable in a browser on this machine.

## Local setup

Run these steps on this machine from the project directory.

1. Use Python 3.
2. Install Flask (`pip install flask`). Flask includes the password-hash helper used below.
3. Create `config.json` in the project directory:

```json
{
  "username": "admin",
  "password_hash": "<hash>",
  "secret_key": "<long random string>"
}
```

Generate `<hash>` with:

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

4. Start the app bound to this machine (`flask --app app run`).
5. Open the local URL in the browser, sign in as `admin`, add this host, and confirm the metric page updates.

`config.json` and the server-list data file stay on this machine. Do not commit the password hash or the secret key.

## Tech

- Python and Flask.
- Server-rendered pages and one stylesheet. A small script may refresh the metric page every 5 seconds.
- Password check with the hash function above (Werkzeug, PBKDF2).
- Server list stored in a local JSON file.

## Done when

- Sign-in rejects a wrong password and accepts `admin` with the configured hash.
- A signed-out visitor cannot open the server list or a server page.
- A user can add and remove a server, and the list is still there after a restart.
- This host’s page shows CPU, memory, network, and listening ports, and those values change on the 5-second refresh.
- An address that is not this host shows “Not this host” and does not open a remote connection.
- The metric page has no action that changes the host.
