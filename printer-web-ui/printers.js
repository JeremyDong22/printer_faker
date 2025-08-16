// Printer Processing Units Dashboard - JavaScript Client with Chinese/English Support
// Language translations
const translations = {
    'zh': {
        'title': '打印机处理单元控制台',
        'header.title': '打印机处理单元',
        'status.connecting': '连接中...',
        'status.connected': '已连接',
        'status.disconnected': '连接断开',
        'status.offline': '离线',
        'stats.activePrinters': '活跃打印机',
        'stats.queuedJobs': '排队任务',
        'nav.listView': '列表视图',
        'nav.tables': '餐桌',
        'controls.view': '视图:',
        'controls.sortBy': '排序:',
        'filter.allPrinters': '所有打印机',
        'filter.activeOnly': '仅活跃',
        'filter.kitchen': '厨房',
        'filter.bar': '吧台',
        'filter.receipt': '收据',
        'filter.dessert': '甜品',
        'sort.queueLength': '队列长度',
        'sort.printerType': '打印机类型',
        'sort.recentActivity': '最近活动',
        'buttons.refresh': '刷新',
        'buttons.startMonitor': '开始监控',
        'buttons.stopMonitor': '停止监控',
        'buttons.clearAllQueues': '清空所有队列',
        'buttons.clearQueue': '清空队列',
        'buttons.testPrint': '测试打印',
        'buttons.enableDisable': '启用/禁用',
        'empty.noActivePrinters': '没有活跃的打印机',
        'empty.startReceiving': '开始接收订单以查看打印机活动',
        'modal.printerDetails': '打印机详情',
        'performance.systemPerformance': '系统性能',
        'printer.queue': '队列',
        'printer.capacity': '容量',
        'printer.utilization': '利用率',
        'printer.successRate': '成功率',
        'printer.avgTime': '平均时间',
        'printer.processing': '处理中',
        'printer.noQueuedJobs': '没有排队任务',
        'printer.lastActivity': '最后活动',
        'printer.information': '打印机信息',
        'printer.type': '类型',
        'printer.location': '位置',
        'printer.status': '状态',
        'printer.currentQueue': '当前队列',
        'performance.metrics': '性能指标',
        'performance.totalJobs': '总任务数',
        'performance.successful': '成功',
        'performance.failed': '失败',
        'performance.avgProcessing': '平均处理时间',
        'queue.jobs': '任务',
        'queue.currentlyProcessing': '正在处理',
        'queue.jobId': '任务ID',
        'queue.type': '类型',
        'queue.content': '内容',
        'queue.estTime': '预计时间',
        'queue.receipt': '收据',
        'queue.added': '添加时间',
        'queue.highPriority': '高优先级',
        'queue.noJobsInQueue': '队列中没有任务',
        'performance.overview': '系统概览',
        'performance.capacity': '总容量',
        'performance.byType': '按类型',
        'performance.busiestPrinters': '最繁忙的打印机',
        'notifications.queueCleared': '队列已清空',
        'notifications.allQueuesCleared': '所有队列已清空',
        'notifications.testPrintSent': '测试打印已发送',
        'notifications.printerStatusChanged': '打印机状态已更改',
        'notifications.newOrderDistributed': '新订单已分发到',
        'printers.kitchenHot.name': '厨房 - 热食',
        'printers.kitchenHot.location': '主厨房',
        'printers.kitchenHot.description': '热菜、主菜、开胃菜',
        'printers.kitchenCold.name': '厨房 - 冷食准备',
        'printers.kitchenCold.location': '冷菜厨房',
        'printers.kitchenCold.description': '沙拉、冷开胃菜',
        'printers.barMain.name': '主吧台',
        'printers.barMain.location': '前台吧',
        'printers.barMain.description': '酒精饮料、鸡尾酒',
        'printers.barCoffee.name': '咖啡站',
        'printers.barCoffee.location': '咖啡吧',
        'printers.barCoffee.description': '咖啡、茶、无酒精饮料',
        'printers.dessertStation.name': '甜品站',
        'printers.dessertStation.location': '糕点厨房',
        'printers.dessertStation.description': '甜品、糕点、冰淇淋',
        'printers.receiptCashier.name': '收银台收据',
        'printers.receiptCashier.location': '前台',
        'printers.receiptCashier.description': '顾客收据、账单',
        'printers.receiptKitchen.name': '厨房收据',
        'printers.receiptKitchen.location': '厨房传菜口',
        'printers.receiptKitchen.description': '厨房订单汇总',
        'printers.backupPrinter.name': '备用打印机',
        'printers.backupPrinter.location': '经理办公室',
        'printers.backupPrinter.description': '紧急备用打印机'
    },
    'en': {
        'title': 'Printer Processing Units Dashboard',
        'header.title': 'Printer Processing Units',
        'status.connecting': 'Connecting...',
        'status.connected': 'Connected',
        'status.disconnected': 'Disconnected',
        'status.offline': 'Offline',
        'stats.activePrinters': 'Active Printers',
        'stats.queuedJobs': 'Queued Jobs',
        'nav.listView': 'List View',
        'nav.tables': 'Tables',
        'controls.view': 'View:',
        'controls.sortBy': 'Sort By:',
        'filter.allPrinters': 'All Printers',
        'filter.activeOnly': 'Active Only',
        'filter.kitchen': 'Kitchen',
        'filter.bar': 'Bar',
        'filter.receipt': 'Receipt',
        'filter.dessert': 'Dessert',
        'sort.queueLength': 'Queue Length',
        'sort.printerType': 'Printer Type',
        'sort.recentActivity': 'Recent Activity',
        'buttons.refresh': 'Refresh',
        'buttons.startMonitor': 'Start Monitor',
        'buttons.stopMonitor': 'Stop Monitor',
        'buttons.clearAllQueues': 'Clear All Queues',
        'buttons.clearQueue': 'Clear Queue',
        'buttons.testPrint': 'Test Print',
        'buttons.enableDisable': 'Enable/Disable',
        'empty.noActivePrinters': 'No Active Printers',
        'empty.startReceiving': 'Start receiving orders to see printer activity',
        'modal.printerDetails': 'Printer Details',
        'performance.systemPerformance': 'System Performance',
        'printer.queue': 'Queue',
        'printer.capacity': 'Capacity',
        'printer.utilization': 'Utilization',
        'printer.successRate': 'Success Rate',
        'printer.avgTime': 'Avg Time',
        'printer.processing': 'PROCESSING',
        'printer.noQueuedJobs': 'No queued jobs',
        'printer.lastActivity': 'Last Activity',
        'printer.information': 'Printer Information',
        'printer.type': 'Type',
        'printer.location': 'Location',
        'printer.status': 'Status',
        'printer.currentQueue': 'Current Queue',
        'performance.metrics': 'Performance Metrics',
        'performance.totalJobs': 'Total Jobs',
        'performance.successful': 'Successful',
        'performance.failed': 'Failed',
        'performance.avgProcessing': 'Avg Processing',
        'queue.jobs': 'jobs',
        'queue.currentlyProcessing': 'Currently Processing',
        'queue.jobId': 'Job ID',
        'queue.type': 'Type',
        'queue.content': 'Content',
        'queue.estTime': 'Est. Time',
        'queue.receipt': 'Receipt',
        'queue.added': 'Added',
        'queue.highPriority': 'HIGH PRIORITY',
        'queue.noJobsInQueue': 'No jobs in queue',
        'performance.overview': 'System Overview',
        'performance.capacity': 'Total Capacity',
        'performance.byType': 'By Type',
        'performance.busiestPrinters': 'Busiest Printers',
        'notifications.queueCleared': 'Queue cleared for',
        'notifications.allQueuesCleared': 'All queues cleared',
        'notifications.testPrintSent': 'Test print sent to',
        'notifications.printerStatusChanged': 'is now',
        'notifications.newOrderDistributed': 'New order distributed to',
        'printers.kitchenHot.name': 'Kitchen - Hot Food',
        'printers.kitchenHot.location': 'Main Kitchen',
        'printers.kitchenHot.description': 'Hot dishes, mains, appetizers',
        'printers.kitchenCold.name': 'Kitchen - Cold Prep',
        'printers.kitchenCold.location': 'Cold Kitchen',
        'printers.kitchenCold.description': 'Salads, cold appetizers',
        'printers.barMain.name': 'Main Bar',
        'printers.barMain.location': 'Front Bar',
        'printers.barMain.description': 'Alcoholic beverages, cocktails',
        'printers.barCoffee.name': 'Coffee Station',
        'printers.barCoffee.location': 'Coffee Bar',
        'printers.barCoffee.description': 'Coffee, tea, non-alcoholic drinks',
        'printers.dessertStation.name': 'Dessert Station',
        'printers.dessertStation.location': 'Pastry Kitchen',
        'printers.dessertStation.description': 'Desserts, pastries, ice cream',
        'printers.receiptCashier.name': 'Cashier Receipt',
        'printers.receiptCashier.location': 'Front Desk',
        'printers.receiptCashier.description': 'Customer receipts, bills',
        'printers.receiptKitchen.name': 'Kitchen Receipt',
        'printers.receiptKitchen.location': 'Kitchen Pass',
        'printers.receiptKitchen.description': 'Order summaries for kitchen',
        'printers.backupPrinter.name': 'Backup Printer',
        'printers.backupPrinter.location': 'Manager Office',
        'printers.backupPrinter.description': 'Emergency backup printer'
    }
};

