// Printer API Dashboard - JavaScript Client with Chinese/English Support
// Language translations
const translations = {
    'zh': {
        'title': '打印机API控制台',
        'header.title': '打印机API控制台',
        'stats.receipts': '张收据',
        'buttons.refresh': '刷新',
        'buttons.start_stream': '开始实时更新',
        'buttons.stop_stream': '停止实时更新',
        'buttons.clear': '清空显示',
        'buttons.search': '搜索',
        'status.connecting': '连接中...',
        'status.connected': '已连接',
        'status.disconnected': '连接断开',
        'receipts.recent': '最近收据',
        'receipts.detail': '收据详情',
        'receipts.click_to_view': '点击收据查看详情',
        'receipts.no_receipts': '暂无收据',
        'receipts.noReceiptsYet': '暂无收据。启动流以查看实时更新。',
        'receipts.clickToView': '点击收据查看详情',
        'stats.status': '状态',
        'stats.uptime': '运行时间',
        'stats.totalReceived': '总接收数',
        'stats.parseErrors': '解析错误',
        'status.checking': '检查中...',
        'buttons.startStream': '开始流',
        'buttons.clearDisplay': '清空显示',
        'controls.search': '搜索:'
    },
    'en': {
        'title': 'Printer API Dashboard',
        'header.title': 'Printer API Dashboard',
        'stats.receipts': 'Receipts',
        'buttons.refresh': 'Refresh',
        'buttons.start_stream': 'Start Stream',
        'buttons.stop_stream': 'Stop Stream',
        'buttons.clear': 'Clear Display',
        'buttons.search': 'Search',
        'status.connecting': 'Connecting...',
        'status.connected': 'Connected',
        'status.disconnected': 'Disconnected',
        'receipts.recent': 'Recent Receipts',
        'receipts.detail': 'Receipt Detail',
        'receipts.click_to_view': 'Click on a receipt to view details',
        'receipts.no_receipts': 'No receipts found',
        'receipts.noReceiptsYet': 'No receipts yet. Start the stream to see real-time updates.',
        'receipts.clickToView': 'Click on a receipt to view details',
        'stats.status': 'Status',
        'stats.uptime': 'Uptime',
        'stats.totalReceived': 'Total Received',
        'stats.parseErrors': 'Parse Errors',
        'status.checking': 'Checking...',
        'buttons.startStream': 'Start Stream',
        'buttons.clearDisplay': 'Clear Display',
        'controls.search': 'Search:'
    }
};

// API Configuration
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

// Application State
class PrinterDashboard {
    constructor() {
        this.receipts = [];
        this.eventSource = null;
        this.isStreaming = false;
        this.selectedReceipt = null;
        
        // Language support
        this.currentLang = this.getLanguageFromUrl() || localStorage.getItem('language') || 'zh';
        
        this.initializeElements();
        this.initializeLanguage();
        this.bindEvents();
        this.checkHealth();
        this.loadRecentReceipts();
    }
    
    getLanguageFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('lang');
    }
    
    initializeLanguage() {
        localStorage.setItem('language', this.currentLang);
        this.updateLanguageDisplay();
        this.translatePage();
        
        // Global language toggle function
        window.toggleLanguage = () => {
            this.currentLang = this.currentLang === 'zh' ? 'en' : 'zh';
            localStorage.setItem('language', this.currentLang);
            this.updateLanguageDisplay();
            this.translatePage();
        };
    }
    
    updateLanguageDisplay() {
        const langElement = document.getElementById('currentLang');
        if (langElement) {
            langElement.textContent = this.currentLang === 'zh' ? '中文' : 'English';
        }
    }
    
    translatePage() {
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = translations[this.currentLang][key];
            if (translation) {
                element.textContent = translation;
            }
        });
        
        // Update page title
        document.title = translations[this.currentLang]['title'];
    }
    
    initializeElements() {
        // Status elements
        this.statusBadge = document.getElementById('statusBadge');
        this.statusText = document.getElementById('statusText');
        this.healthStatus = document.getElementById('healthStatus');
        this.uptime = document.getElementById('uptime');
        this.totalReceived = document.getElementById('totalReceived');
        this.parseErrors = document.getElementById('parseErrors');
        this.receiptCount = document.getElementById('receiptCount');
        this.liveIndicator = document.getElementById('liveIndicator');
        
        // Control elements
        this.refreshBtn = document.getElementById('refreshBtn');
        this.streamToggle = document.getElementById('streamToggle');
        this.clearBtn = document.getElementById('clearBtn');
        this.searchInput = document.getElementById('searchInput');
        this.searchBtn = document.getElementById('searchBtn');
        
        // Display elements
        this.receiptsList = document.getElementById('receiptsList');
        this.receiptDetail = document.getElementById('receiptDetail');
    }
    
    bindEvents() {
        this.refreshBtn.addEventListener('click', () => this.loadRecentReceipts());
        this.streamToggle.addEventListener('click', () => this.toggleStream());
        this.clearBtn.addEventListener('click', () => this.clearDisplay());
        this.searchBtn.addEventListener('click', () => this.searchReceipts());
        
        // Enter key for search
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchReceipts();
            }
        });
        
        // Auto-refresh health every 30 seconds
        setInterval(() => this.checkHealth(), 30000);
    }
    
    // API Communication Methods
    async makeApiRequest(endpoint, params = {}) {
        const url = new URL(API_CONFIG.baseUrl + endpoint);
        
        // Add authentication
        url.searchParams.append('auth', API_CONFIG.apiKey);
        
        // Add additional parameters
        Object.keys(params).forEach(key => {
            url.searchParams.append(key, params[key]);
        });
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Authorization': API_CONFIG.apiKey,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            this.showError(`API Error: ${error.message}`);
            throw error;
        }
    }
    
    // Health Check
    async checkHealth() {
        try {
            const health = await this.makeApiRequest(API_CONFIG.endpoints.health);
            this.updateHealthStatus(health);
            this.updateStatus('online', 'Connected');
        } catch (error) {
            this.updateStatus('offline', 'Disconnected');
            this.healthStatus.textContent = 'Offline';
        }
    }
    
    updateHealthStatus(health) {
        this.healthStatus.textContent = health.status.toUpperCase();
        this.receiptCount.textContent = health.receipts_count || 0;
        this.totalReceived.textContent = health.total_received || 0;
        this.parseErrors.textContent = health.parse_errors || 0;
        
        // Format uptime
        const uptimeSeconds = health.uptime_seconds || 0;
        this.uptime.textContent = this.formatUptime(uptimeSeconds);
    }
    
    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }
    
    updateStatus(status, text) {
        this.statusBadge.className = `px-4 py-2 rounded-full text-white font-bold status-${status}`;
        this.statusText.textContent = text;
        
        if (status === 'online') {
            this.statusBadge.style.background = 'linear-gradient(45deg, #10b981, #059669)';
        } else {
            this.statusBadge.style.background = 'linear-gradient(45deg, #ef4444, #dc2626)';
        }
    }
    
    // Receipt Loading
    async loadRecentReceipts() {
        try {
            const receipts = await this.makeApiRequest(API_CONFIG.endpoints.recent);
            this.receipts = receipts;
            this.renderReceipts();
        } catch (error) {
            console.error('Failed to load receipts:', error);
        }
    }
    
    // Search Functionality
    async searchReceipts() {
        const query = this.searchInput.value.trim();
        if (!query) {
            this.loadRecentReceipts();
            return;
        }
        
        try {
            const results = await this.makeApiRequest(API_CONFIG.endpoints.search, { no: query });
            this.receipts = results;
            this.renderReceipts();
            
            if (results.length === 0) {
                this.showMessage('No receipts found for: ' + query);
            }
        } catch (error) {
            console.error('Search failed:', error);
        }
    }
    
    // Real-time Streaming
    toggleStream() {
        if (this.isStreaming) {
            this.stopStream();
        } else {
            this.startStream();
        }
    }
    
    startStream() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        const streamUrl = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stream}?auth=${API_CONFIG.apiKey}`;
        
        this.eventSource = new EventSource(streamUrl);
        
        this.eventSource.onopen = () => {
            this.isStreaming = true;
            this.updateStreamButton();
            this.updateLiveIndicator(true);
            console.log('SSE stream connected');
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const receipt = JSON.parse(event.data);
                
                if (receipt.type === 'connected') {
                    console.log('Stream connection confirmed');
                    return;
                }
                
                // Add new receipt to the beginning of the list
                this.receipts.unshift(receipt);
                
                // Keep only the last 50 receipts in memory
                if (this.receipts.length > 50) {
                    this.receipts = this.receipts.slice(0, 50);
                }
                
                this.renderReceipts();
                this.showNotification(`New receipt: ${receipt.receipt_no || 'Unknown'}`);
                
            } catch (error) {
                console.error('Failed to parse SSE data:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('SSE stream error:', error);
            this.stopStream();
            this.showError('Stream connection lost. Click to reconnect.');
        };
    }
    
    stopStream() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        this.isStreaming = false;
        this.updateStreamButton();
        this.updateLiveIndicator(false);
    }
    
    updateStreamButton() {
        if (this.isStreaming) {
            this.streamToggle.innerHTML = '<i class="fas fa-stop mr-2"></i>Stop Stream';
            this.streamToggle.className = 'bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors';
        } else {
            this.streamToggle.innerHTML = '<i class="fas fa-play mr-2"></i>Start Stream';
            this.streamToggle.className = 'bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors';
        }
    }
    
    updateLiveIndicator(isLive) {
        if (isLive) {
            this.liveIndicator.innerHTML = '<i class="fas fa-circle mr-1"></i>Live';
            this.liveIndicator.className = 'ml-auto text-sm px-2 py-1 bg-green-500 text-white rounded-full status-online';
        } else {
            this.liveIndicator.innerHTML = '<i class="fas fa-circle mr-1"></i>Offline';
            this.liveIndicator.className = 'ml-auto text-sm px-2 py-1 bg-gray-300 text-gray-600 rounded-full';
        }
    }
    
    // UI Rendering
    renderReceipts() {
        if (this.receipts.length === 0) {
            this.receiptsList.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-receipt text-4xl mb-4"></i>
                    <p>No receipts found.</p>
                </div>
            `;
            return;
        }
        
        const receiptsHtml = this.receipts.map(receipt => this.createReceiptCard(receipt)).join('');
        this.receiptsList.innerHTML = receiptsHtml;
        
        // Bind click events
        this.receiptsList.querySelectorAll('.receipt-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const receiptId = e.currentTarget.dataset.receiptId;
                const receipt = this.receipts.find(r => r.id === receiptId);
                if (receipt) {
                    this.showReceiptDetail(receipt);
                }
            });
        });
    }
    
    createReceiptCard(receipt) {
        const timestamp = new Date(receipt.timestamp).toLocaleString();
        const preview = this.getReceiptPreview(receipt.plain_text);
        
        return `
            <div class="receipt-item cursor-pointer bg-gray-50 hover:bg-blue-50 p-4 rounded-lg mb-4 border border-gray-200 new-receipt" 
                 data-receipt-id="${receipt.id}">
                <div class="flex justify-between items-start mb-2">
                    <div class="font-bold text-lg text-blue-600">${receipt.receipt_no || 'No Receipt #'}</div>
                    <div class="text-sm text-gray-500">${timestamp}</div>
                </div>
                <div class="text-sm text-gray-700 receipt-preview">${preview}</div>
                <div class="mt-2 flex items-center text-xs text-gray-500">
                    <i class="fas fa-clock mr-1"></i>
                    ${timestamp}
                </div>
            </div>
        `;
    }
    
    getReceiptPreview(text) {
        if (!text) return 'No content';
        
        // Get first meaningful line
        const lines = text.split('\n').filter(line => line.trim().length > 0);
        const preview = lines.slice(0, 3).join(' ').substring(0, 100);
        return preview + (preview.length >= 100 ? '...' : '');
    }
    
    showReceiptDetail(receipt) {
        this.selectedReceipt = receipt;
        const timestamp = new Date(receipt.timestamp).toLocaleString();
        
        this.receiptDetail.innerHTML = `
            <div class="receipt-paper p-4 rounded-lg mb-4">
                <div class="text-center border-b border-gray-300 pb-2 mb-4">
                    <h3 class="font-bold text-lg">Receipt Details</h3>
                    <p class="text-sm text-gray-600">ID: ${receipt.id}</p>
                </div>
                
                <div class="mb-4">
                    <div class="flex justify-between mb-2">
                        <span class="font-bold">Receipt #:</span>
                        <span>${receipt.receipt_no || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between mb-2">
                        <span class="font-bold">Timestamp:</span>
                        <span>${timestamp}</span>
                    </div>
                </div>
                
                <div class="border-t border-gray-300 pt-4">
                    <h4 class="font-bold mb-2">Receipt Content:</h4>
                    <div class="receipt-paper p-3 text-sm max-h-96 overflow-y-auto">
                        ${this.formatReceiptText(receipt.plain_text)}
                    </div>
                </div>
            </div>
            
            <div class="flex space-x-2">
                <button onclick="navigator.clipboard.writeText('${receipt.plain_text.replace(/'/g, "\\'")}').then(() => app.showNotification('Copied to clipboard!'))" 
                        class="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-sm transition-colors">
                    <i class="fas fa-copy mr-1"></i>Copy Text
                </button>
                <button onclick="app.downloadReceipt('${receipt.id}')" 
                        class="flex-1 bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm transition-colors">
                    <i class="fas fa-download mr-1"></i>Download
                </button>
            </div>
        `;
    }
    
    formatReceiptText(text) {
        if (!text) return '<em class="text-gray-500">No content available</em>';
        
        // Escape HTML and preserve formatting
        const escaped = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>');
            
        return escaped;
    }
    
    downloadReceipt(receiptId) {
        const receipt = this.receipts.find(r => r.id === receiptId);
        if (!receipt) return;
        
        const content = `Receipt #: ${receipt.receipt_no || 'N/A'}\nTimestamp: ${receipt.timestamp}\n\n${receipt.plain_text}`;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `receipt_${receipt.receipt_no || receiptId}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showNotification('Receipt downloaded!');
    }
    
    // Utility Methods
    clearDisplay() {
        this.receipts = [];
        this.renderReceipts();
        this.receiptDetail.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <i class="fas fa-mouse-pointer text-4xl mb-4"></i>
                <p>Click on a receipt to view details</p>
            </div>
        `;
        this.showNotification('Display cleared');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-20 right-6 px-4 py-2 rounded-lg text-white z-50 transition-all duration-300 transform translate-x-full`;
        
        switch (type) {
            case 'error':
                notification.classList.add('bg-red-500');
                break;
            case 'success':
                notification.classList.add('bg-green-500');
                break;
            default:
                notification.classList.add('bg-blue-500');
        }
        
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-info-circle mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Animate out and remove
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showMessage(message) {
        this.showNotification(message, 'info');
    }
}

// Initialize the application
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new PrinterDashboard();
});

// Global error handling
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    if (app) {
        app.showError('An unexpected error occurred');
    }
});

// Make app globally available for button onclick handlers
window.app = app;