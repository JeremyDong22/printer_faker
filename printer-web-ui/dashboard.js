// Dashboard with Chinese/English Language Support
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

// Language translations
const translations = {
    'zh': {
        'title': '智能打印机管理系统',
        'hero.title': '智能打印机管理系统',
        'hero.subtitle': '实时监控餐厅订单和打印机状态',
        'hero.cta': '选择您的视图',
        'hero.description': '三种不同的界面，满足不同的管理需求',
        
        'views.list.title': '订单列表',
        'views.list.description': '传统的订单时间线视图，实时显示所有收据和订单详情',
        'views.tables.title': '餐桌管理', 
        'views.tables.description': '按餐桌组织订单，直观显示桌台状态和用餐进度',
        'views.printers.title': '打印机监控',
        'views.printers.description': '监控不同打印机的队列状态，优化厨房和服务效率',
        
        'features.search': '搜索功能',
        'features.export': '导出数据',
        'features.tableStatus': '桌台状态',
        'features.timeline': '时间线',
        'features.queues': '队列管理',
        'features.metrics': '性能指标',
        
        'features.title': '强大功能',
        'features.subtitle': '为现代餐厅设计的智能管理工具',
        'features.realtime.title': '实时更新',
        'features.realtime.description': '通过SSE技术实现毫秒级的实时数据更新',
        'features.multilingual.title': '中英双语',
        'features.multilingual.description': '完美支持中文和英文界面切换',
        'features.responsive.title': '响应式设计',
        'features.responsive.description': '适配手机、平板和桌面设备',
        'features.intelligent.title': '智能分析',
        'features.intelligent.description': '自动识别桌台信息和菜品分类',
        
        'stats.totalReceipts': '总订单数',
        'stats.activeTables': '活跃桌台',
        'stats.activePrinters': '在线打印机',
        'stats.uptime': '系统运行时间',
        
        'buttons.enter': '进入视图',
        
        'status.connecting': '连接中...',
        'status.connected': '已连接',
        'status.disconnected': '连接断开',
        
        'footer.title': '智能打印机管理系统',
        'footer.description': '连接到 printer.smartice.ai API 服务',
        'footer.lastUpdate': '最后更新'
    },
    'en': {
        'title': 'Smart Printer Management System',
        'hero.title': 'Smart Printer Management System',
        'hero.subtitle': 'Real-time monitoring of restaurant orders and printer status',
        'hero.cta': 'Choose Your View',
        'hero.description': 'Three different interfaces to meet different management needs',
        
        'views.list.title': 'Order List',
        'views.list.description': 'Traditional order timeline view with real-time display of all receipts and order details',
        'views.tables.title': 'Table Management',
        'views.tables.description': 'Organize orders by table, visually display table status and dining progress',
        'views.printers.title': 'Printer Monitor',
        'views.printers.description': 'Monitor different printer queue status to optimize kitchen and service efficiency',
        
        'features.search': 'Search',
        'features.export': 'Export',
        'features.tableStatus': 'Table Status',
        'features.timeline': 'Timeline',
        'features.queues': 'Queue Management',
        'features.metrics': 'Performance Metrics',
        
        'features.title': 'Powerful Features',
        'features.subtitle': 'Smart management tools designed for modern restaurants',
        'features.realtime.title': 'Real-time Updates',
        'features.realtime.description': 'Millisecond-level real-time data updates through SSE technology',
        'features.multilingual.title': 'Bilingual Support',
        'features.multilingual.description': 'Perfect support for Chinese and English interface switching',
        'features.responsive.title': 'Responsive Design',
        'features.responsive.description': 'Compatible with mobile, tablet and desktop devices',
        'features.intelligent.title': 'Intelligent Analysis',
        'features.intelligent.description': 'Automatically identify table information and dish classification',
        
        'stats.totalReceipts': 'Total Orders',
        'stats.activeTables': 'Active Tables',
        'stats.activePrinters': 'Online Printers',
        'stats.uptime': 'System Uptime',
        
        'buttons.enter': 'Enter View',
        
        'status.connecting': 'Connecting...',
        'status.connected': 'Connected',
        'status.disconnected': 'Disconnected',
        
        'footer.title': 'Smart Printer Management System',
        'footer.description': 'Connected to printer.smartice.ai API service',
        'footer.lastUpdate': 'Last Updated'
    }
};

// Dashboard Application
class DashboardApp {
    constructor() {
        this.currentLang = localStorage.getItem('language') || 'zh';
        this.stats = {
            totalReceipts: 0,
            activeTables: 0,
            activePrinters: 8, // Default printer count
            uptime: 0
        };
        
        this.initializeElements();
        this.initializeLanguage();
        this.bindEvents();
        this.checkHealth();
        this.loadStats();
        
        // Auto-refresh every 30 seconds
        setInterval(() => this.checkHealth(), 30000);
        setInterval(() => this.loadStats(), 60000);
    }
    