// API Configuration (same as other interfaces)
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

// Printer Management System
class PrinterUnitsApp {
    constructor() {
        this.printers = new Map(); // Printer ID -> Printer Data
        this.receipts = [];
        this.eventSource = null;
        this.isStreaming = false;
        this.selectedPrinter = null;
        this.performanceData = {
            totalJobs: 0,
            avgProcessingTime: 0,
            errorRate: 0,
            uptimePercentage: 100
        };
        
        // Language support
        this.currentLang = this.getLanguageFromUrl() || localStorage.getItem('language') || 'zh';
        
        this.initializeElements();
        this.initializeLanguage();
        this.bindEvents();
        this.initializePrinters();
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
            this.renderPrinters(); // Re-render to update printer card content
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
        this.activePrintersCount = document.getElementById('activePrintersCount');
        this.queuedJobsCount = document.getElementById('queuedJobsCount');
        this.liveIndicator = document.getElementById('liveIndicator');
        
        // Control elements
        this.refreshBtn = document.getElementById('refreshBtn');
        this.streamToggle = document.getElementById('streamToggle');
        this.viewSelect = document.getElementById('viewSelect');
        this.sortSelect = document.getElementById('sortSelect');
        this.clearQueuesBtn = document.getElementById('clearQueuesBtn');
        this.statsToggle = document.getElementById('statsToggle');
        
        // Display elements
        this.printersGrid = document.getElementById('printersGrid');
        this.emptyState = document.getElementById('emptyState');
        this.statsOverlay = document.getElementById('statsOverlay');
        this.performanceStats = document.getElementById('performanceStats');
        this.closeStats = document.getElementById('closeStats');
        
        // Modal elements
        this.printerModal = document.getElementById('printerModal');
        this.modalTitle = document.getElementById('modalTitle');
        this.modalContent = document.getElementById('modalContent');
        this.closeModal = document.getElementById('closeModal');
        this.clearQueueBtn = document.getElementById('clearQueueBtn');
        this.testPrintBtn = document.getElementById('testPrintBtn');
        this.enablePrinterBtn = document.getElementById('enablePrinterBtn');
    }
    
