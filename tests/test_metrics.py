import unittest

from metrics import (
    MetricState,
    collect,
    cpu_percent,
    listening_ports,
    network_rates,
    parse_cpu_times,
    parse_meminfo,
    parse_netdev,
    parse_ss,
    read_text,
)


def cpu_line(busy, idle):
    return f"cpu  {busy} 0 0 {idle} 0 0 0 0 0 0\n"


def net_line(name, received, sent):
    columns = [str(received)] + ["0"] * 7 + [str(sent)] + ["0"] * 7
    return f"{name}: {' '.join(columns)}\n"


MEMINFO = "MemTotal: 2048 kB\nMemAvailable: 1024 kB\n"
SS_SAMPLE = (
    'tcp LISTEN 0 128 127.0.0.1:22 0.0.0.0:* users:(("sshd",pid=9,fd=3))\n'
    'udp UNCONN 0 0 [::]:68 [::]:* users:(("dhclient",pid=4,fd=8))\n'
)


class MetricTests(unittest.TestCase):
    def test_parse_cpu_and_memory_samples(self):
        first = parse_cpu_times(cpu_line(10, 90))
        second = parse_cpu_times(cpu_line(20, 100))
        self.assertEqual(cpu_percent(first, second), 50.0)
        memory = parse_meminfo(MEMINFO)
        self.assertEqual(memory["total_mib"], 2.0)
        self.assertEqual(memory["used_mib"], 1.0)
        self.assertEqual(memory["available_mib"], 1.0)
        self.assertEqual(memory["used_percent"], 50.0)

    def test_unreadable_proc_file(self):
        self.assertIsNone(read_text("/tmp/server-monitor-missing-proc"))
        state = MetricState()
        result = collect(
            state,
            read_stat=lambda: None,
            read_meminfo=lambda: MEMINFO,
            read_netdev=lambda: net_line("eth0", 10, 20),
            read_ports=lambda: [],
            now=1,
        )
        self.assertIsNone(result["cpu"])
        self.assertEqual(result["memory"]["total_mib"], 2.0)
        self.assertEqual(result["network"][0]["name"], "eth0")

    def test_network_rate_from_two_samples(self):
        previous = parse_netdev(net_line("eth0", 1000, 2000))
        current = parse_netdev(net_line("eth0", 3000, 5000))
        rows = network_rates(previous, current, 2)
        self.assertEqual(rows[0]["bytes_received"], 3000)
        self.assertEqual(rows[0]["bytes_sent"], 5000)
        self.assertEqual(rows[0]["receive_rate"], 1000.0)
        self.assertEqual(rows[0]["send_rate"], 1500.0)

    def test_ss_samples(self):
        listeners = parse_ss(SS_SAMPLE)
        self.assertEqual(listeners[0]["protocol"], "tcp")
        self.assertEqual(listeners[0]["address"], "127.0.0.1")
        self.assertEqual(listeners[0]["port"], "22")
        self.assertEqual(listeners[0]["process"], "sshd")
        self.assertEqual(listeners[0]["pid"], "9")
        self.assertEqual(listeners[1]["address"], "::")
        scoped = parse_ss("udp UNCONN 0 0 127.0.0.53%lo:53 0.0.0.0:*\n")
        self.assertEqual(scoped[0]["address"], "127.0.0.53")
        self.assertEqual(scoped[0]["port"], "53")
        self.assertEqual(listeners[1]["port"], "68")
        self.assertEqual(parse_ss(""), [])

        def failed(command, **kwargs):
            self.assertEqual(command, ["ss", "-H", "-l", "-n", "-t", "-u", "-p"])
            self.assertNotIn("shell", kwargs) or self.assertFalse(kwargs.get("shell"))
            return type("Result", (), {"returncode": 1, "stdout": ""})()

        self.assertIsNone(listening_ports(run=failed))


if __name__ == "__main__":
    unittest.main()
