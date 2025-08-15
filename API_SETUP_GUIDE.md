# Printer API Service Setup Guide

## Quick Start

### 1. Start the API Service

In Terminal 1:
```bash
./start_api_service.sh
```

This will:
- Start TCP listener on port 9100 (for POS machine)
- Start API server on port 5000
- Create logs in `logs/api_debug.log`

### 2. Setup Internet Access (Cloudflare Tunnel)

In Terminal 2:
```bash
./setup_tunnel.sh
```

This will:
- Install cloudflared if needed
- Create a public URL like `https://random-name.trycloudflare.com`
- Keep this terminal open to maintain the tunnel

**Copy the URL it gives you** - this is your public API endpoint!

## API Endpoints

Once running, you can access:

- `GET /api/health` - Check service status
- `GET /api/recent` - Last 10 receipts
- `GET /api/receipts` - All receipts (max 500)
- `GET /api/search?no=240815001` - Search by receipt number
- `GET /api/stream` - Real-time SSE stream

## Testing

### Local Testing
```bash
# Test with the included client
python test_api_client.py

# Or use curl
curl http://localhost:5000/api/health
curl http://localhost:5000/api/recent
```

### Web Interface
Open browser to: http://localhost:5000

### From Your Cloud App

JavaScript example to connect to the real-time stream:
```javascript
// Replace with your tunnel URL
const API_URL = 'https://your-tunnel.trycloudflare.com';

// Connect to SSE stream
const eventSource = new EventSource(`${API_URL}/api/stream`);

eventSource.onmessage = (event) => {
    const receipt = JSON.parse(event.data);
    
    if (receipt.type === 'connected') {
        console.log('Connected to printer API');
    } else {
        console.log('New receipt:', {
            receipt_no: receipt.receipt_no,
            timestamp: receipt.timestamp,
            text: receipt.plain_text
        });
        
        // Process the receipt...
    }
};

eventSource.onerror = (error) => {
    console.error('Stream error:', error);
};
```

Python example:
```python
import requests
import json

# Get recent receipts
response = requests.get('https://your-tunnel.trycloudflare.com/api/recent')
receipts = response.json()

# Stream real-time receipts
response = requests.get('https://your-tunnel.trycloudflare.com/api/stream', stream=True)
for line in response.iter_lines():
    if line and line.startswith(b'data: '):
        data = json.loads(line[6:])
        print(f"New receipt: {data['receipt_no']}")
```

## Receipt JSON Format

Each receipt has this structure:
```json
{
    "id": "unique-uuid",
    "receipt_no": "240815001",      // Extracted from 单号
    "timestamp": "2024-08-15 17:51:01",  // Extracted from 时间
    "plain_text": "Full receipt text here..."
}
```

## Logs

Debug logs are stored in `logs/api_debug.log`
- Automatically rotates at 10MB
- Keeps 1 backup file
- Contains connection info, errors, receipt IDs

## Troubleshooting

### Port 9100 Already in Use
```bash
# Check what's using port 9100
sudo lsof -i :9100

# Kill the process if needed
sudo kill -9 <PID>
```

### Tunnel Not Working
1. Make sure API service is running first
2. Check firewall allows outbound HTTPS
3. Try restarting the tunnel

### No Receipts Showing
1. Check POS is sending to port 9100
2. Check logs: `tail -f logs/api_debug.log`
3. Test with virtual_printer.py to send test data

## Architecture

```
POS Machine
    ↓ (TCP 9100)
Your Local Machine [printer_api_service.py]
    ↓ (Cloudflare Tunnel)
Internet (https://xxx.trycloudflare.com)
    ↓
Your Cloud Application
```

## Notes

- Service keeps last 500 receipts in memory
- No files are saved (API only)
- Tunnel URL changes each time (use named tunnel for permanent URL)
- SSE stream supports multiple concurrent clients