    bindEvents() {
        this.refreshBtn.addEventListener('click', () => this.loadInitialData());
        this.streamToggle.addEventListener('click', () => this.toggleStream());
        this.viewSelect.addEventListener('change', () => this.renderPrinters());
        this.sortSelect.addEventListener('change', () => this.renderPrinters());
        this.clearQueuesBtn.addEventListener('click', () => this.clearAllQueues());
        this.statsToggle.addEventListener('click', () => this.toggleStats());
        this.closeStats.addEventListener('click', () => this.toggleStats());
        
        // Modal events
        this.closeModal.addEventListener('click', () => this.closePrinterModal());
        this.printerModal.addEventListener('click', (e) => {
            if (e.target === this.printerModal) this.closePrinterModal();
        });
        this.clearQueueBtn.addEventListener('click', () => this.clearPrinterQueue());
        this.testPrintBtn.addEventListener('click', () => this.testPrint());
        this.enablePrinterBtn.addEventListener('click', () => this.togglePrinterStatus());
        
        // Auto-refresh
        setInterval(() => this.checkHealth(), 30000);
        setInterval(() => this.updatePrinterActivity(), 5000);
    }
    
    // API Communication (same as other interfaces)
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
            this.updatePerformanceMetrics(health);
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
    
    // Get translated printer information
    getPrinterInfo(printerId) {
        const printerMap = {
            'kitchen-hot': 'kitchenHot',
            'kitchen-cold': 'kitchenCold',
            'bar-main': 'barMain',
            'bar-coffee': 'barCoffee',
            'dessert-station': 'dessertStation',
            'receipt-cashier': 'receiptCashier',
            'receipt-kitchen': 'receiptKitchen',
            'backup-printer': 'backupPrinter'
        };
        
        const key = printerMap[printerId];
        if (!key) return null;
        
        return {
            name: translations[this.currentLang][`printers.${key}.name`],
            location: translations[this.currentLang][`printers.${key}.location`],
            description: translations[this.currentLang][`printers.${key}.description`]
        };
    }

