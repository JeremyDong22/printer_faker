"""
Web Dashboard for Printer API Service
Provides a visual monitoring interface
"""

def get_dashboard_html():
    """Returns the HTML dashboard for monitoring"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Printer Monitor Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 { 
                color: white;
                font-size: 2.5rem;
                margin-bottom: 30px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }
            .dashboard {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .card h3 {
                margin-bottom: 15px;
                color: #667eea;
            }
            .stat-value {
                font-size: 2rem;
                font-weight: bold;
                color: #333;
            }
            .stat-label {
                color: #666;
                font-size: 0.9rem;
                margin-top: 5px;
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
                animation: pulse 2s infinite;
            }
            .status-online { background: #48bb78; }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            .receipt-list {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                max-height: 80vh;
                overflow-y: auto;
            }
            .receipt-item {
                padding: 15px;
                border-bottom: 1px solid #e2e8f0;
                transition: all 0.2s;
                cursor: pointer;
            }
            .receipt-item:hover {
                background: #f7fafc;
                transform: translateX(5px);
            }
            .receipt-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
            }
            .receipt-no {
                font-weight: bold;
                color: #667eea;
            }
            .receipt-time {
                color: #718096;
                font-size: 0.9rem;
            }
            .receipt-preview {
                color: #4a5568;
                font-size: 0.85rem;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .new-receipt {
                animation: slideIn 0.5s ease-out;
                background: #f0fff4;
            }
            @keyframes slideIn {
                from {
                    transform: translateX(-100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            .order-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 999;
            }
            .order-modal.show {
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .order-details {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                width: 90%;
                max-width: 800px;
                max-height: 90vh;
                overflow-y: auto;
            }
            .order-details h2 {
                color: #667eea;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .close-btn {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: #718096;
            }
            .order-info {
                margin-bottom: 20px;
                padding: 15px;
                background: #f7fafc;
                border-radius: 5px;
            }
            .order-info-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
            }
            .order-info-label {
                font-weight: 600;
                color: #4a5568;
            }
            .order-content {
                background: #fff;
                padding: 15px;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                font-family: monospace;
                white-space: pre-wrap;
                max-height: 400px;
                overflow-y: auto;
            }
            .live-indicator {
                display: inline-block;
                padding: 4px 8px;
                background: #48bb78;
                color: white;
                border-radius: 4px;
                font-size: 0.8rem;
                font-weight: 600;
                animation: blink 2s infinite;
            }
            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            .controls {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            button {
                background: white;
                color: #667eea;
                border: 2px solid #667eea;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s;
            }
            button:hover {
                background: #667eea;
                color: white;
            }
            .auth-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
            }
            .auth-modal.show {
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .auth-form {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                width: 90%;
                max-width: 400px;
            }
            .auth-form h2 {
                margin-bottom: 20px;
                color: #667eea;
            }
            .auth-form input {
                width: 100%;
                margin-bottom: 15px;
                padding: 10px;
                border: 2px solid #e2e8f0;
                border-radius: 5px;
            }
            .auth-form button {
                width: 100%;
            }
            .error-message {
                color: #f56565;
                margin-top: 10px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🖨️ Printer Monitor Dashboard</h1>
            
            <div class="dashboard">
                <div class="card">
                    <h3>Service Status</h3>
                    <div>
                        <span class="status-indicator status-online"></span>
                        <span id="status-text">Online</span>
                        <span class="live-indicator" style="margin-left: 10px;">LIVE</span>
                    </div>
                    <div class="stat-label" id="uptime">Uptime: Loading...</div>
                </div>
                
                <div class="card">
                    <h3>Total Receipts</h3>
                    <div class="stat-value" id="total-receipts">0</div>
                    <div class="stat-label">Processed Today</div>
                </div>
                
                <div class="card">
                    <h3>Last Receipt</h3>
                    <div id="last-receipt-time">-</div>
                    <div class="stat-label">Receipt Time</div>
                </div>
                
                <div class="card">
                    <h3>Active Connections</h3>
                    <div class="stat-value" id="active-connections">0</div>
                    <div class="stat-label" id="connection-status">of 50 max</div>
                </div>
            </div>
            
            <div class="controls">
                <button onclick="loadRecent()">Refresh</button>
                <button onclick="exportReceipts()">Export All</button>
            </div>
            
            <div class="receipt-list" id="receipt-list">
                <h3 style="margin-bottom: 15px;">Recent Receipts</h3>
                <div id="receipts-container"></div>
            </div>
        </div>
        
        <div class="auth-modal" id="auth-modal">
            <div class="auth-form">
                <h2>🔐 Authentication Required</h2>
                <p style="margin-bottom: 20px; color: #718096;">Please enter the API password</p>
                <input type="password" id="auth-password" placeholder="Enter password" onkeypress="if(event.key==='Enter') authenticate()">
                <button onclick="authenticate()">Login</button>
                <div class="error-message" id="auth-error">Invalid password. Please try again.</div>
            </div>
        </div>
        
        <div class="order-modal" id="order-modal">
            <div class="order-details">
                <h2>
                    <span>📋 Order Details</span>
                    <button class="close-btn" onclick="closeOrderModal()">&times;</button>
                </h2>
                <div class="order-info" id="order-info"></div>
                <h3 style="margin-bottom: 10px; color: #4a5568;">Receipt Content</h3>
                <div class="order-content" id="order-content"></div>
            </div>
        </div>
        
        <script>
            let apiPassword = localStorage.getItem('apiPassword') || '';
            let isAuthenticated = false;
            let lastReceiptCount = 0;
            let currentReceipts = [];
            let updateInterval = null;
            
            async function updateStatus() {
                try {
                    const res = await fetch('/api/stats', {
                        headers: { 'Authorization': apiPassword }
                    });
                    if (!res.ok) {
                        showAuthPrompt();
                        return;
                    }
                    const data = await res.json();
                    
                    document.getElementById('total-receipts').textContent = data.total_receipts || 0;
                    document.getElementById('active-connections').textContent = data.connection_pool?.active || 0;
                    document.getElementById('connection-status').textContent = `of ${data.connection_pool?.max || 50} max`;
                    
                    // Get health for uptime
                    const healthRes = await fetch('/api/health', {
                        headers: { 'Authorization': apiPassword }
                    });
                    if (healthRes.ok) {
                        const health = await healthRes.json();
                        const uptime = health.uptime_seconds || 0;
                        const hours = Math.floor(uptime / 3600);
                        const minutes = Math.floor((uptime % 3600) / 60);
                        document.getElementById('uptime').textContent = `Uptime: ${hours}h ${minutes}m`;
                        
                        if (health.last_receipt) {
                            const lastTime = new Date(health.last_receipt);
                            document.getElementById('last-receipt-time').textContent = lastTime.toLocaleString();
                        }
                    }
                } catch (error) {
                    console.error('Failed to update status:', error);
                }
            }
            
            async function loadRecent() {
                try {
                    const res = await fetch('/api/recent?limit=50', {
                        headers: { 'Authorization': apiPassword }
                    });
                    if (!res.ok) {
                        showAuthPrompt();
                        return;
                    }
                    const data = await res.json();
                    
                    // Check for new receipts
                    const isNewData = data.length > lastReceiptCount;
                    lastReceiptCount = data.length;
                    currentReceipts = data;
                    
                    displayReceipts(data, isNewData);
                } catch (error) {
                    console.error('Failed to load recent:', error);
                }
            }
            
            function displayReceipts(receiptList, hasNew = false) {
                const container = document.getElementById('receipts-container');
                container.innerHTML = '';
                
                receiptList.forEach((receipt, index) => {
                    const item = document.createElement('div');
                    item.className = 'receipt-item';
                    
                    // Highlight new receipts
                    if (hasNew && index === 0) {
                        item.classList.add('new-receipt');
                        setTimeout(() => item.classList.remove('new-receipt'), 3000);
                    }
                    
                    const preview = receipt.plain_text ? 
                        receipt.plain_text.split('\\n').filter(line => line.trim()).slice(0, 2).join(' | ').substring(0, 150) : 
                        '[Empty Receipt]';
                    
                    item.innerHTML = `
                        <div class="receipt-header">
                            <span class="receipt-no">Receipt #${receipt.receipt_no || 'N/A'}</span>
                            <span class="receipt-time">${new Date(receipt.timestamp).toLocaleString()}</span>
                        </div>
                        <div class="receipt-preview">${preview}...</div>
                    `;
                    
                    // Add click handler
                    item.onclick = () => showOrderDetails(receipt);
                    
                    container.appendChild(item);
                });
            }
            
            function showOrderDetails(receipt) {
                const modal = document.getElementById('order-modal');
                const infoDiv = document.getElementById('order-info');
                const contentDiv = document.getElementById('order-content');
                
                // Parse receipt content for structured display
                const lines = receipt.plain_text ? receipt.plain_text.split('\\n') : [];
                let tableNo = 'N/A';
                let orderType = 'Receipt';
                
                // Extract table number and order type
                lines.forEach(line => {
                    if (line.includes('桌号:') || line.includes('台号:')) {
                        tableNo = line.split(':')[1]?.trim() || 'N/A';
                    }
                    if (line.includes('制作分单')) {
                        orderType = 'Kitchen Slip';
                    } else if (line.includes('客单')) {
                        orderType = 'Customer Order';
                    }
                });
                
                // Display order info
                infoDiv.innerHTML = `
                    <div class="order-info-row">
                        <span class="order-info-label">Receipt Number:</span>
                        <span>${receipt.receipt_no || 'N/A'}</span>
                    </div>
                    <div class="order-info-row">
                        <span class="order-info-label">Order Type:</span>
                        <span>${orderType}</span>
                    </div>
                    <div class="order-info-row">
                        <span class="order-info-label">Table:</span>
                        <span>${tableNo}</span>
                    </div>
                    <div class="order-info-row">
                        <span class="order-info-label">Time:</span>
                        <span>${new Date(receipt.timestamp).toLocaleString()}</span>
                    </div>
                    ${receipt.supabase_status ? `
                    <div class="order-info-row">
                        <span class="order-info-label">Supabase Status:</span>
                        <span style="color: ${receipt.supabase_status === 'processed' ? '#48bb78' : '#f56565'}">
                            ${receipt.supabase_status.toUpperCase()}
                        </span>
                    </div>
                    ` : ''}
                `;
                
                // Display receipt content
                contentDiv.textContent = receipt.plain_text || 'No content available';
                
                // Show modal
                modal.classList.add('show');
            }
            
            function closeOrderModal() {
                document.getElementById('order-modal').classList.remove('show');
            }
            
            async function exportReceipts() {
                try {
                    const res = await fetch('/api/receipts', {
                        headers: { 'Authorization': apiPassword }
                    });
                    if (!res.ok) {
                        showAuthPrompt();
                        return;
                    }
                    const data = await res.json();
                    
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `receipts_${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                } catch (error) {
                    console.error('Export failed:', error);
                }
            }
            
            function showAuthPrompt() {
                document.getElementById('auth-modal').classList.add('show');
                document.getElementById('auth-password').focus();
            }
            
            async function authenticate() {
                const password = document.getElementById('auth-password').value;
                if (!password) return;
                
                try {
                    const res = await fetch('/api/health', {
                        headers: { 'Authorization': password }
                    });
                    
                    if (res.ok) {
                        apiPassword = password;
                        isAuthenticated = true;
                        localStorage.setItem('apiPassword', password);
                        document.getElementById('auth-modal').classList.remove('show');
                        document.getElementById('auth-error').style.display = 'none';
                        
                        startLiveUpdates();
                    } else {
                        document.getElementById('auth-error').style.display = 'block';
                        document.getElementById('auth-password').value = '';
                    }
                } catch (error) {
                    console.error('Auth error:', error);
                    document.getElementById('auth-error').style.display = 'block';
                }
            }
            
            function startLiveUpdates() {
                // Clear any existing interval
                if (updateInterval) {
                    clearInterval(updateInterval);
                }
                
                // Update immediately
                updateStatus();
                loadRecent();
                
                // Set up polling intervals
                updateInterval = setInterval(() => {
                    updateStatus();
                    loadRecent();
                }, 5000); // Update every 5 seconds for live updates
            }
            
            // Initialize
            if (apiPassword) {
                fetch('/api/health', { headers: { 'Authorization': apiPassword } })
                    .then(res => {
                        if (res.ok) {
                            isAuthenticated = true;
                            startLiveUpdates();
                        } else {
                            showAuthPrompt();
                        }
                    })
                    .catch(() => showAuthPrompt());
            } else {
                showAuthPrompt();
            }
            
            // Close modal on ESC key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    closeOrderModal();
                }
            });
        </script>
    </body>
    </html>
    """