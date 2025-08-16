// Restaurant Tables Dashboard - JavaScript Client with Chinese/English Support
// Language translations
const translations = {
    'zh': {
        'title': '餐厅餐桌控制台',
        'header.title': '餐厅餐桌控制台',
        'status.connecting': '连接中...',
        'status.connected': '已连接',
        'status.disconnected': '连接断开',
        'status.offline': '离线',
        'stats.activeTables': '活跃餐桌',
        'stats.orders': '订单',
        'nav.listView': '列表视图',
        'nav.printers': '打印机',
        'controls.layout': '布局:',
        'controls.filter': '筛选:',
        'layout.gridView': '网格视图',
        'layout.floorPlan': '楼层平面图',
        'filter.allTables': '所有餐桌',
        'filter.occupied': '已占用',
        'filter.pendingOrders': '待处理订单',
        'filter.readyToServe': '准备上菜',
        'filter.empty': '空闲',
        'buttons.refresh': '刷新',
        'buttons.startLiveUpdates': '开始实时更新',
        'buttons.stopLiveUpdates': '停止实时更新',
        'buttons.markReady': '标记为准备好',
        'buttons.clearTable': '清空餐桌',
        'empty.noActiveTables': '没有活跃的餐桌',
        'empty.startReceiving': '开始接收订单以查看餐桌活动',
        'modal.tableOrders': '餐桌订单',
        'table.orders': '订单',
        'table.lastUpdate': '最后更新',
        'table.items': '项目',
        'table.status': '状态',
        'table.totalOrders': '总订单数',
        'table.totalAmount': '总金额',
        'table.orderTimeline': '订单时间线',
        'table.dishesOrdered': '已点菜品',
        'table.qty': '数量',
        'table.empty': '空桌',
        'table.occupied': '已占用',
        'table.pending': '新订单',
        'table.ready': '准备好',
        'notifications.tableMarkedReady': '餐桌已标记为准备好',
        'notifications.tableCleared': '餐桌已清空',
        'notifications.newOrderFor': '新订单来自',
        'time.justNow': '刚刚',
        'time.minutesAgo': '分钟前',
        'time.hoursAgo': '小时前',
        'time.never': '从未'
    },
    'en': {
        'title': 'Restaurant Tables Dashboard',
        'header.title': 'Restaurant Tables Dashboard',
        'status.connecting': 'Connecting...',
        'status.connected': 'Connected',
        'status.disconnected': 'Disconnected',
        'status.offline': 'Offline',
        'stats.activeTables': 'Active Tables',
        'stats.orders': 'Orders',
        'nav.listView': 'List View',
        'nav.printers': 'Printers',
        'controls.layout': 'Layout:',
        'controls.filter': 'Filter:',
        'layout.gridView': 'Grid View',
        'layout.floorPlan': 'Floor Plan',
        'filter.allTables': 'All Tables',
        'filter.occupied': 'Occupied',
        'filter.pendingOrders': 'Pending Orders',
        'filter.readyToServe': 'Ready to Serve',
        'filter.empty': 'Empty',
        'buttons.refresh': 'Refresh',
        'buttons.startLiveUpdates': 'Start Live Updates',
        'buttons.stopLiveUpdates': 'Stop Live Updates',
        'buttons.markReady': 'Mark Ready',
        'buttons.clearTable': 'Clear Table',
        'empty.noActiveTables': 'No Active Tables',
        'empty.startReceiving': 'Start receiving orders to see table activity',
        'modal.tableOrders': 'Table Orders',
        'table.orders': 'Orders',
        'table.lastUpdate': 'Last Update',
        'table.items': 'items',
        'table.status': 'Status',
        'table.totalOrders': 'Total Orders',
        'table.totalAmount': 'Total Amount',
        'table.orderTimeline': 'Order Timeline',
        'table.dishesOrdered': 'Dishes Ordered',
        'table.qty': 'Qty',
        'table.empty': 'Empty',
        'table.occupied': 'Occupied',
        'table.pending': 'New Order',
        'table.ready': 'Ready',
        'notifications.tableMarkedReady': 'Table marked as ready!',
        'notifications.tableCleared': 'Table cleared!',
        'notifications.newOrderFor': 'New order for',
        'time.justNow': 'Just now',
        'time.minutesAgo': 'm ago',
        'time.hoursAgo': 'h ago',
        'time.never': 'Never'
    }
};

// API Configuration (same as main app)
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