    // Initialize Virtual Printers
    initializePrinters() {
        // Create standard restaurant printer units
        const printerConfigs = [
            {
                id: 'kitchen-hot',
                type: 'kitchen',
                capacity: 50,
                status: 'online'
            },
            {
                id: 'kitchen-cold',
                type: 'kitchen',
                capacity: 30,
                status: 'online'
            },
            {
                id: 'bar-main',
                type: 'bar',
                capacity: 40,
                status: 'online'
            },
            {
                id: 'bar-coffee',
                type: 'bar',
                capacity: 25,
                status: 'online'
            },
            {
                id: 'dessert-station',
                type: 'dessert',
                capacity: 20,
                status: 'online'
            },
            {
                id: 'receipt-cashier',
                type: 'receipt',
                capacity: 100,
                status: 'online'
            },
            {
                id: 'receipt-kitchen',
                type: 'receipt',
                capacity: 80,
                status: 'online'
            },
            {
                id: 'backup-printer',
                type: 'receipt',
                capacity: 50,
                status: 'offline'
            }
        ];
        
        printerConfigs.forEach(config => {
            this.printers.set(config.id, {
                ...config,
                queue: [],
                totalJobs: Math.floor(Math.random() * 100),
                successfulJobs: Math.floor(Math.random() * 90),
                failedJobs: Math.floor(Math.random() * 10),
                avgProcessingTime: Math.floor(Math.random() * 30) + 10,
                lastActivity: new Date(),
                isProcessing: false,
                currentJob: null
            });
        });
    }
    
    // Data Loading and Processing
    async loadInitialData() {
        try {
            const receipts = await this.makeApiRequest(API_CONFIG.endpoints.receipts);
            this.receipts = receipts;
            this.processReceiptsIntoPrinters();
            this.renderPrinters();
        } catch (error) {
            console.error('Failed to load initial data:', error);
        }
    }
    
    processReceiptsIntoPrinters() {
        // Clear existing queues
        this.printers.forEach(printer => {
            printer.queue = [];
        });
        
        // Process recent receipts and distribute to appropriate printers
        this.receipts.slice(-20).forEach(receipt => {
            const jobs = this.extractPrintJobs(receipt);
            jobs.forEach(job => {
                const printer = this.printers.get(job.printerId);
                if (printer) {
                    printer.queue.push(job);
                    printer.lastActivity = new Date(receipt.timestamp);
                }
            });
        });
        
        this.updatePrinterCounts();
    }
    
    extractPrintJobs(receipt) {
        const jobs = [];
        const text = receipt.plain_text.toLowerCase();
        const dishes = this.extractDishes(receipt.plain_text);
        
        // Always send to receipt printers
        jobs.push({
            id: `receipt-${receipt.id}`,
            receiptId: receipt.id,
            printerId: 'receipt-cashier',
            type: 'receipt',
            content: receipt.plain_text,
            priority: 'normal',
            timestamp: receipt.timestamp,
            estimatedTime: 5
        });
        
        jobs.push({
            id: `kitchen-receipt-${receipt.id}`,
            receiptId: receipt.id,
            printerId: 'receipt-kitchen',
            type: 'order-summary',
            content: receipt.plain_text,
            priority: 'normal',
            timestamp: receipt.timestamp,
            estimatedTime: 5
        });
        
        // Analyze dishes and route to appropriate stations
        dishes.forEach((dish, index) => {
            const dishName = dish.name.toLowerCase();
            let printerId = 'kitchen-hot'; // Default
            let priority = 'normal';
            
            // Route based on dish type
            if (dishName.includes('沙拉') || dishName.includes('凉菜') || dishName.includes('salad')) {
                printerId = 'kitchen-cold';
            } else if (dishName.includes('酒') || dishName.includes('啤酒') || dishName.includes('cocktail') || dishName.includes('wine')) {
                printerId = 'bar-main';
            } else if (dishName.includes('咖啡') || dishName.includes('茶') || dishName.includes('coffee') || dishName.includes('tea')) {
                printerId = 'bar-coffee';
            } else if (dishName.includes('甜品') || dishName.includes('蛋糕') || dishName.includes('dessert') || dishName.includes('ice cream')) {
                printerId = 'dessert-station';
            }
            
            // Set priority based on dish type
            if (dishName.includes('急') || dishName.includes('特快') || dishName.includes('priority')) {
                priority = 'high';
            }
            
            jobs.push({
                id: `dish-${receipt.id}-${index}`,
                receiptId: receipt.id,
                printerId: printerId,
                type: 'dish-order',
                content: `${dish.name} ${dish.quantity ? `x${dish.quantity}` : ''}`,
                dishInfo: dish,
                priority: priority,
                timestamp: receipt.timestamp,
                estimatedTime: this.estimateProcessingTime(dishName)
            });
        });
        
        return jobs;
    }
    
