(function () {
  const root = document.querySelector("[data-metrics]");
  if (!root) {
    return;
  }
  const url = root.getAttribute("data-metrics");
  const interval = Number(root.getAttribute("data-refresh")) || 5000;

  function text(value, suffix) {
    return value + suffix;
  }

  function fillMemory(memory) {
    const node = document.getElementById("memory-value");
    node.replaceChildren();
    if (!memory) {
      node.textContent = "Unavailable";
      return;
    }
    const list = document.createElement("ul");
    list.className = "facts";
    const lines = [
      "Total " + memory.total_mib + " MiB",
      "Used " + memory.used_mib + " MiB",
      "Available " + memory.available_mib + " MiB",
      "Used " + memory.used_percent + "%",
    ];
    lines.forEach(function (line) {
      const item = document.createElement("li");
      item.textContent = line;
      list.appendChild(item);
    });
    node.appendChild(list);
  }

  function fillTable(node, columns, rows, emptyText) {
    node.replaceChildren();
    if (!rows) {
      node.textContent = "Unavailable";
      return;
    }
    if (!rows.length) {
      node.textContent = emptyText;
      return;
    }
    const wrap = document.createElement("div");
    wrap.className = "table-wrap";
    const table = document.createElement("table");
    const head = document.createElement("tr");
    columns.forEach(function (column) {
      const cell = document.createElement("th");
      cell.textContent = column.label;
      head.appendChild(cell);
    });
    const thead = document.createElement("thead");
    thead.appendChild(head);
    const body = document.createElement("tbody");
    rows.forEach(function (row) {
      const line = document.createElement("tr");
      columns.forEach(function (column) {
        const cell = document.createElement("td");
        cell.textContent = column.text(row);
        line.appendChild(cell);
      });
      body.appendChild(line);
    });
    table.appendChild(thead);
    table.appendChild(body);
    wrap.appendChild(table);
    node.appendChild(wrap);
  }

  function render(data) {
    const cpu = document.getElementById("cpu-value");
    cpu.textContent = data.cpu === null || data.cpu === undefined ? "Unavailable" : text(data.cpu, "%");
    fillMemory(data.memory);
    fillTable(
      document.getElementById("network-value"),
      [
        { label: "Name", text: function (row) { return row.name; } },
        { label: "Received", text: function (row) { return row.bytes_received + " bytes"; } },
        { label: "Sent", text: function (row) { return row.bytes_sent + " bytes"; } },
        { label: "Receive", text: function (row) { return row.receive_rate + " bytes/s"; } },
        { label: "Send", text: function (row) { return row.send_rate + " bytes/s"; } },
      ],
      data.network,
      "No interfaces."
    );
    const portsNode = document.getElementById("ports-value");
    if (data.ports && data.ports.length) {
      fillTable(
        portsNode,
        [
          { label: "Protocol", text: function (row) { return row.protocol; } },
          { label: "Address", text: function (row) { return row.address; } },
          { label: "Port", text: function (row) { return row.port; } },
          { label: "Process", text: function (row) { return row.process; } },
          { label: "PID", text: function (row) { return row.pid; } },
        ],
        data.ports,
        "No listening ports."
      );
    } else if (data.ports) {
      portsNode.textContent = "No listening ports.";
    } else {
      portsNode.textContent = "Unavailable";
    }
  }

  function refresh() {
    fetch(url, { headers: { Accept: "application/json" }, credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) {
          return null;
        }
        return response.json();
      })
      .then(function (data) {
        if (!data || data.message) {
          return;
        }
        render(data);
      })
      .catch(function () {});
  }

  window.setInterval(refresh, interval);
})();