// Table Management System
class RestaurantTablesApp {
    constructor() {
        this.tables = new Map(); // Table Number -> Table Data
        this.receipts = [];
        this.eventSource = null;
        this.isStreaming = false;
        this.selectedTable = null;
        
        // Language support
        this.currentLang = this.getLanguageFromUrl() || localStorage.getItem('language') || 'zh';
        
        this.initializeElements();
        this.initializeLanguage();
        this.bindEvents();
        this.checkHealth();
        this.loadInitialData();
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
            this.renderTables(); // Re-render to update table card content
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
        this.activeTablesCount = document.getElementById('activeTablesCount');
        this.totalOrdersCount = document.getElementById('totalOrdersCount');
        this.liveIndicator = document.getElementById('liveIndicator');
        
        // Control elements
        this.refreshBtn = document.getElementById('refreshBtn');
        this.streamToggle = document.getElementById('streamToggle');
        this.layoutSelect = document.getElementById('layoutSelect');
        this.statusFilter = document.getElementById('statusFilter');
        this.fullscreenBtn = document.getElementById('fullscreenBtn');
        
        // Display elements
        this.tablesGrid = document.getElementById('tablesGrid');
        this.emptyState = document.getElementById('emptyState');
        
        // Modal elements
        this.orderModal = document.getElementById('orderModal');
        this.modalTitle = document.getElementById('modalTitle');
        this.modalContent = document.getElementById('modalContent');
        this.closeModal = document.getElementById('closeModal');
        this.markReadyBtn = document.getElementById('markReadyBtn');
        this.clearTableBtn = document.getElementById('clearTableBtn');
    }
    
    bindEvents() {
        this.refreshBtn.addEventListener('click', () => this.loadInitialData());
        this.streamToggle.addEventListener('click', () => this.toggleStream());
        this.layoutSelect.addEventListener('change', () => this.renderTables());
        this.statusFilter.addEventListener('change', () => this.renderTables());
        this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        
        // Modal events
        this.closeModal.addEventListener('click', () => this.closeOrderModal());
        this.orderModal.addEventListener('click', (e) => {
            if (e.target === this.orderModal) this.closeOrderModal();
        });
        this.markReadyBtn.addEventListener('click', () => this.markTableReady());
        this.clearTableBtn.addEventListener('click', () => this.clearTable());
        
        // Auto-refresh health every 30 seconds
        setInterval(() => this.checkHealth(), 30000);
    }
    
