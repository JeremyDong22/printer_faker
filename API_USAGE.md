# Printer API Service - Secure Usage Guide

## 🔐 Authentication Required

All API endpoints require authentication using the password: `smartbcg`

### Authentication Methods:

**Method 1: Authorization Header (Recommended)**
```bash
curl -H "Authorization: smartbcg" https://printer.smartice.ai/api/health
```

**Method 2: URL Parameter**
```bash
curl "https://printer.smartice.ai/api/recent?auth=smartbcg"
```

## 📡 API Endpoints

### 1. Health Check
Check if the service is running and get statistics.

```bash
curl -H "Authorization: smartbcg" https://printer.smartice.ai/api/health
```

Response:
```json
{
  "status": "ok",
  "receipts_count": 42,
  "total_received": 156,
  "parse_errors": 0,
  "uptime_seconds": 3600,
  "last_receipt": "2025-08-15T21:30:00"
}
```

### 2. Recent Receipts
Get the last 10 receipts.

```bash
curl -H "Authorization: smartbcg" https://printer.smartice.ai/api/recent
```

Response:
```json
[
  {
    "id": "uuid-here",
    "receipt_no": "140877542508150062",
    "timestamp": "2025-08-15 21:36:57",
    "plain_text": "Full receipt text..."
  }
]
```

### 3. All Receipts
Get all stored receipts (max 500).

```bash
curl -H "Authorization: smartbcg" https://printer.smartice.ai/api/receipts
```

### 4. Search by Receipt Number
Search for receipts by receipt number (单号).

```bash
curl -H "Authorization: smartbcg" "https://printer.smartice.ai/api/search?no=140877542508150062"
```

### 5. Real-time Stream (SSE)
Connect to real-time receipt stream using Server-Sent Events.

```bash
curl -H "Authorization: smartbcg" https://printer.smartice.ai/api/stream
```

## 💻 Client Integration Examples

### JavaScript/Node.js
```javascript
const API_URL = 'https://printer.smartice.ai';
const API_PASSWORD = 'smartbcg';

// Fetch recent receipts
fetch(`${API_URL}/api/recent`, {
  headers: {
    'Authorization': API_PASSWORD
  }
})
.then(res => res.json())
.then(receipts => {
  console.log('Recent receipts:', receipts);
});

// Real-time stream
const eventSource = new EventSource(`${API_URL}/api/stream?auth=${API_PASSWORD}`);
eventSource.onmessage = (event) => {
  const receipt = JSON.parse(event.data);
  console.log('New receipt:', receipt);
};
```

### Python
```python
import requests
import json

API_URL = 'https://printer.smartice.ai'
API_PASSWORD = 'smartbcg'

# Get recent receipts
response = requests.get(
    f'{API_URL}/api/recent',
    headers={'Authorization': API_PASSWORD}
)
receipts = response.json()

# Search for specific receipt
response = requests.get(
    f'{API_URL}/api/search',
    params={'no': '140877542508150062'},
    headers={'Authorization': API_PASSWORD}
)
results = response.json()

# Stream real-time receipts
response = requests.get(
    f'{API_URL}/api/stream',
    headers={'Authorization': API_PASSWORD},
    stream=True
)
for line in response.iter_lines():
    if line and line.startswith(b'data: '):
        receipt = json.loads(line[6:])
        print(f"New receipt: {receipt['receipt_no']}")
```

### PHP
```php
<?php
$apiUrl = 'https://printer.smartice.ai';
$apiPassword = 'smartbcg';

// Get recent receipts
$ch = curl_init("$apiUrl/api/recent");
curl_setopt($ch, CURLOPT_HTTPHEADER, ["Authorization: $apiPassword"]);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
$receipts = json_decode($response, true);
curl_close($ch);

foreach ($receipts as $receipt) {
    echo "Receipt No: " . $receipt['receipt_no'] . "\n";
    echo "Time: " . $receipt['timestamp'] . "\n";
    echo "---\n";
}
?>
```

## 📊 Receipt Data Format

Each receipt contains:

```json
{
  "id": "unique-uuid",
  "receipt_no": "140877542508150062",  // Extracted 单号
  "timestamp": "2025-08-15 21:36:57",   // Extracted 时间
  "plain_text": "Full plain text of the receipt..."
}
```

## 🔧 System Service Management

The API runs as a system service and starts automatically on boot.

### Check Service Status
```bash
sudo systemctl status printer-api
```

### Restart Service
```bash
sudo systemctl restart printer-api
```

### View Logs
```bash
sudo journalctl -u printer-api -f
```

### Stop Service
```bash
sudo systemctl stop printer-api
```

## 🌐 Architecture

```
POS Machine (Local Network)
    ↓ TCP Port 9100
Printer API Service (Your Server)
    ↓ Cloudflare Tunnel
Internet (https://printer.smartice.ai)
    ↓ HTTPS + Auth
Your Cloud Application
```

## 🛡️ Security Notes

1. **Password Protection**: All endpoints require authentication
2. **HTTPS Only**: Traffic encrypted via Cloudflare
3. **Rate Limiting**: Cloudflare provides DDoS protection
4. **Local Network**: POS connection is local only (port 9100)

## ⚠️ Important

- Keep the password `smartbcg` secure
- Don't expose port 9100 to the internet
- Monitor logs regularly for suspicious activity
- The service stores last 500 receipts in memory

## 📞 Support

For issues or questions, check:
- Service logs: `/home/smartahc/smartice/printer_faker/logs/`
- Debug log: `logs/api_debug.log`
- System journal: `sudo journalctl -u printer-api`