    extractDishes(text) {
        if (!text) return [];
        
        const lines = text.split('\\n');
        const dishes = [];
        
        for (const line of lines) {
            const trimmed = line.trim();
            
            if (!trimmed || 
                trimmed.includes('收银员') || 
                trimmed.includes('时间') ||
                trimmed.includes('单号') ||
                trimmed.includes('合计') ||
                trimmed.includes('找零') ||
                trimmed.length < 2) {
                continue;
            }
            
            const priceMatch = trimmed.match(/^(.+?)[\s\*]+([\d.]+)$/);
            if (priceMatch) {
                const dishName = priceMatch[1].trim();
                const price = parseFloat(priceMatch[2]);
                
                if (dishName.length > 1 && price > 0) {
                    dishes.push({
                        name: dishName,
                        price: price,
                        quantity: 1
                    });
                }
            } else if (trimmed.length > 2 && trimmed.length < 30) {
                dishes.push({
                    name: trimmed,
                    price: null,
                    quantity: 1
                });
            }
        }
        
        return dishes.slice(0, 8);
    }
    
    estimateProcessingTime(dishName) {
        // Estimate cooking/preparation time based on dish type
        if (dishName.includes('汤') || dishName.includes('soup')) return 20;
        if (dishName.includes('炒') || dishName.includes('烧') || dishName.includes('烤')) return 15;
        if (dishName.includes('沙拉') || dishName.includes('凉菜')) return 5;
        if (dishName.includes('饮料') || dishName.includes('drink')) return 3;
        if (dishName.includes('甜品') || dishName.includes('dessert')) return 10;
        
        return 12; // Default time
    }
    
    updatePrinterCounts() {
        const activePrinters = Array.from(this.printers.values()).filter(p => p.status === 'online');
        const totalQueuedJobs = Array.from(this.printers.values()).reduce((sum, p) => sum + p.queue.length, 0);
        
        this.activePrintersCount.textContent = activePrinters.length;
        this.queuedJobsCount.textContent = totalQueuedJobs;
    }
    
    updatePrinterActivity() {
        // Simulate printer processing
        this.printers.forEach(printer => {
            if (printer.status === 'online' && printer.queue.length > 0 && !printer.isProcessing) {
                // Start processing next job
                const job = printer.queue.shift();
                printer.currentJob = job;
                printer.isProcessing = true;
                
                // Simulate processing time
                setTimeout(() => {
                    printer.isProcessing = false;
                    printer.currentJob = null;
                    printer.successfulJobs++;
                    printer.totalJobs++;
                    printer.lastActivity = new Date();
                    
                    this.renderPrinters();
                    this.updatePrinterCounts();
                }, job.estimatedTime * 100); // Scaled down for demo
            }
        });
    }
    
    // Rendering Methods
    renderPrinters() {
        const view = this.viewSelect.value;
        const sort = this.sortSelect.value;
        
        let printersToShow = Array.from(this.printers.values());
        
        // Apply view filter
        if (view !== 'all') {
            if (view === 'active') {
                printersToShow = printersToShow.filter(p => p.status === 'online');
            } else {
                printersToShow = printersToShow.filter(p => p.type === view);
            }
        }
        
        // Apply sorting
        switch (sort) {
            case 'queue':
                printersToShow.sort((a, b) => b.queue.length - a.queue.length);
                break;
            case 'type':
                printersToShow.sort((a, b) => a.type.localeCompare(b.type));
                break;
            case 'activity':
                printersToShow.sort((a, b) => new Date(b.lastActivity) - new Date(a.lastActivity));
                break;
        }
        
        if (printersToShow.length === 0) {
            this.printersGrid.classList.add('hidden');
            this.emptyState.classList.remove('hidden');
            return;
        }
        
        this.printersGrid.classList.remove('hidden');
        this.emptyState.classList.add('hidden');
        
        this.printersGrid.innerHTML = printersToShow.map(printer => this.createPrinterCard(printer)).join('');
        this.bindPrinterEvents();
    }
    