    // API Communication Methods (same as main app)
    async makeApiRequest(endpoint, params = {}) {
        const url = new URL(API_CONFIG.baseUrl + endpoint);
        url.searchParams.append('auth', API_CONFIG.apiKey);
        
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
            this.showNotification(`API Error: ${error.message}`, 'error');
            throw error;
        }
    }
    
    async checkHealth() {
        try {
            const health = await this.makeApiRequest(API_CONFIG.endpoints.health);
            this.updateStatus('online', 'Connected');
            this.totalOrdersCount.textContent = health.receipts_count || 0;
        } catch (error) {
            this.updateStatus('offline', 'Disconnected');
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
    
    // Data Loading and Processing
    async loadInitialData() {
        try {
            const receipts = await this.makeApiRequest(API_CONFIG.endpoints.receipts);
            this.receipts = receipts;
            this.processReceiptsIntoTables();
            this.renderTables();
        } catch (error) {
            console.error('Failed to load initial data:', error);
        }
    }
    
    processReceiptsIntoTables() {
        // Clear existing tables
        this.tables.clear();
        
        // Process receipts and extract table information
        this.receipts.forEach(receipt => {
            const tableInfo = this.extractTableInfo(receipt);
            if (tableInfo) {
                this.addOrderToTable(tableInfo.tableNumber, receipt, tableInfo);
            }
        });
        
        this.updateTableCounts();
    }
    
    extractTableInfo(receipt) {
        if (!receipt.plain_text) return null;
        
        const text = receipt.plain_text.toLowerCase();
        
        // Try to extract table number from various patterns
        let tableNumber = null;
        
        // Pattern 1: "桌号: 5" or "table: 5"
        let match = text.match(/(?:桌号|table)[:\s]+(\d+)/);
        if (match) {
            tableNumber = parseInt(match[1]);
        }
        
        // Pattern 2: "5号桌" or "table 5"
        if (!tableNumber) {
            match = text.match(/(\d+)号桌|table\s+(\d+)/);
            if (match) {
                tableNumber = parseInt(match[1] || match[2]);
            }
        }
        
        // Pattern 3: Look for numbers near beginning of receipt
        if (!tableNumber) {
            const lines = receipt.plain_text.split('\n').slice(0, 5);
            for (const line of lines) {
                match = line.match(/\b(\d{1,2})\b/);
                if (match) {
                    const num = parseInt(match[1]);
                    if (num >= 1 && num <= 99) { // Reasonable table range
                        tableNumber = num;
                        break;
                    }
                }
            }
        }
        
        // If no table number found, assign to counter/takeaway (table 0)
        if (!tableNumber) {
            tableNumber = 0; // Counter/Takeaway orders
        }
        
        // Extract dishes/items
        const dishes = this.extractDishes(receipt.plain_text);
        
        return {
            tableNumber,
            dishes,
            timestamp: receipt.timestamp
        };
    }
    
    extractDishes(text) {
        if (!text) return [];
        
        const lines = text.split('\\n');
        const dishes = [];
        
        // Look for lines that look like menu items
        for (const line of lines) {
            const trimmed = line.trim();
            
            // Skip empty lines, headers, and footer info
            if (!trimmed || 
                trimmed.includes('收银员') || 
                trimmed.includes('时间') ||
                trimmed.includes('单号') ||
                trimmed.includes('合计') ||
                trimmed.includes('找零') ||
                trimmed.length < 2) {
                continue;
            }
            
            // Look for price patterns (dish name + price)
            const priceMatch = trimmed.match(/^(.+?)[\s\*]+([\d.]+)$/);
            if (priceMatch) {
                const dishName = priceMatch[1].trim();
                const price = parseFloat(priceMatch[2]);
                
                if (dishName.length > 1 && price > 0) {
                    dishes.push({
                        name: dishName,
                        price: price,
                        quantity: 1 // Default quantity
                    });
                }
            } else if (trimmed.length > 2 && trimmed.length < 30) {
                // Potential dish name without clear price
                dishes.push({
                    name: trimmed,
                    price: null,
                    quantity: 1
                });
            }
        }
        
        return dishes.slice(0, 10); // Limit to 10 items per order
    }
    
    addOrderToTable(tableNumber, receipt, tableInfo) {
        if (!this.tables.has(tableNumber)) {
            this.tables.set(tableNumber, {
                number: tableNumber,
                status: 'occupied',
                orders: [],
                dishes: [],
                totalAmount: 0,
                lastUpdate: receipt.timestamp,
                orderCount: 0
            });
        }
        
        const table = this.tables.get(tableNumber);
        table.orders.push(receipt);
        table.dishes.push(...tableInfo.dishes);
        table.orderCount = table.orders.length;
        table.lastUpdate = receipt.timestamp;
        
        // Calculate total if prices available
        table.totalAmount = table.dishes.reduce((sum, dish) => {
            return sum + (dish.price || 0);
        }, 0);
        
        // Determine table status
        const now = new Date();
        const lastUpdate = new Date(table.lastUpdate);
        const minutesSinceUpdate = (now - lastUpdate) / (1000 * 60);
        
        if (minutesSinceUpdate < 5) {
            table.status = 'pending'; // New order
        } else if (minutesSinceUpdate < 15) {
            table.status = 'occupied'; // Processing
        } else {
            table.status = 'ready'; // Ready to serve
        }
    }
    
    updateTableCounts() {
        const activeTables = Array.from(this.tables.values()).filter(table => 
            table.status !== 'empty' && table.number !== 0
        );
        this.activeTablesCount.textContent = activeTables.length;
    }
    
    // Rendering Methods
    renderTables() {
        const layout = this.layoutSelect.value;
        const filter = this.statusFilter.value;
        
        let tablesToShow = Array.from(this.tables.values());
        
        // Apply filter
        if (filter !== 'all') {
            tablesToShow = tablesToShow.filter(table => table.status === filter);
        }
        
        // Sort tables by number
        tablesToShow.sort((a, b) => a.number - b.number);
        
        if (tablesToShow.length === 0) {
            this.tablesGrid.classList.add('hidden');
            this.emptyState.classList.remove('hidden');
            return;
        }
        
        this.tablesGrid.classList.remove('hidden');
        this.emptyState.classList.add('hidden');
        
        if (layout === 'grid') {
            this.renderGridLayout(tablesToShow);
        } else {
            this.renderFloorPlan(tablesToShow);
        }
    }
    
    renderGridLayout(tables) {
        this.tablesGrid.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6';
        
        this.tablesGrid.innerHTML = tables.map(table => this.createTableCard(table)).join('');
        this.bindTableEvents();
    }
    
    renderFloorPlan(tables) {
        this.tablesGrid.className = 'grid grid-cols-1 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 gap-4';
        
        // Create a floor plan layout with tables positioned more naturally
        const maxTable = Math.max(...tables.map(t => t.number), 20);
        const floorTables = [];
        
        for (let i = 0; i <= maxTable; i++) {
            const table = tables.find(t => t.number === i);
            if (table) {
                floorTables.push(table);
            } else if (i > 0 && i <= 20) {
                // Show empty table placeholders for reasonable range
                floorTables.push({
                    number: i,
                    status: 'empty',
                    orders: [],
                    dishes: [],
                    orderCount: 0
                });
            }
        }
        
        this.tablesGrid.innerHTML = floorTables.map(table => this.createCompactTableCard(table)).join('');
        this.bindTableEvents();
    }
    
    createTableCard(table) {
        const displayName = table.number === 0 ? 'Counter' : `Table ${table.number}`;
        const statusClass = table.status;
        const lastUpdate = new Date(table.lastUpdate || Date.now()).toLocaleTimeString();
        
        const dishList = table.dishes.slice(0, 3).map(dish => 
            `<span class="dish-tag">${dish.name}</span>`
        ).join('');
        
        const moreItems = table.dishes.length > 3 ? `<span class="dish-tag">+${table.dishes.length - 3} more</span>` : '';
        
        return `
            <div class="table-card ${statusClass} rounded-lg p-6 cursor-pointer" data-table="${table.number}">
                <div class="status-badge bg-black bg-opacity-20">
                    ${this.getStatusLabel(table.status)}
                </div>
                
                <div class="table-number mb-4">${displayName}</div>
                
                <div class="mb-4">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm opacity-75">Orders:</span>
                        <span class="font-bold">${table.orderCount}</span>
                    </div>
                    ${table.totalAmount > 0 ? `
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm opacity-75">Total:</span>
                        <span class="font-bold">¥${table.totalAmount.toFixed(2)}</span>
                    </div>
                    ` : ''}
                    <div class="flex items-center justify-between">
                        <span class="text-sm opacity-75">Last Update:</span>
                        <span class="text-xs">${lastUpdate}</span>
                    </div>
                </div>
                
                ${table.dishes.length > 0 ? `
                <div class="mb-4">
                    <div class="text-sm opacity-75 mb-2">Dishes:</div>
                    <div class="flex flex-wrap">
                        ${dishList}
                        ${moreItems}
                    </div>
                </div>
                ` : ''}
                
                <div class="flex items-center justify-between text-sm opacity-75">
                    <span><i class="fas fa-utensils mr-1"></i>${table.dishes.length} items</span>
                    <span><i class="fas fa-clock mr-1"></i>${this.getTimeAgo(table.lastUpdate)}</span>
                </div>
            </div>
        `;
    }
    
    createCompactTableCard(table) {
        const statusClass = table.status;
        const displayName = table.number === 0 ? 'C' : table.number;
        
        return `
            <div class="table-card ${statusClass} rounded-lg p-4 cursor-pointer text-center aspect-square flex flex-col justify-center" 
                 data-table="${table.number}">
                <div class="table-number text-xl mb-1">${displayName}</div>
                <div class="text-xs opacity-75">
                    ${table.orderCount} orders
                </div>
                ${table.dishes.length > 0 ? `
                <div class="text-xs opacity-60 mt-1">
                    ${table.dishes.length} items
                </div>
                ` : ''}
            </div>
        `;
    }
    
    getStatusLabel(status) {
        const labels = {
            'empty': 'Empty',
            'occupied': 'Occupied',
            'pending': 'New Order',
            'ready': 'Ready'
        };
        return labels[status] || status;
    }
    
    getTimeAgo(timestamp) {
        if (!timestamp) return 'Unknown';
        
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / (1000 * 60));
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        
        return time.toLocaleDateString();
    }
    
    bindTableEvents() {
        this.tablesGrid.querySelectorAll('.table-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const tableNumber = parseInt(e.currentTarget.dataset.table);
                this.showTableDetails(tableNumber);
            });
        });
    }
    
    // Modal Methods
    showTableDetails(tableNumber) {
        const table = this.tables.get(tableNumber);
        if (!table) return;
        
        this.selectedTable = tableNumber;
        const displayName = tableNumber === 0 ? 'Counter Orders' : `Table ${tableNumber} Orders`;
        this.modalTitle.textContent = displayName;
        
        const content = `
            <div class="mb-6">
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <div class="text-sm text-gray-600">Status</div>
                        <div class="font-bold text-lg capitalize">${table.status}</div>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <div class="text-sm text-gray-600">Total Orders</div>
                        <div class="font-bold text-lg">${table.orderCount}</div>
                    </div>
                </div>
                
                ${table.totalAmount > 0 ? `
                <div class="bg-green-50 p-4 rounded-lg mb-4">
                    <div class="text-sm text-gray-600">Total Amount</div>
                    <div class="font-bold text-2xl text-green-600">¥${table.totalAmount.toFixed(2)}</div>
                </div>
                ` : ''}
            </div>
            
            <div class="mb-6">
                <h3 class="font-bold text-lg mb-3">Order Timeline</h3>
                <div class="order-timeline">
                    ${table.orders.map((order, index) => `
                        <div class="timeline-item">
                            <div class="bg-white p-3 rounded-lg border border-gray-200">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="font-semibold">Order #${index + 1}</span>
                                    <span class="text-sm text-gray-500">${new Date(order.timestamp).toLocaleString()}</span>
                                </div>
                                <div class="text-sm text-gray-600">Receipt: ${order.receipt_no || 'N/A'}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            ${table.dishes.length > 0 ? `
            <div>
                <h3 class="font-bold text-lg mb-3">Dishes Ordered</h3>
                <div class="grid grid-cols-1 gap-2">
                    ${table.dishes.map(dish => `
                        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span class="font-medium">${dish.name}</span>
                            <div class="text-right">
                                ${dish.price ? `<span class="font-bold">¥${dish.price.toFixed(2)}</span>` : ''}
                                <div class="text-sm text-gray-500">Qty: ${dish.quantity}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        `;
        
        this.modalContent.innerHTML = content;
        this.orderModal.classList.remove('hidden');
    }
    
    closeOrderModal() {
        this.orderModal.classList.add('hidden');
        this.selectedTable = null;
    }
    
    markTableReady() {
        if (this.selectedTable !== null && this.tables.has(this.selectedTable)) {
            const table = this.tables.get(this.selectedTable);
            table.status = 'ready';
            this.renderTables();
            this.closeOrderModal();
            this.showNotification(`Table ${this.selectedTable} marked as ready!`, 'success');
        }
    }
    
    clearTable() {
        if (this.selectedTable !== null) {
            this.tables.delete(this.selectedTable);
            this.updateTableCounts();
            this.renderTables();
            this.closeOrderModal();
            this.showNotification(`Table ${this.selectedTable} cleared!`, 'success');
        }
    }
    
    // Real-time Streaming (same pattern as main app)
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
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const receipt = JSON.parse(event.data);
                
                if (receipt.type === 'connected') return;
                
                // Add new receipt and reprocess tables
                this.receipts.unshift(receipt);
                if (this.receipts.length > 100) {
                    this.receipts = this.receipts.slice(0, 100);
                }
                
                this.processReceiptsIntoTables();
                this.renderTables();
                
                const tableInfo = this.extractTableInfo(receipt);
                if (tableInfo) {
                    const tableName = tableInfo.tableNumber === 0 ? 'Counter' : `Table ${tableInfo.tableNumber}`;
                    this.showNotification(`New order for ${tableName}!`, 'success');
                }
                
            } catch (error) {
                console.error('Failed to parse SSE data:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('SSE stream error:', error);
            this.stopStream();
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
            this.streamToggle.innerHTML = '<i class="fas fa-stop mr-2"></i>Stop Live Updates';
            this.streamToggle.className = 'bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors';
        } else {
            this.streamToggle.innerHTML = '<i class="fas fa-play mr-2"></i>Start Live Updates';
            this.streamToggle.className = 'bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors';
        }
    }
    
    updateLiveIndicator(isLive) {
        if (isLive) {
            this.liveIndicator.innerHTML = '<i class="fas fa-circle mr-1"></i>Live';
            this.liveIndicator.className = 'px-4 py-2 bg-green-500 text-white rounded-full text-sm status-online';
        } else {
            this.liveIndicator.innerHTML = '<i class="fas fa-circle mr-1"></i>Offline';
            this.liveIndicator.className = 'px-4 py-2 bg-gray-300 text-gray-600 rounded-full text-sm';
        }
    }
    
    // Utility Methods
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
            this.fullscreenBtn.innerHTML = '<i class="fas fa-compress-alt"></i>';
        } else {
            document.exitFullscreen();
            this.fullscreenBtn.innerHTML = '<i class="fas fa-expand-alt"></i>';
        }
    }
    
    showNotification(message, type = 'info') {
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
        
        setTimeout(() => notification.classList.remove('translate-x-full'), 100);
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }
}

// Initialize the application
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new RestaurantTablesApp();
});

// Make app globally available
window.app = app;