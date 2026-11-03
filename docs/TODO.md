# Implementation TODO

Local demo on this Linux machine. Do one increment at a time, including its security and documentation boxes, before starting the next.

Details live in [requirements.md](requirements.md).

## 1. Project initialization and basic UI

- [ ] Add `requirements.txt` with Flask
- [ ] Add `app.py` that serves one page
- [ ] Add one stylesheet and a page shell: title, short intro, and an empty content area
- [ ] Add `.gitignore` for the virtualenv, `__pycache__`, `config.json`, and the server-list file
- [ ] Open the page in a browser on this machine and confirm it renders

**Security**

- [ ] Run the app on localhost
- [ ] Leave secrets out of the repo; `.gitignore` covers `config.json`
- [ ] The page takes no input and runs no host commands

**Documentation**

- [ ] Add `README.md` with the local steps: virtualenv, install, start, open the local URL

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

- [ ] Add `.github/workflows/test.yml` to install dependencies and run the unit tests on push and pull request
- [ ] Run the workflow file’s commands locally once (`pip install -r requirements.txt` and the test command) so the job matches this machine

**Security**

- [ ] The workflow uses no repository secrets and does not read `config.json`
- [ ] Tests still generate their own password hash in memory
- [ ] The workflow runs tests only; starting the demo stays a local command

**Documentation**

- [ ] Note in `README.md` that GitHub Actions runs the tests, and the app is started on this machine

## 4. Require sign-in

- [ ] Send signed-out visitors from the servers page and later server pages back to sign-in
- [ ] Leave the sign-in page available without a session
- [ ] Add a unit test that a signed-out request to the servers page is redirected

**Security**

- [ ] Refuse to start the app when `secret_key` is missing or empty
- [ ] Keep the session check on the server for every page after sign-in

**Documentation**

- [ ] Note in `README.md` that the server list opens only after sign-in

## 5. Empty server list

- [ ] Replace the placeholder with a servers page
- [ ] Show a short prompt when the list is empty
- [ ] Show sign-out on the page
- [ ] Add a unit test that a signed-in user sees the empty prompt

**Security**

- [ ] Render the page with Jinja autoescape on
- [ ] Add no control that changes the host

**Documentation**

- [ ] Note the empty-list prompt in `README.md`

## 6. Add a server

- [ ] Add a form for display name and address; both are required
- [ ] Save the entry in a local JSON file with a generated id
- [ ] Show the new row (name and address) on the servers page
- [ ] Add unit tests for a missing field and for a successful add

**Security**

- [ ] Accept the address as stored text; do not pass it to a shell or open a connection
- [ ] Limit name and address length
- [ ] POST the form with a session CSRF token
- [ ] Escape name and address when rendering

**Documentation**

- [ ] Document the add fields and the JSON file name in `README.md`

## 7. Remove a server

- [ ] Add a remove control on each row
- [ ] Delete that id from the JSON file and leave the host unchanged
- [ ] Keep the list after an app restart
- [ ] Add unit tests for remove, for an unknown id, and for the list surviving a new load

**Security**

- [ ] Delete only by id from the fixed JSON path
- [ ] Ignore a remove id that is not in the file
- [ ] Require the same CSRF token on remove

**Documentation**

- [ ] Note in `README.md` that remove updates the demo list only

## 8. Mark this host

- [ ] Treat `localhost`, `127.0.0.1`, `::1`, this machine’s hostname, and its interface addresses as this host
- [ ] Show “This host” or “Not this host” on each row
- [ ] Add unit tests with a fixed set of local addresses, including one match and one non-match

**Security**

- [ ] Compare the saved address to local names only
- [ ] Do not connect to an address that is not this host

**Documentation**

- [ ] List the addresses that count as this host in `README.md`

## 9. Server page

- [ ] Link each row to its own page
- [ ] Show name, address, and status
- [ ] For “Not this host,” show “This demo only monitors the machine it is running on.” and no metric cards
- [ ] For “This host,” show four empty cards: CPU, memory, network, and ports
- [ ] Add a unit test for each status

**Security**

- [ ] Look up the server by id from the JSON file
- [ ] Unknown ids return the servers page
- [ ] The page has no action that changes the host

**Documentation**

- [ ] Describe the two server-page states in `README.md`

## 10. CPU and memory

- [ ] Read CPU use from `/proc/stat` and show one percentage
- [ ] Read memory from `/proc/meminfo` and show total, used, available, and used percent
- [ ] Add unit tests that parse sample `/proc` text, including a file that cannot be read

**Security**

- [ ] Read only those fixed paths
- [ ] When a read fails, show “Unavailable” on that card

**Documentation**

- [ ] State the CPU and memory fields and their units in `README.md`

## 11. Network

- [ ] Read interface counters from `/proc/net/dev`
- [ ] Show name, bytes received, bytes sent, and the rate since the last refresh
- [ ] Add unit tests that parse sample counters and compute a rate from two samples

**Security**

- [ ] Read only `/proc/net/dev`
- [ ] Keep the previous sample in memory for the rate
- [ ] When the file cannot be read, show “Unavailable” on the network card

**Documentation**

- [ ] State the network fields and units (bytes and bytes/s) in `README.md`

## 12. Listening ports

- [ ] Read listening TCP and UDP ports with a fixed local command (`ss`), using an argument list and no shell
- [ ] Show protocol, local address, port, process name, and process id
- [ ] Add unit tests that parse sample `ss` output, including an empty list and a failed command

**Security**

- [ ] Run only that fixed command; never include typed input
- [ ] When the command fails, show “Unavailable” on the ports card

**Documentation**

- [ ] State that port data comes from a read-only `ss` command in `README.md`

## 13. Refresh

- [ ] Refresh the open server page every 5 seconds
- [ ] Update the four cards in place
- [ ] Keep a failed card on “Unavailable” while the other cards still update
- [ ] Add a unit test that the page (or its metric response) includes each card and the 5-second refresh

**Security**

- [ ] Refresh with a same-origin GET that returns data for the signed-in session
- [ ] Return the same “Not this host” message for any other address, with no remote call

**Documentation**

- [ ] Note the 5-second refresh in `README.md`

## 14. Demo check

- [ ] Walk the “Done when” list in `requirements.md` on this machine
- [ ] Confirm the metric page has no control that changes files, services, processes, or network settings
- [ ] Confirm `config.json` and the server-list file are untracked

**Security**

- [ ] Review each increment’s security boxes and tick any that are still open
- [ ] Confirm logs and test output contain no password or secret key

**Documentation**

- [ ] Match `README.md` to the steps that actually start the app locally
