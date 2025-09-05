/**
 * Durable Object for maintaining persistent SSE connection to printer API
 * Replaces the local PM2 supabase-integration.js service
 */

import { AxiomLogger } from './logger';

export interface Env {
  API_URL: string;
  API_AUTH_TOKEN: string;
  NEXT_PUBLIC_SUPABASE_URL: string;
  NEXT_PUBLIC_SUPABASE_ANON_KEY: string;
  SUPABASE_SERVICE_ROLE_KEY: string;
  CACHE: KVNamespace;
  ORDER_LOGS?: KVNamespace;
  AXIOM_TOKEN?: string;
  AXIOM_DATASET?: string;
  SSE_LISTENER: DurableObjectNamespace;
}

export class SSEListener {
  state: DurableObjectState;
  env: Env;
  activeConnection: boolean = false;
  reconnectAttempts: number = 0;
  maxReconnectAttempts: number = 10;
  reconnectDelay: number = 5000; // Start with 5 seconds
  abortController: AbortController | null = null;
  logger: AxiomLogger;
  supabaseUrl: string = '';
  supabaseServiceKey: string = '';
  totalOrdersReceived: number = 0;
  lastFlushTime: number = Date.now();

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
    this.env = env;
    this.logger = new AxiomLogger(env.AXIOM_TOKEN, env.AXIOM_DATASET || 'kitchen-orders');
    this.supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL || '';
    this.supabaseServiceKey = env.SUPABASE_SERVICE_ROLE_KEY || '';
    
    console.log(`[SSE] Durable Object initialized at ${new Date().toISOString()}`);
    console.log(`[SSE] Axiom logger initialized: ${this.logger.isEnabled() ? 'ENABLED' : 'DISABLED'}`);
    console.log(`[SSE] Axiom token present: ${!!env.AXIOM_TOKEN}`);
    console.log(`[SSE] Axiom dataset: ${env.AXIOM_DATASET || 'kitchen-orders'}`);
    console.log(`[SSE] Supabase URL: ${this.supabaseUrl ? 'SET' : 'NOT SET'}`);
    console.log(`[SSE] Supabase key: ${this.supabaseServiceKey ? 'SET' : 'NOT SET'}`);
    
    // Restore state if needed
    this.state.blockConcurrencyWhile(async () => {
      const stored = await this.state.storage.get(['activeConnection', 'reconnectAttempts', 'totalOrdersReceived']);
      this.activeConnection = stored.get('activeConnection') as boolean || false;
      this.reconnectAttempts = stored.get('reconnectAttempts') as number || 0;
      this.totalOrdersReceived = stored.get('totalOrdersReceived') as number || 0;
      
      console.log(`[SSE] Restored state: active=${this.activeConnection}, reconnects=${this.reconnectAttempts}, total=${this.totalOrdersReceived}`);
    });
    
    // Set up periodic heartbeat to keep DO alive and flush Axiom
    this.setupHeartbeat();
    
    // Auto-start connection if it was previously active
    if (this.activeConnection) {
      console.log('[SSE] Auto-restarting previously active connection');
      this.startSSEConnection();
    }
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    
    // Extract environment variables from query params (passed by the Worker)
    const axiomToken = url.searchParams.get('axiomToken');
    const axiomDataset = url.searchParams.get('axiomDataset');
    const supabaseUrl = url.searchParams.get('supabaseUrl');
    const supabaseKey = url.searchParams.get('supabaseKey');
    
    // Update logger if Axiom token is provided and not yet initialized
    if (axiomToken && !this.logger.isEnabled()) {
      console.log('[SSEListener] Initializing Axiom with token from Worker');
      console.log(`[SSEListener] Token length: ${axiomToken.length}`);
      console.log(`[SSEListener] Dataset: ${axiomDataset || 'kitchen-orders'}`);
      this.logger = new AxiomLogger(axiomToken, axiomDataset || 'kitchen-orders');
      console.log(`[SSEListener] Axiom enabled after init: ${this.logger.isEnabled()}`);
    } else if (!axiomToken) {
      console.log('[SSEListener] No Axiom token provided in request');
    } else {
      console.log('[SSEListener] Axiom already enabled');
    }
    
    // Update Supabase config if provided
    if (supabaseUrl && supabaseKey) {
      this.supabaseUrl = supabaseUrl;
      this.supabaseServiceKey = supabaseKey;
    }
    
    // Handle the actual path (remove /api/sse prefix)
    const path = url.pathname.replace('/api/sse', '');
    
