/**
 * Axiom Logger for Cloudflare Workers
 * Provides structured logging and performance tracking for kitchen orders
 */

import { Axiom } from '@axiomhq/js';

export interface LogEvent {
  event: string;
  [key: string]: any;
}

export class AxiomLogger {
  private client: Axiom | null = null;
  private dataset: string;
  private buffer: LogEvent[] = [];
  private enabled: boolean = false;
  
  constructor(token?: string, dataset: string = 'kitchen-orders') {
    this.dataset = dataset;
    
    if (token) {
      try {
        this.client = new Axiom({
          token,
        });
        this.enabled = true;
      } catch (error) {
        console.error('Failed to initialize Axiom client:', error);
        this.enabled = false;
      }
    }
  }
  
  /**
   * Log an event to the buffer
   */
  log(event: LogEvent): void {
    const enrichedEvent = {
      ...event,
      _time: new Date().toISOString(),
      timestamp: new Date().toISOString(),
    };
    
    // Always log to console for debugging
    console.log(JSON.stringify(enrichedEvent));
    
    // Buffer events if Axiom is enabled
    if (this.enabled) {
      this.buffer.push(enrichedEvent);
    }
  }
  
  /**
   * Log order received event
   */
  logOrderReceived(orderData: any, request?: Request): void {
    this.log({
      event: 'order.received',
      receiptNo: orderData.receipt_no || orderData.reference,
      tableNo: orderData.table_no || orderData.tableNumber || 'unknown',
      orderType: orderData.type || 'unknown',
      rawSize: JSON.stringify(orderData).length,
      hasPlainText: !!orderData.plain_text,
      hasItems: !!(orderData.items && orderData.items.length > 0),
      cfRay: request?.headers.get('cf-ray') || null,
    });
  }
  
  /**
   * Log order processing result
   */
  logOrderProcessed(
    orderId: string,
    orderData: any,
    duration: number,
    status: 'success' | 'failed',
    error?: string
  ): void {
    this.log({
      event: 'order.processed',
      orderId,
      receiptNo: orderData.receipt_no || orderData.reference,
      tableNo: orderData.table_no || orderData.tableNumber || 'unknown',
      duration,
      status,
      dishCount: orderData.items?.length || 0,
      error: error || null,
    });
  }
  
  /**
   * Log Supabase operation
   */
  logSupabaseOperation(
    operation: string,
    table: string,
    success: boolean,
    duration: number,
    error?: string
  ): void {
    this.log({
      event: 'supabase.operation',
      operation,
      table,
      success,
      duration,
      error: error || null,
    });
  }
  
  /**
   * Log SSE connection event
   */
  logSSEConnection(status: 'connected' | 'disconnected' | 'error', error?: string): void {
    this.log({
      event: 'sse.connection',
      status,
      error: error || null,
    });
  }
  
  /**
   * Log error with context
   */
  logError(type: string, message: string, context?: any): void {
    this.log({
      event: 'error',
      type,
      message,
      context: context || {},
      stack: new Error().stack,
    });
  }
  
  /**
   * Flush buffered events to Axiom
   */
  async flush(): Promise<void> {
    if (!this.enabled || !this.client || this.buffer.length === 0) {
      return;
    }
    
    try {
      // Use the ingest method for the Axiom client
      await this.client.ingest(this.dataset, this.buffer);
      console.log(`Flushed ${this.buffer.length} events to Axiom`);
      this.buffer = [];
    } catch (error) {
      console.error('Failed to flush events to Axiom:', error);
      // Keep events in buffer for potential retry
    }
  }
  
  /**
   * Get buffer size (for monitoring)
   */
  getBufferSize(): number {
    return this.buffer.length;
  }
  
  /**
   * Check if logger is enabled
   */
  isEnabled(): boolean {
    return this.enabled;
  }
}