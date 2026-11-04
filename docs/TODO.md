# Implementation TODO

Local demo on this Linux machine. Do one increment at a time, including its security and documentation boxes, before starting the next.

Details live in [requirements.md](requirements.md).

## 1. Project initialization and basic UI

- [x] Add `requirements.txt` with Flask
- [x] Add `app.py` that serves one page
- [x] Add one stylesheet and a page shell: title, short intro, and an empty content area
- [x] Add `.gitignore` for the virtualenv, `__pycache__`, `config.json`, and the server-list file
- [x] Open the page in a browser on this machine and confirm it renders

**Security**

- [x] Run the app on localhost
- [x] Leave secrets out of the repo; `.gitignore` covers `config.json`
- [x] The page takes no input and runs no host commands

**Documentation**

- [x] Add `README.md` with the local steps: virtualenv, install, start, open the local URL

## 2. Sign-in and unit tests

- [x] Load `username`, `password_hash`, and `secret_key` from `config.json`
- [x] Add a sign-in page with username, password, and one submit button
- [x] Accept only `admin`, checked with Werkzeug’s password hash
- [x] On success, start a session and open a placeholder servers page
- [x] On failure, stay on the sign-in page and show one error line
- [x] Add sign-out, which ends the session and returns to sign-in
- [x] Add unit tests for a missing config, a wrong password, a correct password, and sign-out

**Security**

- [x] Compare passwords with Werkzeug’s hash check
- [x] Keep the password out of logs, templates, and git; tests create a hash in memory
- [x] Set the session cookie HTTP-only and SameSite strict
- [x] Use one error message for a bad username or password

**Documentation**

- [x] Document the hash command and the `config.json` fields in `README.md`

## 3. CI/CD with GitHub Actions

- [x] Add `.github/workflows/test.yml` to install dependencies and run the unit tests on push and pull request
- [x] Run the workflow file’s commands locally once (`pip install -r requirements.txt` and the test command) so the job matches this machine

**Security**

- [x] The workflow uses no repository secrets and does not read `config.json`
- [x] Tests still generate their own password hash in memory
- [x] The workflow runs tests only; starting the demo stays a local command

**Documentation**

- [x] Note in `README.md` that GitHub Actions runs the tests, and the app is started on this machine

## 4. Require sign-in

- [x] Send signed-out visitors from the servers page and later server pages back to sign-in
- [x] Leave the sign-in page available without a session
- [x] Add a unit test that a signed-out request to the servers page is redirected

**Security**

- [x] Refuse to start the app when `secret_key` is missing or empty
- [x] Keep the session check on the server for every page after sign-in

**Documentation**

- [x] Note in `README.md` that the server list opens only after sign-in

## 5. Empty server list

- [x] Replace the placeholder with a servers page
- [x] Show a short prompt when the list is empty
- [x] Show sign-out on the page
- [x] Add a unit test that a signed-in user sees the empty prompt

**Security**

- [x] Render the page with Jinja autoescape on
- [x] Add no control that changes the host

**Documentation**

- [x] Note the empty-list prompt in `README.md`

## 6. Add a server

- [x] Add a form for display name and address; both are required
- [x] Save the entry in a local JSON file with a generated id
- [x] Show the new row (name and address) on the servers page
- [x] Add unit tests for a missing field and for a successful add

**Security**

- [x] Accept the address as stored text; do not pass it to a shell or open a connection
- [x] Limit name and address length
- [x] POST the form with a session CSRF token
- [x] Escape name and address when rendering

**Documentation**

- [x] Document the add fields and the JSON file name in `README.md`

## 7. Remove a server

- [x] Add a remove control on each row
- [x] Delete that id from the JSON file and leave the host unchanged
- [x] Keep the list after an app restart
- [x] Add unit tests for remove, for an unknown id, and for the list surviving a new load

**Security**

- [x] Delete only by id from the fixed JSON path
- [x] Ignore a remove id that is not in the file
- [x] Require the same CSRF token on remove

**Documentation**

- [x] Note in `README.md` that remove updates the demo list only

## 8. Mark this host

- [x] Treat `localhost`, `127.0.0.1`, `::1`, this machine’s hostname, and its interface addresses as this host
- [x] Show “This host” or “Not this host” on each row
- [x] Add unit tests with a fixed set of local addresses, including one match and one non-match

**Security**

- [x] Compare the saved address to local names only
- [x] Do not connect to an address that is not this host

**Documentation**

- [x] List the addresses that count as this host in `README.md`

## 9. Server page

- [x] Link each row to its own page
- [x] Show name, address, and status
- [x] For “Not this host,” show “This demo only monitors the machine it is running on.” and no metric cards
- [x] For “This host,” show four empty cards: CPU, memory, network, and ports
- [x] Add a unit test for each status

**Security**

- [x] Look up the server by id from the JSON file
- [x] Unknown ids return the servers page
- [x] The page has no action that changes the host

**Documentation**

- [x] Describe the two server-page states in `README.md`

## 10. CPU and memory

- [x] Read CPU use from `/proc/stat` and show one percentage
- [x] Read memory from `/proc/meminfo` and show total, used, available, and used percent
- [x] Add unit tests that parse sample `/proc` text, including a file that cannot be read

**Security**

- [x] Read only those fixed paths
- [x] When a read fails, show “Unavailable” on that card

**Documentation**

- [x] State the CPU and memory fields and their units in `README.md`

## 11. Network

- [x] Read interface counters from `/proc/net/dev`
- [x] Show name, bytes received, bytes sent, and the rate since the last refresh
- [x] Add unit tests that parse sample counters and compute a rate from two samples

**Security**

- [x] Read only `/proc/net/dev`
- [x] Keep the previous sample in memory for the rate
- [x] When the file cannot be read, show “Unavailable” on the network card

**Documentation**

- [x] State the network fields and units (bytes and bytes/s) in `README.md`

## 12. Listening ports

- [x] Read listening TCP and UDP ports with a fixed local command (`ss`), using an argument list and no shell
- [x] Show protocol, local address, port, process name, and process id
- [x] Add unit tests that parse sample `ss` output, including an empty list and a failed command

**Security**

- [x] Run only that fixed command; never include typed input
- [x] When the command fails, show “Unavailable” on the ports card

**Documentation**

- [x] State that port data comes from a read-only `ss` command in `README.md`

## 13. Refresh

- [x] Refresh the open server page every 5 seconds
- [x] Update the four cards in place
- [x] Keep a failed card on “Unavailable” while the other cards still update
- [x] Add a unit test that the page (or its metric response) includes each card and the 5-second refresh

**Security**

- [x] Refresh with a same-origin GET that returns data for the signed-in session
- [x] Return the same “Not this host” message for any other address, with no remote call

**Documentation**

- [x] Note the 5-second refresh in `README.md`

## 14. Demo check

- [x] Walk the “Done when” list in `requirements.md` on this machine
- [x] Confirm the metric page has no control that changes files, services, processes, or network settings
- [x] Confirm `config.json` and the server-list file are untracked

**Security**

- [x] Review each increment’s security boxes and tick any that are still open
- [x] Confirm logs and test output contain no password or secret key

**Documentation**

- [x] Match `README.md` to the steps that actually start the app locally