    initializeElements() {
        // Status elements
        this.statusBadge = document.getElementById('statusBadge');
        this.statusText = document.getElementById('statusText');
        this.currentLangElement = document.getElementById('currentLang');
        
        // Stats elements
        this.totalReceipts = document.getElementById('totalReceipts');
        this.activeTables = document.getElementById('activeTables');
        this.activePrinters = document.getElementById('activePrinters');
        this.systemUptime = document.getElementById('systemUptime');
        this.lastUpdateTime = document.getElementById('lastUpdateTime');
    }
    
    initializeLanguage() {
        this.updateLanguageDisplay();
        this.translatePage();
    }
    
    bindEvents() {
        // Language toggle
        window.toggleLanguage = () => {
            this.currentLang = this.currentLang === 'zh' ? 'en' : 'zh';
            localStorage.setItem('language', this.currentLang);
            this.updateLanguageDisplay();
            this.translatePage();
        };
        
        // Navigation
        window.navigateToView = (view) => {
            const pages = {
                'list': 'index.html',
                'tables': 'tables.html', 
                'printers': 'printers.html'
            };
            
            if (pages[view]) {
                // Add language parameter
                const url = new URL(pages[view], window.location.href);
                url.searchParams.set('lang', this.currentLang);
                window.location.href = url.toString();
            }
        };
    }
    
    updateLanguageDisplay() {
        if (this.currentLangElement) {
            this.currentLangElement.textContent = this.currentLang === 'zh' ? '中文' : 'English';
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
    
    // API Communication
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
            throw error;
        }
    }
    
    async checkHealth() {
        try {
            const health = await this.makeApiRequest(API_CONFIG.endpoints.health);
            this.updateStatus('online', this.currentLang === 'zh' ? '已连接' : 'Connected');
            this.updateHealthStats(health);
        } catch (error) {
            this.updateStatus('offline', this.currentLang === 'zh' ? '连接断开' : 'Disconnected');
        }
    }
    
    updateStatus(status, text) {
        this.statusBadge.className = `px-4 py-2 rounded-full text-white font-bold status-${status}`;
        this.statusText.textContent = text;
    }
    
    updateHealthStats(health) {
        this.stats.totalReceipts = health.receipts_count || 0;
        this.stats.uptime = health.uptime_seconds || 0;
        
        this.updateStatsDisplay();
    }
    
    async loadStats() {
        try {
            // Load recent receipts to calculate table stats
            const receipts = await this.makeApiRequest(API_CONFIG.endpoints.recent);
            this.calculateTableStats(receipts);
            this.updateStatsDisplay();
            
            // Update last update time
            this.lastUpdateTime.textContent = new Date().toLocaleString(
                this.currentLang === 'zh' ? 'zh-CN' : 'en-US'
            );
            
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }
    
    calculateTableStats(receipts) {
        const tables = new Set();
        
        receipts.forEach(receipt => {
            const tableInfo = this.extractTableInfo(receipt);
            if (tableInfo && tableInfo.tableNumber > 0) {
                tables.add(tableInfo.tableNumber);
            }
        });
        
        this.stats.activeTables = tables.size;
    }
    
    extractTableInfo(receipt) {
        if (!receipt.plain_text) return null;
        
        const text = receipt.plain_text.toLowerCase();
        let tableNumber = null;
        
        // Pattern matching for table numbers
        let match = text.match(/(?:桌号|table)[:\s]+(.+?)(?:\n|$)/);
        if (match) {
            const tableStr = match[1].trim();
            // Extract number from strings like "B区-B5" -> 5
            const numMatch = tableStr.match(/(\d+)/);
            if (numMatch) {
                tableNumber = parseInt(numMatch[1]);
            }
        }
        
        return tableNumber ? { tableNumber } : null;
    }
    
    updateStatsDisplay() {
        if (this.totalReceipts) {
            this.totalReceipts.textContent = this.stats.totalReceipts.toLocaleString();
        }
        if (this.activeTables) {
            this.activeTables.textContent = this.stats.activeTables.toString();
        }
        if (this.activePrinters) {
            this.activePrinters.textContent = this.stats.activePrinters.toString();
        }
        if (this.systemUptime) {
            this.systemUptime.textContent = this.formatUptime(this.stats.uptime);
        }
    }
    
    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (this.currentLang === 'zh') {
            if (days > 0) return `${days}天 ${hours}小时`;
            if (hours > 0) return `${hours}小时 ${minutes}分钟`;
            return `${minutes}分钟`;
        } else {
            if (days > 0) return `${days}d ${hours}h`;
            if (hours > 0) return `${hours}h ${minutes}m`;
            return `${minutes}m`;
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new DashboardApp();
});

// Global language function
window.toggleLanguage = () => {
    // Will be bound by DashboardApp
};