    switch (path) {
      case '/start':
        return this.handleStart();
      case '/stop':
        return this.handleStop();
      case '/status':
        return this.handleStatus();
      case '/test':
        return this.handleTest();
      case '/health':
        return new Response('OK', { status: 200 });
      default:
        return new Response('Not found', { status: 404 });
    }
  }

  private setupHeartbeat(): void {
    // Send heartbeat every 5 minutes to keep DO alive and flush Axiom
    const heartbeatInterval = 5 * 60 * 1000; // 5 minutes
    
    const sendHeartbeat = async () => {
      if (this.activeConnection) {
        console.log(`[SSE] Heartbeat at ${new Date().toISOString()}, total received: ${this.totalOrdersReceived}`);
        
        // Log heartbeat to Axiom
        this.logger.log({
          event: 'sse.heartbeat',
          timestamp: new Date().toISOString(),
          totalReceived: this.totalOrdersReceived,
          ordersProcessed: await this.state.storage.get('ordersProcessed') as number || 0,
          connected: this.activeConnection,
          bufferSize: this.logger.getBufferSize()
        });
        
        // Force flush to Axiom
        if (this.logger.getBufferSize() > 0) {
          console.log(`[SSE] Flushing ${this.logger.getBufferSize()} events to Axiom (heartbeat)`);
          await this.logger.flush();
        }
        
        // Persist state
        await this.state.storage.put('totalOrdersReceived', this.totalOrdersReceived);
        
        // Schedule next heartbeat
        setTimeout(sendHeartbeat, heartbeatInterval);
      }
    };
    
    // Start heartbeat after a delay
    setTimeout(sendHeartbeat, heartbeatInterval);
  }

  private async handleStart(): Promise<Response> {
    if (this.activeConnection) {
      return new Response(JSON.stringify({ 
        message: 'SSE connection already active',
        status: 'connected' 
      }), { 
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    try {
      // Send a test event to Axiom to verify it's working
      console.log('[SSEListener] Sending test event to Axiom');
      this.logger.log({
        event: 'sse.test_event',
        message: 'Testing Axiom connection from Durable Object',
        timestamp: new Date().toISOString(),
        axiomEnabled: this.logger.isEnabled()
      });
      await this.logger.flush();
      console.log('[SSEListener] Test event sent to Axiom');
      
      await this.startSSEConnection();
      return new Response(JSON.stringify({ 
        message: 'SSE connection started',
        status: 'connecting' 
      }), { 
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      this.logger.logError('sse.start_failed', error instanceof Error ? error.message : 'Unknown error');
      await this.logger.flush();
      return new Response(JSON.stringify({ 
        error: 'Failed to start SSE connection',
        details: error instanceof Error ? error.message : 'Unknown error'
      }), { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  private async handleStop(): Promise<Response> {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    this.activeConnection = false;
    await this.state.storage.put('activeConnection', false);
    
    this.logger.log({
      event: 'sse.connection_stopped',
      manual: true
    });
    await this.logger.flush();
    
    return new Response(JSON.stringify({ 
      message: 'SSE connection stopped',
      status: 'disconnected' 
    }), { 
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  private async handleTest(): Promise<Response> {
    console.log('[SSE] Test endpoint called');
    
    // Send multiple test events to Axiom
    const testEvents = [
      {
        event: 'test.manual',
        timestamp: new Date().toISOString(),
        message: 'Manual test from /api/sse/test endpoint',
        axiomEnabled: this.logger.isEnabled(),
        bufferSize: this.logger.getBufferSize()
      },
      {
        event: 'test.connection_info',
        timestamp: new Date().toISOString(),
        connected: this.activeConnection,
        totalReceived: this.totalOrdersReceived,
        reconnectAttempts: this.reconnectAttempts
      }
    ];
    
    for (const event of testEvents) {
      this.logger.log(event);
    }
    
    // Force immediate flush
    console.log(`[SSE] Flushing ${this.logger.getBufferSize()} test events to Axiom`);
    await this.logger.flush();
    
    return new Response(JSON.stringify({
      message: 'Test events sent to Axiom',
      eventsCount: testEvents.length,
      axiomEnabled: this.logger.isEnabled(),
      timestamp: new Date().toISOString()
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  private async handleStatus(): Promise<Response> {
    const lastUpdate = await this.state.storage.get('lastUpdate') as string;
    const lastError = await this.state.storage.get('lastError') as string;
    const ordersProcessed = await this.state.storage.get('ordersProcessed') as number || 0;
    const totalReceived = this.totalOrdersReceived;
    
    return new Response(JSON.stringify({
      connected: this.activeConnection,
      reconnectAttempts: this.reconnectAttempts,
      lastUpdate: lastUpdate || null,
      lastError: lastError || null,
      ordersProcessed,
      totalReceived,
      axiomBufferSize: this.logger.getBufferSize(),
      env: {
        hasSupabase: !!this.env.NEXT_PUBLIC_SUPABASE_URL,
        hasAxiom: !!this.env.AXIOM_TOKEN,
        hasOrderLogs: !!this.env.ORDER_LOGS
      }
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  private async startSSEConnection(): Promise<void> {
    if (this.activeConnection) return;
    
    this.activeConnection = true;
    await this.state.storage.put('activeConnection', true);
    
    // Reset abort controller
    if (this.abortController) {
      this.abortController.abort();
    }
    this.abortController = new AbortController();
    
    this.logger.logSSEConnection('connected');
    await this.logger.flush(); // Flush connection event immediately
    
    // Start the connection in the background
    this.maintainSSEConnection();
  }

  private async maintainSSEConnection(): Promise<void> {
    const sseUrl = 'https://printer.smartice.ai/api/stream?auth=smartbcg';
    
    while (this.activeConnection && this.reconnectAttempts < this.maxReconnectAttempts) {
      try {
        console.log(`[SSE] Connecting to ${sseUrl}...`);
        
        const response = await fetch(sseUrl, {
          headers: {
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
          },
          signal: this.abortController?.signal
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        if (!response.body) {
          throw new Error('No response body from SSE stream');
        }

        // Reset reconnection attempts on successful connection
        this.reconnectAttempts = 0;
        await this.state.storage.put('reconnectAttempts', 0);
        this.reconnectDelay = 5000; // Reset delay
        
        console.log('[SSE] Connected successfully');
        this.logger.log({ event: 'sse.connected', url: sseUrl });
        
        // Process the stream
        await this.processSSEStream(response.body);
        
      } catch (error) {
        if (!this.activeConnection) {
          console.log('[SSE] Connection stopped by user');
          break;
        }
        
        if (error instanceof Error && error.name === 'AbortError') {
          console.log('[SSE] Connection aborted');
          break;
        }
        
        console.error('[SSE] Connection error:', error);
        this.logger.logError('sse.connection_error', error instanceof Error ? error.message : 'Unknown error');
        await this.logger.flush();
        
        this.reconnectAttempts++;
        await this.state.storage.put('reconnectAttempts', this.reconnectAttempts);
        await this.state.storage.put('lastError', new Date().toISOString());
        
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          console.error('[SSE] Max reconnection attempts reached');
          this.activeConnection = false;
          await this.state.storage.put('activeConnection', false);
          break;
        }
        
        // Exponential backoff with max delay of 60 seconds
        const delay = Math.min(this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1), 60000);
        console.log(`[SSE] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    this.logger.logSSEConnection('disconnected');
    await this.logger.flush();
  }

  private async processSSEStream(stream: ReadableStream<Uint8Array>): Promise<void> {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    try {
      while (this.activeConnection) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('[SSE] Stream ended');
          break;
        }
        
        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });
        
        // The real API sends raw JSON objects, one per line (NOT SSE format!)
        // Based on the actual logs: Raw: {"id": "...", "receipt_no": "...", ...}
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer
        
        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) continue;
          
          try {
            // Parse as direct JSON (this is the actual format from printer.smartice.ai)
            const orderData = JSON.parse(trimmedLine);
            
            // Skip connection messages
            if (orderData.type === 'connected' || orderData.message === 'Stream connected') {
              console.log('[SSE] Connection heartbeat');
              continue;
            }
            
            // Log ALL received events for debugging
            this.totalOrdersReceived++;
            await this.state.storage.put('totalReceived', this.totalOrdersReceived);
            console.log(`[SSE] Event #${this.totalOrdersReceived}: receipt=${orderData.receipt_no}, hasText=${!!orderData.plain_text}`);
            
            // Log the raw event to Axiom for analysis
            this.logger.log({
              event: 'sse.raw_event',
              eventNumber: this.totalOrdersReceived,
              timestamp: new Date().toISOString(),
              eventType: orderData.type || 'unknown',
              hasReceipt: !!orderData.receipt_no,
              hasPlainText: !!orderData.plain_text,
              receiptNo: orderData.receipt_no,
              dataPreview: JSON.stringify(orderData).substring(0, 500)
            });
            
            // Flush to Axiom every 5 events or every 30 seconds
            const timeSinceLastFlush = Date.now() - this.lastFlushTime;
            if (this.logger.getBufferSize() > 5 || timeSinceLastFlush > 30000) {
              console.log(`[SSE] Flushing ${this.logger.getBufferSize()} events to Axiom`);
              await this.logger.flush();
              this.lastFlushTime = Date.now();
            }
            
            // Skip events without receipt_no (like 预结单 - pre-checkout bills)
            if (!orderData.receipt_no) {
              console.log('[SSE] Skipping event without receipt_no (likely pre-checkout)');
              
              // Check if it's a pre-checkout bill by looking at plain_text
              if (orderData.plain_text && orderData.plain_text.includes('预结单')) {
                console.log('[SSE] Pre-checkout bill detected, logging only');
                this.logger.log({
                  event: 'order.pre_checkout',
                  timestamp: orderData.timestamp,
                  plainText: orderData.plain_text.substring(0, 200)
                });
              }
              continue;
            }
            
            // Check if we have the minimum required data
            if (!orderData.plain_text) {
              console.log('[SSE] WARNING: Event missing plain_text');
              continue;
            }
            
            // Process order to Supabase
            await this.processOrder(orderData);
            
          } catch (parseError) {
            // Only log parse errors for non-empty lines
            if (trimmedLine.length > 0) {
              console.error('[SSE] Failed to parse JSON:', trimmedLine.substring(0, 100));
              this.logger.log({
                event: 'sse.parse_error',
                line: trimmedLine.substring(0, 200),
                error: parseError instanceof Error ? parseError.message : 'Unknown error'
              });
            }
            
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  // Parse dishes from raw text
  private parseDishesFromText(text: string): Array<{name: string, quantity: number}> {
    const dishes: Array<{name: string, quantity: number}> = [];
    if (!text) return dishes;
    
    // Look for dishes section between "菜品单价数量小计" and "菜品价格合计"
    const dishSectionMatch = text.match(/菜品[单价]*数量[小计]*\n([\s\S]*?)菜品价格合计/);
    if (!dishSectionMatch) return dishes;
    
    const dishSection = dishSectionMatch[1];
    const lines = dishSection.split('\n');
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      
      // Skip modifiers (start with -)
      if (trimmed.startsWith('-')) continue;
      
      // Real format from API: "野菜卷181份18"
      // Pattern: dish_name + price + quantity + unit + subtotal
      // The key insight: the quantity is just before the unit (份/瓶/听/etc)
      
      // Match pattern: name + numbers + unit + final number
      const match = trimmed.match(/^(.+?)(\d+)(\d)([份瓶听盒位杯碗个张])(\d+)$/);
      if (match) {
        const name = match[1].trim();
        // match[2] is price, match[3] is quantity, match[4] is unit, match[5] is subtotal
        const quantity = parseInt(match[3]);
        
        if (name && quantity > 0) {
          dishes.push({ name, quantity });
          console.log(`[SSE] Parsed dish: ${name} x${quantity}`);
        }
      } else {
        // Fallback for simpler format or when regex doesn't match perfectly
        // Just extract the dish name by removing all numbers at the end
        const simpleMatch = trimmed.match(/^(.+?)(?:\d+[份瓶听盒位杯碗个张]\d+|\d+)$/);
        if (simpleMatch) {
          const name = simpleMatch[1].trim();
          if (name && !name.match(/^\d/)) {
            // Default to quantity 1 if we can't parse it
            dishes.push({ name, quantity: 1 });
            console.log(`[SSE] Parsed dish (fallback): ${name} x1`);
          }
        }
      }
    }
    
    console.log(`[SSE] Parsed ${dishes.length} dishes from text`);
    return dishes;
  }

  private async processOrder(orderData: any): Promise<void> {
    try {
      // Skip checkout receipts
      if (orderData.plain_text && orderData.plain_text.includes('结账单')) {
        console.log('[SSE] Skipping checkout receipt');
        return;
      }
      
      // Determine if it's a kitchen slip or customer order
      const isKitchenSlip = orderData.plain_text && orderData.plain_text.includes('制作分单');
      const isCustomerOrder = orderData.plain_text && (orderData.plain_text.includes('客单') || orderData.plain_text.includes('加菜'));
      
      // Extract table number and order type BEFORE logging
      let tableNo = 'unknown';
      let orderType = 'unknown';
      
      if (orderData.plain_text) {
        // Extract table number
        const tableMatch = orderData.plain_text.match(/桌号:\s*([^\n]+)/);
        if (tableMatch) {
          tableNo = tableMatch[1].trim();
        }
        
        // Determine order type
        if (isKitchenSlip) {
          orderType = 'kitchen_slip';
        } else if (isCustomerOrder) {
          orderType = 'customer_order';
        } else if (orderData.plain_text.includes('结账')) {
          orderType = 'checkout';
        }
        
        // Parse dishes for logging
        const dishes = this.parseDishesFromText(orderData.plain_text);
        orderData.items = dishes;
      }
      
      // Add extracted info to orderData for logging
      orderData.table_no = tableNo;
      orderData.type = orderType;
      
      console.log(`[SSE] Processing ${orderType} for table ${tableNo}: ${orderData.receipt_no}`);
      
      // Log order received with enriched data
      this.logger.logOrderReceived(orderData);
      
      const startTime = performance.now();
      
      // Process to Supabase - use instance variables that are updated from Worker
      const supabase = {
        url: this.supabaseUrl || this.env.NEXT_PUBLIC_SUPABASE_URL,
        headers: {
          'apikey': this.supabaseServiceKey || this.env.SUPABASE_SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${this.supabaseServiceKey || this.env.SUPABASE_SERVICE_ROLE_KEY}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=representation'
        }
      };
      
      // Station mapping with hardcoded IDs
      const stationMap: Record<string, string> = {
        '荤菜': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
        '素菜': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
        '酒水': 'd4e5f6a7-b8c9-0123-defa-456789012345',
        '主食': 'e5f6a7b8-c9d0-1234-efab-567890123456',
        '汤品': 'f6a7b8c9-d0e1-2345-fabc-678901234567',
        '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',
        '凉菜': 'a7b8c9d0-e1f2-3456-abcd-789012345678',
        '其他': 'a7b8c9d0-e1f2-3456-abcd-789012345678'
      };
      
      // Process customer orders to create order record
      if (isCustomerOrder) {
        // Use the already extracted table number
        // Process customer order - handle both old and new formats
        const processedOrder = {
          restaurant_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
          receipt_no: orderData.receipt_no || orderData.reference || orderData.orderReference,
          table_no: tableNo,
          order_type: 'dine_in',
          status: 'pending',
          raw_data: { text: orderData.plain_text || JSON.stringify(orderData) },
          ordered_at: orderData.timestamp || orderData.orderTime || new Date().toISOString(),
          source: 'printer_api'
        };
        
        // Insert order
        const orderResponse = await fetch(`${supabase.url}/rest/v1/order_orders`, {
          method: 'POST',
          headers: supabase.headers,
          body: JSON.stringify(processedOrder)
        });
        
        if (!orderResponse.ok) {
          const errorText = await orderResponse.text();
          this.logger.logSupabaseOperation('insert', 'order_orders', false, performance.now() - startTime, errorText);
          throw new Error(`Order insert failed: ${errorText}`);
        }
        
        const savedOrder = await orderResponse.json() as any[];
        this.logger.logSupabaseOperation('insert', 'order_orders', true, performance.now() - startTime);
        
        // Process dishes - try structured items first, then parse from text
        let dishesToProcess: any[] = [];
        
        if (orderData.items && Array.isArray(orderData.items)) {
          // Use structured items if available
          dishesToProcess = orderData.items.map((item: any) => ({
            name: item.name || item.dishName,
            quantity: item.quantity || 1,
            notes: item.notes || item.modifiers?.join(', ') || null
          }));
        } else if (orderData.plain_text) {
          // Parse dishes from plain text
          const parsedDishes = this.parseDishesFromText(orderData.plain_text);
          dishesToProcess = parsedDishes.map(dish => ({
            name: dish.name,
            quantity: dish.quantity,
            notes: null
          }));
        }
        
        if (dishesToProcess.length > 0) {
          const dishes = dishesToProcess.map((dish: any) => ({
            order_id: savedOrder[0].id,
            name: dish.name,
            quantity: dish.quantity,
            station_id: null,
            status: 'pending',
            cooking_instructions: dish.notes
          }));
          
          const dishResponse = await fetch(`${supabase.url}/rest/v1/order_dishes`, {
            method: 'POST',
            headers: supabase.headers,
            body: JSON.stringify(dishes)
          });
          
          if (!dishResponse.ok) {
            console.error('Dish insert failed:', await dishResponse.text());
          } else {
            this.logger.logSupabaseOperation('insert', 'order_dishes', true, performance.now() - startTime);
            console.log(`[SSE] Inserted ${dishes.length} dishes for order ${savedOrder[0].id}`);
          }
        } else {
          console.log('[SSE] No dishes found to process');
        }
        
        // Update processed count
        const count = await this.state.storage.get('ordersProcessed') as number || 0;
        await this.state.storage.put('ordersProcessed', count + 1);
        await this.state.storage.put('lastUpdate', new Date().toISOString());
        
        // Log successful processing
        this.logger.logOrderProcessed(
          savedOrder[0].id,
          orderData,
          performance.now() - startTime,
          'success'
        );
      }
      
      // Process kitchen slips to create dishes
      if (isKitchenSlip) {
        console.log('[SSE] Processing kitchen slip for dishes');
        
        // Use the already extracted table number
        
        // Extract station
        const stationMatch = orderData.plain_text.match(/档口:\s*([^\n]+)/);
        const stationName = stationMatch ? stationMatch[1].trim() : null;
        
        if (stationName && stationMap[stationName]) {
          const stationId = stationMap[stationName];
          console.log(`[SSE] Station: ${stationName} (${stationId})`);
          
          // Extract dishes from kitchen slip
          const dishSection = orderData.plain_text.split('菜品数量')[1]?.split('单号:')[0];
          if (dishSection) {
            const dishLines = dishSection.trim().split('\n').filter(line => line.trim());
            
            for (const dishLine of dishLines) {
              // Parse "木姜子鲜黄牛肉1/份" format
              // Extract the dish name by removing the quantity/unit part
              const trimmed = dishLine.trim();
              if (!trimmed) continue;
              
              const dishName = trimmed.replace(/\d+\/[份瓶听盒个碗杯位].*$/, '').trim();
              const quantityMatch = trimmed.match(/(\d+)\/[份瓶听盒个碗杯位]/);
              const quantity = quantityMatch ? parseInt(quantityMatch[1]) : 1;
              
              if (dishName && dishName.length > 1) {
                const dishRecord = {
                  restaurant_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                  station_id: stationId,
                  receipt_no: orderData.receipt_no,
                  table_no: tableNo,
                  name: dishName,
                  quantity: quantity,
                  prep_time_minutes: 15,
                  status: 'pending',
                  notes: stationName,
                  raw_data: { text: orderData.plain_text }
                };
                
                const dishResponse = await fetch(`${supabase.url}/rest/v1/order_dishes`, {
                  method: 'POST',
                  headers: supabase.headers,
                  body: JSON.stringify(dishRecord)
                });
                
                if (dishResponse.ok) {
                  const savedDish = await dishResponse.json() as any[];
                  console.log(`[SSE] Created dish: ${dishName} at ${stationName}`);
                  this.logger.logSupabaseOperation('insert', 'order_dishes', true, performance.now() - startTime);
                } else {
                  const errorText = await dishResponse.text();
                  console.error(`[SSE] Failed to create dish: ${errorText}`);
                  this.logger.logSupabaseOperation('insert', 'order_dishes', false, performance.now() - startTime, errorText);
                }
              }
            }
          }
        } else {
          console.log(`[SSE] Unknown station: ${stationName}`);
        }
        
        // Store kitchen slip in KV logs if available
        if (this.env.ORDER_LOGS) {
          const slipId = `slip_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
          await this.env.ORDER_LOGS.put(slipId, JSON.stringify({
            ...orderData,
            processedAt: new Date().toISOString(),
            type: 'kitchen_slip'
          }), {
            expirationTtl: 86400 * 7 // Keep for 7 days
          });
        }
        
        console.log(`[SSE] Kitchen slip processed for receipt: ${orderData.receipt_no}`);
      }
      
      // Always flush logs after processing
      if (this.logger.getBufferSize() > 0) {
        console.log(`[SSE] Flushing ${this.logger.getBufferSize()} events to Axiom`);
        await this.logger.flush();
      }
      
    } catch (error) {
      console.error('[SSE] Error processing order:', error);
      this.logger.logError('order.processing_failed', error instanceof Error ? error.message : 'Unknown error', {
        receiptNo: orderData.receipt_no,
        tableNo: orderData.table_no
      });
      await this.logger.flush();
    }
  }
}