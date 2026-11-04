import ipaddress
import json
import os
import socket
import struct
import uuid
from pathlib import Path

NAME_LIMIT = 80
ADDRESS_LIMIT = 253
ADD_REQUIRED = "Display name and address are required."
ADD_TOO_LONG = "Display name or address is too long."
NOT_THIS_HOST = "This demo only monitors the machine it is running on."
EMPTY_PROMPT = "No servers yet. Add a server to begin."


def load_servers(path):
    file_path = Path(path)
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    servers = data.get("servers") if isinstance(data, dict) else None
    if not isinstance(servers, list):
        return []
    cleaned = []
    for server in servers:
        if not isinstance(server, dict):
            continue
        server_id = server.get("id")
        name = server.get("name")
        address = server.get("address")
        if isinstance(server_id, str) and isinstance(name, str) and isinstance(address, str):
            cleaned.append({"id": server_id, "name": name, "address": address})
    return cleaned


def save_servers(path, servers):
    file_path = Path(path)
    payload = json.dumps({"servers": servers}, indent=2) + "\n"
    temporary = file_path.with_suffix(".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(file_path)


def add_server(path, name, address):
    name = (name or "").strip()
    address = (address or "").strip()
    if not name or not address:
        return load_servers(path), ADD_REQUIRED
    if len(name) > NAME_LIMIT or len(address) > ADDRESS_LIMIT:
        return load_servers(path), ADD_TOO_LONG
    servers = load_servers(path)
    servers.append({"id": uuid.uuid4().hex, "name": name, "address": address})
    save_servers(path, servers)
    return servers, None


def remove_server(path, server_id):
    servers = load_servers(path)
    kept = [server for server in servers if server["id"] != server_id]
    if len(kept) != len(servers):
        save_servers(path, kept)
    return kept


def find_server(path, server_id):
    for server in load_servers(path):
        if server["id"] == server_id:
            return server
    return None


def host_label(address, names):
    known = {normalize_address(name) for name in names}
    if normalize_address(address) in known:
        return "This host"
    return "Not this host"


def normalize_address(value):
    text = value.strip().lower()
    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        return text


def local_names():
    names = {"localhost", "127.0.0.1", "::1"}
    hostname = socket.gethostname()
    if hostname:
        names.add(hostname)
    names.update(_ipv4_addresses())
    names.update(_ipv6_addresses())
    return names


def _ipv4_addresses():
    found = set()
    try:
        interfaces = os.listdir("/sys/class/net")
    except OSError:
        return found
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        for name in interfaces:
            try:
                packed = fcntl_ioctl(sock, name)
            except OSError:
                continue
            found.add(socket.inet_ntoa(packed[20:24]))
    finally:
        sock.close()
    return found


def fcntl_ioctl(sock, name):
    import fcntl

    return fcntl.ioctl(
        sock.fileno(),
        0x8915,
        struct.pack("256s", name.encode("utf-8")[:15]),
    )


def _ipv6_addresses():
    found = set()
    try:
        text = Path("/proc/net/if_inet6").read_text(encoding="utf-8")
    except OSError:
        return found
    for line in text.splitlines():
        parts = line.split()
        if not parts or len(parts[0]) != 32:
            continue
        try:
            found.add(str(ipaddress.IPv6Address(int(parts[0], 16))))
        except ValueError:
            continue
    return found
