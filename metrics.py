import os
import re
import subprocess
from pathlib import Path

STAT_PATH = "/proc/stat"
MEMINFO_PATH = "/proc/meminfo"
NETDEV_PATH = "/proc/net/dev"
SS_COMMAND = ["ss", "-H", "-l", "-n", "-t", "-u", "-p"]
USERS = re.compile(r'users:\(\("(?P<name>[^"]*)",pid=(?P<pid>\d+)')


class MetricState:
    def __init__(self):
        self.cpu = None
        self.net = None
        self.net_at = None


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return None


def read_stat():
    return read_text(STAT_PATH)


def read_meminfo():
    return read_text(MEMINFO_PATH)


def read_netdev():
    return read_text(NETDEV_PATH)


def parse_cpu_times(text):
    for line in text.splitlines():
        if line.startswith("cpu "):
            numbers = [int(part) for part in line.split()[1:]]
            idle = numbers[3] + (numbers[4] if len(numbers) > 4 else 0)
            return {"idle": idle, "total": sum(numbers)}
    return None


def cpu_percent(previous, current):
    total_delta = current["total"] - previous["total"]
    idle_delta = current["idle"] - previous["idle"]
    if total_delta <= 0:
        return 0.0
    return round((total_delta - idle_delta) * 100 / total_delta, 1)


def parse_meminfo(text):
    values = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        parts = rest.split()
        if not parts:
            continue
        try:
            values[key] = int(parts[0])
        except ValueError:
            continue
    if "MemTotal" not in values or "MemAvailable" not in values or values["MemTotal"] <= 0:
        return None
    total = values["MemTotal"]
    available = values["MemAvailable"]
    used = max(total - available, 0)
    return {
        "total_mib": round(total / 1024, 1),
        "used_mib": round(used / 1024, 1),
        "available_mib": round(available / 1024, 1),
        "used_percent": round(used * 100 / total, 1),
    }


def parse_netdev(text):
    rows = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        columns = rest.split()
        if len(columns) < 9:
            continue
        try:
            rows[name.strip()] = {"rx": int(columns[0]), "tx": int(columns[8])}
        except ValueError:
            continue
    return rows


def network_rates(previous, current, elapsed):
    rows = []
    for name in sorted(current):
        received = current[name]["rx"]
        sent = current[name]["tx"]
        if previous and name in previous and elapsed and elapsed > 0:
            receive_rate = max(received - previous[name]["rx"], 0) / elapsed
            send_rate = max(sent - previous[name]["tx"], 0) / elapsed
        else:
            receive_rate = 0.0
            send_rate = 0.0
        rows.append(
            {
                "name": name,
                "bytes_received": received,
                "bytes_sent": sent,
                "receive_rate": round(receive_rate, 1),
                "send_rate": round(send_rate, 1),
            }
        )
    return rows


def parse_ss(text):
    listeners = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[0] not in {"tcp", "udp"}:
            continue
        address, port = _split_endpoint(parts[4])
        match = USERS.search(line)
        listeners.append(
            {
                "protocol": parts[0],
                "address": address,
                "port": port,
                "process": match.group("name") if match else "",
                "pid": match.group("pid") if match else "",
            }
        )
    return listeners


def listening_ports(run=subprocess.run):
    environment = os.environ.copy()
    environment["COLUMNS"] = "512"
    try:
        result = run(
            list(SS_COMMAND),
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return parse_ss(result.stdout)


def collect(state, read_stat, read_meminfo, read_netdev, read_ports, now):
    stat_text = read_stat()
    mem_text = read_meminfo()
    net_text = read_netdev()
    ports = read_ports()

    cpu_value = None
    if stat_text is not None:
        current = parse_cpu_times(stat_text)
        if current is not None:
            if state.cpu is None:
                total = current["total"]
                cpu_value = round((total - current["idle"]) * 100 / total, 1) if total else 0.0
            else:
                cpu_value = cpu_percent(state.cpu, current)
            state.cpu = current

    memory = parse_meminfo(mem_text) if mem_text is not None else None

    network = None
    if net_text is not None:
        current_net = parse_netdev(net_text)
        elapsed = None if state.net_at is None else now - state.net_at
        network = network_rates(state.net, current_net, elapsed)
        state.net = current_net
        state.net_at = now

    return {
        "cpu": cpu_value,
        "memory": memory,
        "network": network,
        "ports": ports,
    }


def _split_endpoint(endpoint):
    if endpoint.startswith("["):
        address, _, port = endpoint.rpartition(":")
        address = address.strip("[]")
    else:
        address, _, port = endpoint.rpartition(":")
    if "%" in address:
        address = address.split("%", 1)[0]
    return address, port