    createPrinterCard(printer) {
        const statusClass = printer.status;
        const busyClass = printer.isProcessing ? 'active' : '';
        const queueLength = printer.queue.length;
        const utilization = Math.min((queueLength / printer.capacity) * 100, 100);
        
        // Get translated printer information
        const printerInfo = this.getPrinterInfo(printer.id);
        const displayName = printerInfo ? printerInfo.name : printer.name;
        const displayLocation = printerInfo ? printerInfo.location : printer.location;
        const displayDescription = printerInfo ? printerInfo.description : printer.description;
        
        return `
            <div class="printer-unit ${printer.type} ${statusClass} ${busyClass} rounded-lg p-6 cursor-pointer" 
                 data-printer="${printer.id}">
                <div class="printer-activity"></div>
                <div class="printer-status ${printer.isProcessing ? 'busy' : statusClass}"></div>
                
                <div class="mb-4">
                    <h3 class="text-xl font-bold mb-1">${displayName}</h3>
                    <p class="text-sm opacity-75">${displayLocation}</p>
                    <p class="text-xs opacity-60">${displayDescription}</p>
                </div>
                
                <div class="printer-metrics rounded-lg p-4 mb-4">
                    <div class="grid grid-cols-2 gap-4 mb-3">
                        <div>
                            <div class="text-xs opacity-75">Queue</div>
                            <div class="text-lg font-bold">${queueLength}</div>
                        </div>
                        <div>
                            <div class="text-xs opacity-75">Capacity</div>
                            <div class="text-lg font-bold">${printer.capacity}</div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-xs opacity-75">Utilization</span>
                            <span class="text-xs">${utilization.toFixed(0)}%</span>
                        </div>
                        <div class="w-full bg-black bg-opacity-20 rounded-full h-2">
                            <div class="bg-white rounded-full h-2 transition-all duration-300" 
                                 style="width: ${utilization}%"></div>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <div class="text-xs opacity-75">Success Rate</div>
                            <div class="text-sm font-bold">
                                ${printer.totalJobs > 0 ? 
                                    ((printer.successfulJobs / printer.totalJobs) * 100).toFixed(1) : 100}%
                            </div>
                        </div>
                        <div>
                            <div class="text-xs opacity-75">Avg Time</div>
                            <div class="text-sm font-bold">${printer.avgProcessingTime}s</div>
                        </div>
                    </div>
                </div>
                
                ${printer.isProcessing && printer.currentJob ? `
                <div class="bg-yellow-400 bg-opacity-20 rounded-lg p-3 mb-4">
                    <div class="text-xs font-bold text-yellow-300 mb-1">PROCESSING</div>
                    <div class="text-sm">${printer.currentJob.content.substring(0, 30)}...</div>
                </div>
                ` : ''}
                
                <div class="order-queue max-h-32 overflow-y-auto">
                    ${printer.queue.slice(0, 3).map((job, index) => `
                        <div class="order-item ${job.priority === 'high' ? 'priority' : ''} rounded p-2 mb-2">
                            <div class="flex justify-between items-start">
                                <div class="flex-1">
                                    <div class="text-sm font-medium">${job.content.substring(0, 25)}...</div>
                                    <div class="text-xs opacity-75">${job.type} • ${job.estimatedTime}s</div>
                                </div>
                                ${job.priority === 'high' ? 
                                    '<i class="fas fa-star text-yellow-300 text-xs"></i>' : ''}
                            </div>
                        </div>
                    `).join('')}
                    
                    ${printer.queue.length > 3 ? `
                        <div class="text-xs opacity-75 text-center">
                            +${printer.queue.length - 3} ${translations[this.currentLang]['queue.jobs']}
                        </div>
                    ` : ''}
                    
                    ${printer.queue.length === 0 ? `
                        <div class="text-xs opacity-50 text-center py-4">
                            ${translations[this.currentLang]['printer.noQueuedJobs']}
                        </div>
                    ` : ''}
                </div>
                
                <div class="mt-4 text-xs opacity-75">
                    ${translations[this.currentLang]['printer.lastActivity']}: ${this.getTimeAgo(printer.lastActivity)}
                </div>
            </div>
        `;
    }
    
    getTimeAgo(timestamp) {
        if (!timestamp) return translations[this.currentLang]['time.never'];
        
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / (1000 * 60));
        
