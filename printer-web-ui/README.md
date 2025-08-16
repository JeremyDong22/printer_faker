# Printer API Web UI Dashboard

A comprehensive web interface for the Printer API Service at https://printer.smartice.ai/

## 📋 Overview

This web UI provides three different interfaces to monitor and interact with the printer API service:

1. **List View** (`index.html`) - Traditional receipt listing with real-time updates
2. **Tables View** (`tables.html`) - Restaurant table-based organization 
3. **Printers View** (`printers.html`) - Processing unit management by printer type

## 🔐 Authentication

All interfaces use the API key: `smartbcg`

The API endpoints are protected and require authentication via:
- **Authorization header**: `Authorization: smartbcg`
- **URL parameter**: `?auth=smartbcg`

## 🚀 Features

### Common Features (All Interfaces)
- **Real-time streaming** via Server-Sent Events (SSE)
- **Responsive design** with Tailwind CSS
- **Live status indicators** and connection monitoring
- **Cross-interface navigation**
- **Health monitoring** with auto-refresh
- **Error handling** and notifications

### 1. List View Interface (`index.html`)
- **Receipt timeline** with chronological display
- **Search functionality** by receipt number
- **Receipt detail modal** with full content
- **Copy and download** capabilities
- **Health statistics** dashboard

### 2. Tables Interface (`tables.html`)
- **Table-based organization** for restaurant orders
- **Grid and floor plan** layouts
- **Table status tracking** (Empty, Occupied, Pending, Ready)
- **Order timeline** per table
- **Dish extraction** and categorization
- **Table management** actions (Mark Ready, Clear Table)

### 3. Printers Interface (`printers.html`)
- **Processing unit simulation** for different printer types:
  - Kitchen (Hot Food, Cold Prep)
  - Bar (Main Bar, Coffee Station)
  - Receipt (Cashier, Kitchen)
  - Dessert Station
- **Queue management** with priority handling
- **Performance metrics** and utilization tracking
- **Real-time job processing** simulation
- **Printer control** actions (Enable/Disable, Test Print, Clear Queue)

## 🔧 Technical Implementation

### API Integration
```javascript
const API_CONFIG = {
    baseUrl: 'https://printer.smartice.ai',
    apiKey: 'smartbcg',
    endpoints: {
        health: '/api/health',
        recent: '/api/recent',
        receipts: '/api/receipts',
        search: '/api/search',
        stream: '/api/stream'
    }
};
```

### Real-time Streaming
- Uses **Server-Sent Events** for live updates
- Automatic reconnection on connection loss
- Real-time data processing and UI updates

### Data Processing

#### Tables Interface
- **Table extraction** from receipt content using pattern matching
- **Dish categorization** and routing logic
- **Status management** based on order timing

#### Printers Interface
- **Smart job routing** based on dish types:
  - Salads → Cold Kitchen
  - Drinks → Bar stations
  - Desserts → Dessert station
  - Hot food → Main kitchen
- **Priority handling** for urgent orders
- **Processing time estimation** by dish complexity

### UI Components
- **Modern gradient designs** with hover effects
- **Real-time animations** and status indicators
- **Modal systems** for detailed views
- **Responsive grid layouts**
- **Performance overlays** and statistics

## 📁 File Structure

```
printer-web-ui/
├── index.html          # Main receipt list interface
├── app.js             # List interface logic
├── tables.html        # Restaurant tables interface  
├── tables.js          # Tables interface logic
├── printers.html      # Printer units interface
├── printers.js        # Printers interface logic
└── README.md          # This documentation
```

## 🎯 Usage Instructions

### 1. Setup
1. Download all files to a web server directory
2. Ensure the API service is running at `https://printer.smartice.ai`
3. Open any of the HTML files in a web browser

### 2. Navigation
- Use the **top navigation bar** to switch between interfaces
- Each interface maintains its own real-time connection
- **Status indicators** show connection health

### 3. Real-time Monitoring
1. Click **"Start Stream"** / **"Start Live Updates"** / **"Start Monitor"**
2. Watch for new receipts appearing with animations
3. Observe automatic data processing and categorization

### 4. Interface-Specific Features

#### List View
- Browse receipts chronologically
- Use search to find specific receipt numbers
- Click receipts to view full details
- Copy or download receipt content

#### Tables View
- Monitor table status and orders
- Switch between Grid and Floor Plan layouts
- Click tables to see order details and timeline
- Mark tables as ready or clear them

#### Printers View
- Monitor printer queue lengths and utilization
- View processing performance metrics
- Manage individual printer queues
- Send test prints and control printer status

## 🔍 Data Flow

1. **POS System** → TCP Port 9100 → **Printer API Service**
2. **API Service** → **REST Endpoints** + **SSE Stream**
3. **Web UI** → **Real-time Updates** → **Smart Categorization**
4. **Processed Data** → **Interface-Specific Views**

## 🎨 Design Features

- **Gradient color schemes** for visual hierarchy
- **Real-time animations** for new data
- **Status-based color coding**:
  - Green: Online/Ready
  - Orange: Pending/Processing  
  - Red: Offline/Error
  - Blue: Active/Selected
- **Glass morphism effects** for modern UI
- **Responsive breakpoints** for mobile compatibility

## 🛠️ Customization

### Adding New Printer Types
Modify the `printerConfigs` array in `printers.js`:

```javascript
{
    id: 'new-printer',
    name: 'New Printer Type',
    type: 'custom',
    location: 'Custom Location',
    description: 'Custom description',
    capacity: 30,
    status: 'online'
}
```

### Customizing Table Extraction
Modify the `extractTableInfo()` function in `tables.js` to match your receipt format patterns.

### Styling Changes
All interfaces use Tailwind CSS classes and custom CSS variables for easy theming.

## 📱 Browser Compatibility

- **Modern browsers** with ES6+ support
- **Server-Sent Events** support required
- **WebSocket fallback** not implemented (SSE only)

## 🔧 Troubleshooting

### Connection Issues
1. Check API service status at https://printer.smartice.ai/api/health
2. Verify authentication key is correct
3. Check browser console for CORS errors
4. Ensure SSL/HTTPS connectivity

### Performance Issues
1. Limit concurrent connections (one per interface)
2. Clear browser cache if data seems stale
3. Check network connectivity and firewall settings

### Data Not Appearing
1. Verify POS system is sending to port 9100
2. Check if API service is processing receipts
3. Restart live streaming connections
4. Check for JavaScript console errors

## 📄 License

This web UI is designed specifically for the printer_faker API service and uses the authentication key `smartbcg` for secure access.

## 🤝 Support

For issues related to:
- **API connectivity**: Check the printer_faker service logs
- **Receipt processing**: Verify ESC/POS data format
- **UI bugs**: Check browser console for JavaScript errors
- **Feature requests**: Modify the JavaScript files as needed

---

**Note**: This web UI simulates a complete restaurant management system with intelligent receipt processing, table management, and printer queue optimization. All data processing happens client-side for real-time performance.