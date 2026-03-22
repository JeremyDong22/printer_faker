<div align="center">

# 🖨️ Printer Faker

**A virtual ESC/POS thermal printer that captures restaurant POS orders and exposes them as a real-time REST API**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![Cloudflare](https://img.shields.io/badge/Cloudflare_Tunnel-F38020?style=flat-square&logo=cloudflare&logoColor=white)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## What it does

Most restaurant POS systems speak to thermal receipt printers over a raw TCP connection using **ESC/POS** — a binary command language developed by Epson in the 1980s. This project replaces that physical printer with a software listener that:

1. **Accepts** incoming TCP connections on port `9100` (the standard ESC/POS port)
2. **Parses** the binary ESC/POS command stream into clean plain-text receipts
3. **Stores** every receipt in an in-memory buffer + SQLite database
4. **Exposes** the data via a Flask REST API on port `5000` with authentication, rate limiting, and SSE streaming
5. **Syncs** orders to Supabase for downstream consumption by dashboards, kitchen displays, or analytics pipelines
6. **Tunnels** securely to the internet via Cloudflare, so cloud services can reach a device sitting on a private restaurant LAN

```
POS Terminal
    │  TCP :9100 (ESC/POS binary)
    ▼
┌─────────────────────────────────────────┐
│           printer_api_service           │
│  ┌──────────────┐  ┌─────────────────┐  │
│  │ ESC/POS      │  │  SQLite + RAM   │  │
│  │ Parser       │→ │  Receipt Store  │  │
│  └──────────────┘  └────────┬────────┘  │
│                             │           │
│  ┌──────────────────────────▼────────┐  │
│  │         Flask REST API :5000      │  │
│  │  /api/health  /api/recent         │  │
│  │  /api/receipts  /api/stream (SSE) │  │
│  └──────────────────────────┬────────┘  │
└─────────────────────────────┼───────────┘
                              │ Cloudflare Tunnel
                              ▼
                    https://<tunnel>.trycloudflare.com
                              │
              ┌───────────────┴──────────────┐
              ▼                              ▼
         Supabase DB               Kitchen Dashboard
```

---

## Quick Start

```bash
# 1. Clone and enter the repo
git clone https://github.com/JeremyDong22/printer_faker.git
cd printer_faker

# 2. Copy and fill in your credentials
cp .env.example .env

# 3. Launch everything
./start_api_service.sh
```

The script handles `uv` installation, dependency setup, and port cleanup automatically. The API will be live at `http://localhost:5000`.

### Expose to the Internet

```bash
./setup_tunnel.sh
```

This starts a Cloudflare Tunnel and prints a public HTTPS URL — no firewall rules, no static IP needed.

### Run as a System Service (Linux)

```bash
sudo ./install_system_service.sh
sudo systemctl start printer-api
sudo systemctl enable printer-api
```

---

## API Reference

All endpoints require authentication — pass either an `Authorization: <password>` header or a `?auth=<password>` query parameter.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service status, uptime, receipt count |
| `GET` | `/api/recent` | Last 10 receipts |
| `GET` | `/api/receipts` | All stored receipts (up to 500) |
| `GET` | `/api/search?no=<id>` | Search by receipt number |
| `GET` | `/api/stream` | **Server-Sent Events** — live receipt stream |

### Example: poll for new orders

```python
import requests

BASE = "https://<your-tunnel>.trycloudflare.com"
AUTH = {"Authorization": "your-password"}

resp = requests.get(f"{BASE}/api/recent", headers=AUTH)
for receipt in resp.json()["receipts"]:
    print(receipt["receipt_no"], receipt["text"])
```

### Example: stream orders in real time

```javascript
const es = new EventSource(
  "https://<tunnel>.trycloudflare.com/api/stream?auth=your-password"
);
es.onmessage = (e) => {
  const order = JSON.parse(e.data);
  console.log("New order:", order.receipt_no);
};
```

---

## Project Layout

```
printer_faker/
│
├── printer_api_service.py      # V1 service — in-memory storage, production-proven
├── printer_api_service_v2.py   # V2 service — SQLite persistence, connection pooling
├── virtual_printer.py          # ESC/POS binary parser → plain text + Chinese support
├── order_processor.py          # Supabase sync, dish-station mapping, retry queue
├── dashboard.py                # Web monitoring dashboard (real-time stats & receipts)
├── wsgi.py                     # Gunicorn entry point
├── gunicorn_config.py          # Worker / timeout configuration
│
├── start_api_service.sh        # One-command launcher (handles deps + port cleanup)
├── setup_tunnel.sh             # Temporary Cloudflare tunnel
├── setup_permanent_tunnel.sh   # Persistent named tunnel
├── install_system_service.sh   # systemd service installer
├── monitor_health.sh           # Watchdog / health probe
├── auto_cleanup.sh             # Hourly receipt pruning cron job
│
├── .env.example                # Required environment variables (copy → .env)
├── requirements.txt            # Python dependencies
│
└── docs/
    ├── API_USAGE.md            # Full API reference with multi-language examples
    ├── API_SETUP_GUIDE.md      # Local dev quickstart
    ├── architecture_analysis.md     # V1 vs V2 design trade-offs
    └── LOCAL_SUPABASE_ARCHITECTURE.md  # Supabase integration deep-dive
```

---

## Configuration

Copy `.env.example` to `.env` and set:

```dotenv
# Authentication
API_PASSWORD=your-strong-password

# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key

# Axiom (optional — structured logging)
AXIOM_TOKEN=your-axiom-token
AXIOM_DATASET=printer-logs

# Storage
DB_PATH=./receipts.db
MAX_MEMORY_RECEIPTS=500
```

---

## V1 vs V2

| | `printer_api_service.py` (V1) | `printer_api_service_v2.py` (V2) |
|--|-------------------------------|----------------------------------|
| Storage | In-memory list | SQLite + memory |
| Concurrency | Threading | ThreadPoolExecutor + semaphores |
| Restart recovery | Receipts lost | Receipts persisted |
| Complexity | Simple | More robust |
| Best for | Dev / testing | Production 24/7 |

---

## How ESC/POS Parsing Works

The `virtual_printer.py` parser processes the raw byte stream command-by-command:

- **`ESC @`** — reset printer state
- **`ESC !`** — set font size / emphasis
- **`ESC a`** — text alignment (left / center / right)
- **`GS !`** — character magnification
- **`ESC E`** — bold on/off
- **`\n` / `\r\n`** — line feeds → buffered text lines
- **Multi-byte Chinese** — GB18030 / GBK sequences decoded to Unicode

Receipt fields (`单号`, `时间`) are extracted from the rendered text via regex after parsing.

---

## Requirements

- Python 3.8+
- [`uv`](https://github.com/astral-sh/uv) (auto-installed by start script)
- A POS system configured to print to a network address on port 9100
- Supabase project (for order sync)
- Cloudflare account (for tunnel — free tier works)

---

## Contributing

Pull requests are welcome. For significant changes, open an issue first to discuss what you'd like to change.

---

<div align="center">
  <sub>Built for real-world restaurant operations · Runs 24/7 on a Raspberry Pi</sub>
</div>