        if (this.currentLang === 'zh') {
            if (diffMins < 1) return translations[this.currentLang]['time.justNow'];
            if (diffMins < 60) return `${diffMins}${translations[this.currentLang]['time.minutesAgo']}`;
            
            const diffHours = Math.floor(diffMins / 60);
            if (diffHours < 24) return `${diffHours}${translations[this.currentLang]['time.hoursAgo']}`;
            
            return time.toLocaleDateString('zh-CN');
        } else {
            if (diffMins < 1) return translations[this.currentLang]['time.justNow'];
            if (diffMins < 60) return `${diffMins}${translations[this.currentLang]['time.minutesAgo']}`;
            
            const diffHours = Math.floor(diffMins / 60);
            if (diffHours < 24) return `${diffHours}${translations[this.currentLang]['time.hoursAgo']}`;
            
            return time.toLocaleDateString('en-US');
        }
    }
    
    bindPrinterEvents() {
        this.printersGrid.querySelectorAll('.printer-unit').forEach(card => {
            card.addEventListener('click', (e) => {
                const printerId = e.currentTarget.dataset.printer;
                this.showPrinterDetails(printerId);
            });
        });
    }
    
    // Modal and Actions
    showPrinterDetails(printerId) {
        const printer = this.printers.get(printerId);
        if (!printer) return;
        
        this.selectedPrinter = printerId;
        this.modalTitle.textContent = `${printer.name} - Details`;
        
        const content = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h3 class="font-bold text-lg mb-4">Printer Information</h3>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-600">Type:</span>
                            <span class="font-medium capitalize">${printer.type}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Location:</span>
                            <span class="font-medium">${printer.location}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Status:</span>
                            <span class="font-medium capitalize ${printer.status === 'online' ? 'text-green-600' : 'text-red-600'}">
                                ${printer.status}
                            </span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Capacity:</span>
                            <span class="font-medium">${printer.capacity} jobs</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Current Queue:</span>
                            <span class="font-medium">${printer.queue.length} jobs</span>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h3 class="font-bold text-lg mb-4">Performance Metrics</h3>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-600">Total Jobs:</span>
                            <span class="font-medium">${printer.totalJobs}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Successful:</span>
                            <span class="font-medium text-green-600">${printer.successfulJobs}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Failed:</span>
                            <span class="font-medium text-red-600">${printer.failedJobs}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Success Rate:</span>
                            <span class="font-medium">
                                ${printer.totalJobs > 0 ? 
                                    ((printer.successfulJobs / printer.totalJobs) * 100).toFixed(1) : 100}%
                            </span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Avg Processing:</span>
                            <span class="font-medium">${printer.avgProcessingTime}s</span>
                        </div>
                    </div>
                </div>
            </div>
            
            ${printer.isProcessing && printer.currentJob ? `
            <div class="mt-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <h4 class="font-bold text-yellow-800 mb-2">Currently Processing</h4>
                <div class="text-sm text-yellow-700">
                    <div class="mb-1">Job ID: ${printer.currentJob.id}</div>
                    <div class="mb-1">Type: ${printer.currentJob.type}</div>
                    <div>Content: ${printer.currentJob.content}</div>
                </div>
            </div>
            ` : ''}
            
            <div class="mt-6">
                <h3 class="font-bold text-lg mb-4">Queue (${printer.queue.length} jobs)</h3>
                <div class="max-h-64 overflow-y-auto space-y-2">
                    ${printer.queue.map((job, index) => `
                        <div class="p-3 border border-gray-200 rounded-lg ${job.priority === 'high' ? 'border-yellow-400 bg-yellow-50' : ''}">
                            <div class="flex justify-between items-start">
                                <div class="flex-1">
                                    <div class="font-medium">${job.content}</div>
                                    <div class="text-sm text-gray-600">
                                        Type: ${job.type} • Est. Time: ${job.estimatedTime}s
                                        ${job.priority === 'high' ? ' • HIGH PRIORITY' : ''}
                                    </div>
                                    <div class="text-xs text-gray-500">
                                        Receipt: ${job.receiptId} • Added: ${new Date(job.timestamp).toLocaleString()}
                                    </div>
                                </div>
                                <div class="text-sm text-gray-500">#{index + 1}</div>
                            </div>
                        </div>
                    `).join('')}
                    
                    ${printer.queue.length === 0 ? `
                        <div class="text-center text-gray-500 py-8">
                            <i class="fas fa-inbox text-2xl mb-2"></i>
                            <p>No jobs in queue</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        this.modalContent.innerHTML = content;
        this.printerModal.classList.remove('hidden');
    }
    
    closePrinterModal() {
        this.printerModal.classList.add('hidden');
        this.selectedPrinter = null;
    }
    
    clearPrinterQueue() {
        if (this.selectedPrinter) {
            const printer = this.printers.get(this.selectedPrinter);
            if (printer) {
                printer.queue = [];
                this.renderPrinters();
                this.updatePrinterCounts();
                this.closePrinterModal();
                this.showNotification(`Queue cleared for ${printer.name}`, 'success');
            }
        }
    }
    
    clearAllQueues() {
        this.printers.forEach(printer => {
            printer.queue = [];
        });
        this.renderPrinters();
        this.updatePrinterCounts();
        this.showNotification('All queues cleared', 'success');
    }
    
    testPrint() {
        if (this.selectedPrinter) {
            const printer = this.printers.get(this.selectedPrinter);
            if (printer && printer.status === 'online') {
                const testJob = {
                    id: `test-${Date.now()}`,
                    receiptId: 'test',
                    printerId: printer.id,
                    type: 'test-print',
                    content: 'Test Print - System Check',
                    priority: 'high',
                    timestamp: new Date().toISOString(),
                    estimatedTime: 5
                };
                
                printer.queue.unshift(testJob); // Add to front of queue
                this.renderPrinters();
                this.updatePrinterCounts();
                this.showNotification(`Test print sent to ${printer.name}`, 'success');
            }
        }
    }
    
    togglePrinterStatus() {
        if (this.selectedPrinter) {
            const printer = this.printers.get(this.selectedPrinter);
            if (printer) {
                printer.status = printer.status === 'online' ? 'offline' : 'online';
                this.renderPrinters();
                this.updatePrinterCounts();
                this.closePrinterModal();
                this.showNotification(`${printer.name} is now ${printer.status}`, 'success');
            }
        }
    }
    
    // Performance and Statistics
    updatePerformanceMetrics(health) {
        this.performanceData = {
            totalJobs: health.total_received || 0,
            avgProcessingTime: 15, // Simulated
            errorRate: health.parse_errors || 0,
            uptimePercentage: 99.5 // Simulated
        };
    }
    
    toggleStats() {
        const isHidden = this.statsOverlay.style.transform === 'translateY(-100%)' || 
                        !this.statsOverlay.style.transform;
        
        if (isHidden) {
            this.updateStatsDisplay();
            this.statsOverlay.style.transform = 'translateY(0)';
        } else {
            this.statsOverlay.style.transform = 'translateY(-100%)';
        }
    }
    
    updateStatsDisplay() {
        const activePrinters = Array.from(this.printers.values()).filter(p => p.status === 'online');
        const totalCapacity = Array.from(this.printers.values()).reduce((sum, p) => sum + p.capacity, 0);
        const totalQueue = Array.from(this.printers.values()).reduce((sum, p) => sum + p.queue.length, 0);
        const utilizationRate = totalCapacity > 0 ? (totalQueue / totalCapacity) * 100 : 0;
        
        this.performanceStats.innerHTML = `
            <div class="bg-white bg-opacity-10 rounded-lg p-4">
                <h4 class="font-bold mb-2">System Overview</h4>
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span>Active Printers:</span>
                        <span class="font-bold">${activePrinters.length}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Total Capacity:</span>
                        <span class="font-bold">${totalCapacity}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Utilization:</span>
                        <span class="font-bold">${utilizationRate.toFixed(1)}%</span>
                    </div>
                </div>
            </div>
            
            <div class="bg-white bg-opacity-10 rounded-lg p-4">
                <h4 class="font-bold mb-2">Performance</h4>
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span>Total Jobs:</span>
                        <span class="font-bold">${this.performanceData.totalJobs}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Avg Processing:</span>
                        <span class="font-bold">${this.performanceData.avgProcessingTime}s</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Uptime:</span>
                        <span class="font-bold">${this.performanceData.uptimePercentage}%</span>
                    </div>
                </div>
            </div>
            
            <div class="bg-white bg-opacity-10 rounded-lg p-4">
                <h4 class="font-bold mb-2">By Type</h4>
                <div class="space-y-2">
                    ${['kitchen', 'bar', 'receipt', 'dessert'].map(type => {
                        const typeprinters = Array.from(this.printers.values()).filter(p => p.type === type);
                        const typeQueue = typeprinters.reduce((sum, p) => sum + p.queue.length, 0);
                        return `
                            <div class="flex justify-between">
                                <span class="capitalize">${type}:</span>
                                <span class="font-bold">${typeQueue} jobs</span>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
            
            <div class="bg-white bg-opacity-10 rounded-lg p-4">
                <h4 class="font-bold mb-2">Busiest Printers</h4>
                <div class="space-y-2">
                    ${Array.from(this.printers.values())
                        .sort((a, b) => b.queue.length - a.queue.length)
                        .slice(0, 3)
                        .map(printer => `
                            <div class="flex justify-between">
                                <span class="truncate">${printer.name}:</span>
                                <span class="font-bold">${printer.queue.length}</span>
                            </div>
                        `).join('')}
                </div>
            </div>
        `;
    }
    
    // Real-time Streaming (same pattern as other interfaces)
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
                
                this.receipts.unshift(receipt);
                if (this.receipts.length > 50) {
                    this.receipts = this.receipts.slice(0, 50);
                }
                
                // Add new jobs to printers
                const jobs = this.extractPrintJobs(receipt);
                jobs.forEach(job => {
                    const printer = this.printers.get(job.printerId);
                    if (printer) {
                        printer.queue.push(job);
                    }
                });
                
                this.renderPrinters();
                this.updatePrinterCounts();
                
                this.showNotification(`New order distributed to ${jobs.length} printers`, 'success');
                
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
            this.streamToggle.innerHTML = '<i class="fas fa-stop mr-2"></i>Stop Monitor';
            this.streamToggle.className = 'bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors';
        } else {
            this.streamToggle.innerHTML = '<i class="fas fa-play mr-2"></i>Start Monitor';
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
    app = new PrinterUnitsApp();
});

// Make app globally available
window.app = app;