/**
 * Kitchen Order API - Cloudflare Workers
 * Handles SSE streaming, API logging, and Supabase integration
 * Replaces local services (api-logger and supabase-integration)
 */

/// <reference types="@cloudflare/workers-types" />

import { AxiomLogger } from './logger';
import { SSEListener } from './sse-listener';

// Export the Durable Object class
export { SSEListener };

export interface Env {
  API_URL: string;
  API_AUTH_TOKEN: string;
  NEXT_PUBLIC_SUPABASE_URL: string;
  NEXT_PUBLIC_SUPABASE_ANON_KEY: string;
  SUPABASE_SERVICE_ROLE_KEY: string;
  CACHE: KVNamespace;
  ORDER_LOGS?: KVNamespace; // Optional KV for order logging
  AXIOM_TOKEN?: string; // Axiom API token for logging
  AXIOM_DATASET?: string; // Axiom dataset name (defaults to 'kitchen-orders')
  SSE_LISTENER: DurableObjectNamespace; // Durable Object for SSE connection
}

// Supabase client helper
function createSupabaseClient(env: Env) {
  return {
    url: env.NEXT_PUBLIC_SUPABASE_URL,
    headers: {
      'apikey': env.SUPABASE_SERVICE_ROLE_KEY,
      'Authorization': `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
      'Content-Type': 'application/json',
      'Prefer': 'return=representation'
    }
  };
}

// Process and save order to Supabase
async function processOrderToSupabase(orderData: any, env: Env, logger: AxiomLogger): Promise<Response> {
  const supabase = createSupabaseClient(env);
  const startTime = performance.now();
  
  try {
    // Extract table number from plain_text if available
    let tableNo = '未知';
    if (orderData.plain_text) {
      const tableMatch = orderData.plain_text.match(/桌号:\s*([^\n]+)/);
      tableNo = tableMatch ? tableMatch[1].trim() : '未知';
    }
    // Also check for explicit table fields
    if (orderData.tableNumber || orderData.table || orderData.table_no) {
      tableNo = orderData.tableNumber || orderData.table || orderData.table_no;
    }
    
    // Log order received with extracted table number
    logger.logOrderReceived({
      ...orderData,
      table_no: tableNo
    });
    
    // Determine order type - check kitchen slip FIRST
    let orderType = orderData.type || '';
    
    // Skip pre-checkout bills (they don't have receipt numbers)
    if (orderData.plain_text && orderData.plain_text.includes('预结单')) {
      console.log('Skipping pre-checkout bill (no receipt number)');
      return new Response(JSON.stringify({ 
        success: true, 
        message: 'Pre-checkout bill skipped' 
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Skip final checkout bills (they're just payment receipts)
    if (orderData.plain_text && orderData.plain_text.includes('结账单')) {
      console.log('Skipping final checkout bill (payment receipt only)');
      logger.log({
        event: 'order.checkout',
        receiptNo: orderData.receipt_no,
        timestamp: orderData.timestamp,
        tableNo: tableNo
      });
      return new Response(JSON.stringify({ 
        success: true, 
        message: 'Checkout bill logged' 
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Check if it's a kitchen slip (制作分单 or (加菜)制作分单) - MUST check this first
    if (orderType === 'kitchenSlip' || 
        (orderData.plain_text && (orderData.plain_text.includes('制作分单') || orderData.plain_text.includes('(加菜)制作分单')))) {
      // Kitchen slip processing - create dishes with station assignment
      console.log('Processing kitchen slip');
      
      // Extract station from plain text
      const stationMatch = orderData.plain_text.match(/档口:\s*([^\n]+)/);
      const stationName = stationMatch ? stationMatch[1].trim() : null;
      
      // Station mapping
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
      
      const stationId = stationName && stationMap[stationName] ? stationMap[stationName] : null;
      
      if (stationId) {
        // Parse dishes from kitchen slip
        const dishes = parseKitchenSlipDishes(orderData.plain_text);
        
        if (dishes.length > 0) {
          const dishData = dishes.map(dish => ({
            restaurant_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
            receipt_no: orderData.receipt_no,
            name: dish.name,
            quantity: dish.quantity,
            station_id: stationId,
            table_no: tableNo,
            status: 'pending',
            prep_time_minutes: 10,
            urgency_level: 'normal'
          }));
          
          const dishResponse = await fetch(`${supabase.url}/rest/v1/order_dishes`, {
            method: 'POST',
            headers: supabase.headers,
            body: JSON.stringify(dishData)
          });
          
          if (!dishResponse.ok) {
            console.error('Kitchen slip dish insert failed:', await dishResponse.text());
            return new Response(JSON.stringify({ 
              success: false, 
              error: 'Failed to insert kitchen slip dishes' 
            }), {
              status: 500,
              headers: { 'Content-Type': 'application/json' }
            });
          } else {
            logger.logSupabaseOperation('insert', 'order_dishes', true, performance.now() - startTime);
            logger.log({
              event: 'kitchen_slip.processed',
              station: stationName,
              stationId,
              dishCount: dishes.length,
              tableNo
            });
          }
        }
      }
      
      return new Response(JSON.stringify({ 
        success: true, 
        message: 'Kitchen slip processed',
        station: stationName,
        tableNo,
        dishCount: stationId ? parseKitchenSlipDishes(orderData.plain_text).length : 0
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
      
    } else if (orderType === 'order' || orderType === 'customerOrder' || orderType === '' ||
               (orderData.plain_text && orderData.plain_text.includes('客单'))) {
      // Customer order processing - match local service format
      let processedOrder: any = {
        restaurant_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        receipt_no: orderData.reference || orderData.orderReference || orderData.receipt_no,
        table_no: tableNo,
        order_type: 'dine_in',
        status: 'pending',
        raw_data: { text: orderData.plain_text || JSON.stringify(orderData) },
        ordered_at: orderData.orderTime || orderData.timestamp || new Date().toISOString(),
        source: 'printer_api'
      };
      
      // Insert order to correct table
      const supabaseStartTime = performance.now();
      const orderResponse = await fetch(`${supabase.url}/rest/v1/order_orders`, {
        method: 'POST',
        headers: supabase.headers,
        body: JSON.stringify(processedOrder)
      });
      
      if (!orderResponse.ok) {
        const errorText = await orderResponse.text();
        logger.logSupabaseOperation('insert', 'order_orders', false, performance.now() - supabaseStartTime, errorText);
        throw new Error(`Order insert failed: ${errorText}`);
      }
      
      const savedOrder = await orderResponse.json() as any[];
      logger.logSupabaseOperation('insert', 'order_orders', true, performance.now() - supabaseStartTime);
      
      // Process dishes if present in structured format
      if (orderData.items && Array.isArray(orderData.items)) {
        const dishes = orderData.items.map((item: any) => ({
          order_id: savedOrder[0].id,
          restaurant_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
          receipt_no: orderData.receipt_no,
          name: item.name || item.dishName,
          quantity: item.quantity || 1,
          station_id: null,
          table_no: tableNo,
          status: 'pending',
          prep_time_minutes: 10,
          urgency_level: 'normal'
        }));
        
        const dishResponse = await fetch(`${supabase.url}/rest/v1/order_dishes`, {
          method: 'POST',
          headers: supabase.headers,
          body: JSON.stringify(dishes)
        });
        
        if (!dishResponse.ok) {
          console.error('Dish insert failed:', await dishResponse.text());
        }
      } else if (orderData.plain_text) {
        // Try to parse dishes from plain text
        const dishes = parseDishesFromText(orderData.plain_text);
        if (dishes.length > 0) {
          const dishData = dishes.map(dish => ({
            order_id: savedOrder[0].id,
            restaurant_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
            receipt_no: orderData.receipt_no,
            name: dish.name,
            quantity: dish.quantity,
            station_id: null,
            table_no: tableNo,
            status: 'pending',
            prep_time_minutes: 10,
            urgency_level: 'normal'
          }));
          
          const dishResponse = await fetch(`${supabase.url}/rest/v1/order_dishes`, {
            method: 'POST',
            headers: supabase.headers,
            body: JSON.stringify(dishData)
          });
          
          if (!dishResponse.ok) {
            console.error('Dish insert from text failed:', await dishResponse.text());
          } else {
            logger.logSupabaseOperation('insert', 'order_dishes', true, performance.now() - supabaseStartTime);
          }
        }
      }
      
      // Log successful order processing
      logger.logOrderProcessed(
        savedOrder[0].id,
        orderData,
        performance.now() - startTime,
        'success'
      );
      
      return new Response(JSON.stringify({ success: true, order: savedOrder[0] }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return new Response(JSON.stringify({ success: false, error: 'Unknown order type' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error: any) {
    console.error('Supabase processing error:', error);
    logger.logError('supabase.processing_failed', error.message, {
      receiptNo: orderData.receipt_no,
      tableNo: orderData.table_no
    });
    logger.logOrderProcessed(
      'unknown',
      orderData,
      performance.now() - startTime,
      'failed',
      error.message
    );
    return new Response(JSON.stringify({ success: false, error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Helper function to parse dishes from customer order text (客单 format)
function parseDishesFromText(text: string): Array<{name: string, quantity: number}> {
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
        }
      }
    }
  }
  
  return dishes;
}

// Helper function to parse dishes from kitchen slip text (制作分单 format)
function parseKitchenSlipDishes(text: string): Array<{name: string, quantity: number}> {
  const dishes: Array<{name: string, quantity: number}> = [];
  if (!text) return dishes;
  
  // Look for the dishes section after "菜品数量"
  const dishSectionMatch = text.match(/菜品数量\n([\s\S]*?)(\n单号:|$)/);
  if (!dishSectionMatch) return dishes;
  
  const dishSection = dishSectionMatch[1];
  const lines = dishSection.split('\n');
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    
    // Skip modifiers (start with -)
    if (trimmed.startsWith('-')) continue;
    
    // Real kitchen slip format from API: "木姜子鲜黄牛肉1/份"
    // Format is: dish_name + quantity + "/" + unit
    // Extract the dish name by removing the quantity/unit part
    const dishLine = trimmed.replace(/\d+\/[份瓶听盒个碗杯位].*$/, '').trim();
    
    if (dishLine && dishLine.length > 1) {
      // Extract quantity if possible
      const quantityMatch = trimmed.match(/(\d+)\/[份瓶听盒个碗杯位]/);
      const quantity = quantityMatch ? parseInt(quantityMatch[1]) : 1;
      
      dishes.push({ name: dishLine, quantity });
    }
  }
  
  return dishes;
}

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext
  ): Promise<Response> {
    const url = new URL(request.url);
    
    // Initialize Axiom logger
    const logger = new AxiomLogger(env.AXIOM_TOKEN, env.AXIOM_DATASET || 'kitchen-orders');
    
    // CORS headers for browser access
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // Handle preflight requests
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Health check endpoint
    if (url.pathname === '/api/health') {
      return new Response(JSON.stringify({ 
        status: 'healthy',
        timestamp: new Date().toISOString(),
        env: {
          api_configured: !!env.API_URL,
          supabase_configured: !!env.NEXT_PUBLIC_SUPABASE_URL,
          cache_available: !!env.CACHE
        }
      }), {
        headers: { 
          ...corsHeaders,
          'Content-Type': 'application/json' 
        },
      });
    }

    // Process order to Supabase endpoint
    if (url.pathname === '/api/process-order' && request.method === 'POST') {
      try {
        const orderData = await request.json();
        const result = await processOrderToSupabase(orderData, env, logger);
        
        // Flush logs to Axiom
        ctx.waitUntil(logger.flush());
        
        return new Response(result.body, {
          status: result.status,
          headers: {
            ...corsHeaders,
            ...Object.fromEntries(result.headers.entries())
          }
        });
      } catch (error: any) {
        logger.logError('request.process_order_failed', error.message);
        ctx.waitUntil(logger.flush());
        
        return new Response(JSON.stringify({ error: error.message }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Log order endpoint (stores to KV for later processing)
    if (url.pathname === '/api/log-order' && request.method === 'POST') {
      try {
        const orderData = await request.json();
        const orderId = `order_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
        
        // Store in KV if available
        if (env.ORDER_LOGS) {
          await env.ORDER_LOGS.put(orderId, JSON.stringify({
            ...orderData,
            timestamp: new Date().toISOString(),
            processed: false
          }), {
            expirationTtl: 86400 * 7 // Keep for 7 days
          });
        }
        
        // Also try to process to Supabase immediately
        ctx.waitUntil(processOrderToSupabase(orderData, env, logger));
        
        // Log the order logging event
        logger.log({
          event: 'order.logged_to_kv',
          orderId,
          receiptNo: orderData.receipt_no,
          tableNo: orderData.table_no
        });
        ctx.waitUntil(logger.flush());
        
        return new Response(JSON.stringify({ success: true, orderId }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error: any) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Get logged orders (for debugging/recovery)
    if (url.pathname === '/api/logged-orders' && env.ORDER_LOGS) {
      const limit = parseInt(url.searchParams.get('limit') || '100');
      const list = await env.ORDER_LOGS.list({ limit });
      
      const orders = await Promise.all(
        list.keys.map(async (key) => {
          const value = await env.ORDER_LOGS!.get(key.name);
          return value ? JSON.parse(value) : null;
        })
      );
      
      return new Response(JSON.stringify(orders.filter(Boolean)), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // SSE proxy endpoint with integrated logging
    if (url.pathname === '/api/stream') {
      const auth = url.searchParams.get('auth');
      
      // Verify auth token
      if (auth !== env.API_AUTH_TOKEN) {
        return new Response('Unauthorized', { 
          status: 401,
          headers: corsHeaders 
        });
      }

      try {
        // Build the correct upstream URL
        const sseUrl = `${env.API_URL}?auth=${auth}`; // API_URL already includes /api/stream
        const sseResponse = await fetch(sseUrl, {
          headers: {
            'Accept': 'text/event-stream',
          },
        });

        if (!sseResponse.ok) {
          return new Response('Upstream error', { 
            status: sseResponse.status,
            headers: corsHeaders 
          });
        }

        // Forward SSE stream
        return new Response(sseResponse.body, {
          headers: {
            ...corsHeaders,
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
          },
        });
      } catch (error) {
        console.error('SSE proxy error:', error);
        return new Response('Internal Server Error', { 
          status: 500,
          headers: corsHeaders 
        });
      }
    }

    // Durable Object control endpoints
    if (url.pathname.startsWith('/api/sse-listener/')) {
      // Get or create a Durable Object instance
      const id = env.SSE_LISTENER.idFromName('default-listener');
      const stub = env.SSE_LISTENER.get(id);
      
      // Extract the command from the path
      const command = url.pathname.replace('/api/sse-listener/', '');
      
      // Forward the request to the Durable Object
      const doUrl = new URL(request.url);
      doUrl.pathname = `/${command}`;
      const doRequest = new Request(doUrl.toString(), {
        method: request.method,
        headers: request.headers,
        body: request.body
      });
      
      const response = await stub.fetch(doRequest);
      
      // Add CORS headers to response
      const responseHeaders = new Headers(response.headers);
      Object.entries(corsHeaders).forEach(([key, value]) => {
        responseHeaders.set(key, value);
      });
      
      return new Response(response.body, {
        status: response.status,
        headers: responseHeaders
      });
    }

    // SSE Listener endpoints using Durable Objects
    if (url.pathname.startsWith('/api/sse/')) {
      const durableObjectId = env.SSE_LISTENER.idFromName('singleton');
      const durableObject = env.SSE_LISTENER.get(durableObjectId);
      
      // Pass the environment variables to the Durable Object
      const newUrl = new URL(request.url);
      newUrl.searchParams.set('axiomToken', env.AXIOM_TOKEN || '');
      newUrl.searchParams.set('axiomDataset', env.AXIOM_DATASET || 'kitchen-orders');
      newUrl.searchParams.set('supabaseUrl', env.NEXT_PUBLIC_SUPABASE_URL);
      newUrl.searchParams.set('supabaseKey', env.SUPABASE_SERVICE_ROLE_KEY);
      
      const newRequest = new Request(newUrl.toString(), request);
      const response = await durableObject.fetch(newRequest);
      
      return new Response(response.body, {
        status: response.status,
        headers: {
          ...corsHeaders,
          ...Object.fromEntries(response.headers.entries())
        }
      });
    }

    // Supabase info endpoint (for debugging)
    if (url.pathname === '/api/supabase-info') {
      return new Response(JSON.stringify({
        url: env.NEXT_PUBLIC_SUPABASE_URL,
        hasAnonKey: !!env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
        hasServiceKey: !!env.SUPABASE_SERVICE_ROLE_KEY,
        hasOrderLogs: !!env.ORDER_LOGS,
        hasSSEListener: !!env.SSE_LISTENER,
        endpoints: [
          '/api/stream - SSE proxy for live orders',
          '/api/process-order - Process order to Supabase',
          '/api/log-order - Log order for later processing',
          '/api/logged-orders - View logged orders',
          '/api/sse-listener/start - Start SSE connection to printer API',
          '/api/sse-listener/stop - Stop SSE connection',
          '/api/sse-listener/status - Get SSE connection status',
          '/api/health - Health check',
          '/api/supabase-info - Debug info'
        ]
      }), {
        headers: { 
          ...corsHeaders,
          'Content-Type': 'application/json' 
        },
      });
    }

    // Default response
    return new Response('Kitchen Order API - Worker Active', {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'text/plain',
      },
    });
  },
};