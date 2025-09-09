"""
Order Processor - Local Supabase Integration
Replaces Cloudflare Worker with direct database operations
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import httpx
from supabase import create_client, Client
import asyncio
from threading import Thread
import queue
import time

logger = logging.getLogger(__name__)

@dataclass
class Dish:
    """Represents a dish from receipt"""
    name: str
    quantity: int
    station_id: Optional[str] = None
    is_return: bool = False  # Track if this is a returned dish

class OrderProcessor:
    """Process orders locally and send directly to Supabase"""
    
    # Fixed IDs from Worker
    RESTAURANT_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    
    # Station mapping from Worker
    STATION_MAP = {
        '荤菜': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
        '素菜': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
        '酒水': 'd4e5f6a7-b8c9-0123-defa-456789012345',
        '主食': 'e5f6a7b8-c9d0-1234-efab-567890123456',
        '汤品': 'f6a7b8c9-d0e1-2345-fabc-678901234567',
        '小吃': 'a7b8c9d0-e1f2-3456-abcd-789012345678',
        '凉菜': '581b60be-428a-4673-9147-2c197478392b',  # Fixed: unique UUID for cold dishes
        '其他': 'a7b8c9d0-e1f2-3456-abcd-789012345678'
    }
    
    # Dishes that should always go to cold dishes station regardless of receipt station
    COLD_DISHES_OVERRIDE = {
        '贵州非遗丝娃娃',  # Traditional cold vegetable wrap
        '野佐料擂椒皮蛋',  # Cold preserved egg with mashed pepper
        '贵阳非遗脆三丁',  # Cold crispy diced vegetables
        '木姜子鸡爪',      # Cold chicken feet
        '老醋花生',        # Vinegar peanuts
        '凉拌土豆丝',      # Cold shredded potato
        '拍黄瓜',         # Smashed cucumber
        '凉拌黄瓜',       # Cold cucumber
        '凉拌海带丝',      # Cold seaweed strips
    }
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None, 
                 axiom_token: str = None, axiom_dataset: str = 'kitchen-orders'):
        """Initialize with Supabase and Axiom credentials"""
        # Get from env if not provided
        self.supabase_url = supabase_url or os.environ.get('SUPABASE_URL')
        self.supabase_key = supabase_key or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        self.axiom_token = axiom_token or os.environ.get('AXIOM_TOKEN')
        self.axiom_dataset = axiom_dataset
        
        # Initialize Supabase client
        if self.supabase_url and self.supabase_key:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info(f"Supabase client initialized for {self.supabase_url}")
        else:
            self.supabase = None
            logger.warning("Supabase credentials not configured")
        
        # Retry queue for failed operations
        self.retry_queue = queue.Queue()
        self.retry_thread = None
        self.running = True
        self.start_retry_worker()
    
    def start_retry_worker(self):
        """Start background thread for retry processing"""
        def retry_worker():
            retry_delays = {}  # Track retry delays per receipt
            
            while self.running:
                try:
                    if not self.retry_queue.empty():
                        receipt_data = self.retry_queue.get(timeout=1)
                        receipt_no = receipt_data.get('receipt_no', 'unknown')
                        
                        # Exponential backoff
                        if receipt_no in retry_delays:
                            retry_delays[receipt_no] = min(retry_delays[receipt_no] * 2, 300)
                        else:
                            retry_delays[receipt_no] = 5
                        
                        time.sleep(retry_delays[receipt_no])
                        
                        try:
                            result = self.process_receipt(receipt_data)
                            logger.info(f"Retry successful for receipt {receipt_no}: {result}")
                            # Remove from retry delays on success
                            retry_delays.pop(receipt_no, None)
                        except Exception as e:
                            logger.error(f"Retry failed for {receipt_no}: {e}")
                            # Re-queue if not too many retries
                            if retry_delays[receipt_no] < 300:
                                self.retry_queue.put(receipt_data)
                            else:
                                logger.error(f"Max retries reached for {receipt_no}, discarding")
                                retry_delays.pop(receipt_no, None)
                except queue.Empty:
                    pass
                except Exception as e:
                    logger.error(f"Retry worker error: {e}")
                
                time.sleep(5)  # Check every 5 seconds
        
        self.retry_thread = Thread(target=retry_worker, daemon=True)
        self.retry_thread.start()
        logger.info("Retry worker thread started")
    
    def stop(self):
        """Stop the retry worker"""
        self.running = False
        if self.retry_thread:
            self.retry_thread.join(timeout=10)
    
    def extract_table_number(self, text: str) -> str:
        """Extract table number from receipt text"""
        if not text:
            return '未知'
        
        # Try to match table number pattern
        table_match = re.search(r'桌号[:：]\s*([^\n]+)', text)
        if table_match:
            return table_match.group(1).strip()
        
        return '未知'
    
    def is_kitchen_slip(self, receipt_data: Dict) -> bool:
        """Determine if this is a kitchen slip or customer order"""
        text = receipt_data.get('plain_text', '')
        order_type = receipt_data.get('type', '')
        
        # Check explicit type
        if order_type == 'kitchenSlip':
            return True
        
        # Check text markers
        if '制作分单' in text or '(加菜)制作分单' in text:
            return True
        
        return False
    
    def should_skip_receipt(self, text: str) -> Tuple[bool, str]:
        """Check if receipt should be skipped"""
        if not text:
            return False, ""
        
        # Skip pre-checkout bills
        if '预结单' in text:
            return True, "Pre-checkout bill skipped"
        
        # Skip final checkout bills
        if '结账单' in text:
            return True, "Checkout bill logged"
        
        return False, ""
    
    def is_return_slip(self, text: str) -> bool:
        """Check if this is a return dish slip (退菜单)"""
        return '退菜单' in text or '退菜原因' in text
    
    def extract_return_reason(self, text: str) -> Optional[str]:
        """Extract return reason from receipt"""
        match = re.search(r'退菜原因[:：]\s*([^\n]+)', text)
        return match.group(1).strip() if match else None
    
    def parse_customer_dishes(self, text: str) -> List[Dish]:
        """Parse dishes from customer order text (客单 format)"""
        dishes = []
        if not text:
            return dishes
        
        # Look for dishes section between markers
        dish_section_match = re.search(
            r'菜品[单价]*数量[小计]*\n([\s\S]*?)(?:菜品价格合计|\n\n|$)',
            text
        )
        if not dish_section_match:
            return dishes
        
        dish_section = dish_section_match.group(1)
        lines = dish_section.split('\n')
        
        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue
            
            # Skip modifiers (start with -)
            if trimmed.startswith('-'):
                continue
            
            # Real format from API: "野菜卷181份18" or "紫苏半边云（鲜牛胸口）381份38"
            # Pattern: dish_name + price + quantity + unit + subtotal
            # Use non-greedy match and look for the last occurrence of digit+unit pattern
            match = re.match(r'^(.+?)(\d+)(\d)([份瓶听盒位杯碗个张])(\d+)$', trimmed)
            if match:
                name = match.group(1).strip()
                # The regex might be too greedy, let's validate the name doesn't end with a digit
                # If it does, we need to adjust the parsing
                if name and name[-1].isdigit():
                    # Try to find the actual dish name by looking for the pattern more carefully
                    # Find the last occurrence of digit+digit+unit+digit pattern
                    better_match = re.search(r'^(.*?)(\d{1,3})(\d)([份瓶听盒位杯碗个张])(\d+)$', trimmed)
                    if better_match:
                        name = better_match.group(1).strip()
                        quantity = int(better_match.group(3))
                else:
                    quantity = int(match.group(3))  # The digit before unit is quantity
                
                if name and quantity > 0:
                    dishes.append(Dish(name=name, quantity=quantity))
                    logger.debug(f"Parsed customer dish: {name} x{quantity}")
            else:
                # Fallback for simpler format
                simple_match = re.match(r'^(.+?)(?:\d+[份瓶听盒位杯碗个张]\d+|\d+)$', trimmed)
                if simple_match:
                    name = simple_match.group(1).strip()
                    if name and not name[0].isdigit():
                        dishes.append(Dish(name=name, quantity=1))
                        logger.debug(f"Parsed customer dish (fallback): {name} x1")
        
        logger.info(f"Parsed {len(dishes)} dishes from customer order")
        return dishes
    
    def parse_kitchen_slip_dishes(self, text: str) -> List[Dish]:
        """Parse dishes from kitchen slip text (制作分单 format)"""
        dishes = []
        if not text:
            return dishes
        
        # Look for dishes section after "菜品数量"
        dish_section_match = re.search(r'菜品数量\n([\s\S]*?)(\n单号:|$)', text)
        if not dish_section_match:
            return dishes
        
        dish_section = dish_section_match.group(1)
        lines = dish_section.split('\n')
        
        i = 0
        combo_meal_active = False  # Track if we're processing a combo meal
        
        while i < len(lines):
            trimmed = lines[i].strip()
            if not trimmed:
                i += 1
                continue
            
            # Check if this is a combo meal sub-item (starts with -)
            if trimmed.startswith('-'):
                if combo_meal_active:
                    # Process the actual dish from combo meal
                    sub_item = trimmed[1:].strip()  # Remove the "-" prefix
                    
                    # Check for quantity pattern in sub-item
                    if re.search(r'\d+\/[份瓶听盒个碗杯位]', sub_item):
                        # Extract dish name and quantity
                        dish_name = re.sub(r'\d+\/[份瓶听盒个碗杯位].*$', '', sub_item).strip()
                        quantity_match = re.search(r'(\d+)\/[份瓶听盒个碗杯位]', sub_item)
                        quantity = int(quantity_match.group(1)) if quantity_match else 1
                        
                        if dish_name and len(dish_name) > 1:
                            dishes.append(Dish(name=dish_name, quantity=quantity, is_return=False))
                            logger.debug(f"Parsed combo dish: {dish_name} x{quantity}")
                i += 1
                continue
            
            # Check for dishes with quantity/unit pattern
            if re.search(r'\d+\/[份瓶听盒个碗杯位]', trimmed):
                # Check if this is a return dish
                is_return = False
                if '(退)' in trimmed:
                    is_return = True
                    # Remove (退) prefix for dish name extraction
                    trimmed_for_name = trimmed.replace('(退)', '')
                else:
                    trimmed_for_name = trimmed
                
                # Extract dish name by removing quantity/unit part
                dish_line = re.sub(r'\d+\/[份瓶听盒个碗杯位].*$', '', trimmed_for_name).strip()
                
                # Check if this is a combo meal header
                if '美团团购' in dish_line or '套餐' in dish_line or 'Chill' in dish_line:
                    # This is a combo meal header - check if it's split across lines
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # Check if next line continues the combo name (no quantity pattern)
                        if not re.search(r'\d+\/[份瓶听盒个碗杯位]', next_line) and not next_line.startswith('-'):
                            # Combine the combo name
                            dish_line = dish_line + next_line
                            i += 1  # Skip the next line
                    
                    # Set flag to process sub-items
                    combo_meal_active = True
                    logger.debug(f"Found combo meal: {dish_line}, will process sub-items")
                    i += 1
                    continue  # Skip the combo header itself
                
                # Reset combo flag if we hit a non-combo dish
                combo_meal_active = False
                
                # Check if dish name has unclosed parenthesis (multi-line dish)
                if '（' in dish_line and '）' not in dish_line:
                    # Look for continuation on next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if '）' in next_line and not re.search(r'\d+\/[份瓶听盒个碗杯位]', next_line):
                            # Combine the lines
                            dish_line = dish_line + next_line
                            i += 1  # Skip the next line since we've processed it
                
                if dish_line and len(dish_line) > 1:
                    # Extract quantity if possible
                    quantity_match = re.search(r'(\d+)\/[份瓶听盒个碗杯位]', trimmed)
                    quantity = int(quantity_match.group(1)) if quantity_match else 1
                    
                    dishes.append(Dish(name=dish_line, quantity=quantity, is_return=is_return))
                    if is_return:
                        logger.debug(f"Parsed RETURN dish: {dish_line} x{quantity}")
                    else:
                        logger.debug(f"Parsed kitchen dish: {dish_line} x{quantity}")
            
            i += 1
        
        logger.info(f"Parsed {len(dishes)} dishes from kitchen slip")
        return dishes
    
    def get_station_from_text(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract station name and ID from kitchen slip"""
        if not text:
            return None, None
        
        station_match = re.search(r'档口[:：]\s*([^\n]+)', text)
        if station_match:
            station_name = station_match.group(1).strip()
            station_id = self.STATION_MAP.get(station_name)
            logger.info(f"Found station: {station_name} -> {station_id}")
            return station_name, station_id
        
        return None, None
    
    def parse_timestamp(self, timestamp_str: str) -> str:
        """Parse timestamp from various formats to ISO format
        
        Handles:
        - Chinese format: "打印时间: 2025-09-06 22:24:38"
        - ISO format: "2025-09-06T22:24:38.123456"
        - Falls back to current UTC time if parsing fails
        """
        if not timestamp_str:
            return datetime.utcnow().isoformat()
        
        # If already in ISO format, return as is
        if 'T' in timestamp_str and not '打印时间' in timestamp_str:
            return timestamp_str
        
        # Extract datetime from Chinese format
        if '打印时间' in timestamp_str:
            # Remove the Chinese prefix
            timestamp_str = timestamp_str.replace('打印时间:', '').replace('打印时间：', '').strip()
        
        try:
            # Parse the datetime string "2025-09-06 22:24:38"
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            # Convert to ISO format with timezone info
            return dt.isoformat() + 'Z'
        except ValueError:
            try:
                # Try alternative format without seconds
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                return dt.isoformat() + 'Z'
            except ValueError:
                logger.warning(f"Could not parse timestamp: {timestamp_str}, using current time")
                return datetime.utcnow().isoformat()
    
    def log_to_axiom_sync(self, event_data: Dict):
        """Send monitoring event to Axiom (synchronous version)"""
        if not self.axiom_token:
            return
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    f'https://api.axiom.co/v1/datasets/{self.axiom_dataset}/ingest',
                    json=[{
                        **event_data,
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'local_printer_api'
                    }],
                    headers={
                        'Authorization': f'Bearer {self.axiom_token}',
                        'Content-Type': 'application/json'
                    },
                    timeout=5
                )
                if response.status_code != 200:
                    logger.warning(f"Axiom logging returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Axiom logging failed: {e}")
    
    def process_receipt(self, receipt_data: Dict) -> Dict[str, Any]:
        """Process a receipt and send to Supabase - main entry point"""
        try:
            text = receipt_data.get('plain_text', '')
            receipt_no = receipt_data.get('receipt_no')
            timestamp = receipt_data.get('timestamp', datetime.utcnow().isoformat())
            
            logger.info(f"Processing receipt {receipt_no}")
            
            # Extract table number
            table_no = self.extract_table_number(text)
            # Override with explicit fields if present
            if receipt_data.get('tableNumber') or receipt_data.get('table') or receipt_data.get('table_no'):
                table_no = receipt_data.get('tableNumber') or receipt_data.get('table') or receipt_data.get('table_no')
            
            # Log order received
            self.log_to_axiom_sync({
                'event': 'order.received',
                'receipt_no': receipt_no,
                'table_no': table_no
            })
            
            # Check if should skip
            should_skip, skip_reason = self.should_skip_receipt(text)
            if should_skip:
                logger.info(f"Skipping receipt {receipt_no}: {skip_reason}")
                if '结账单' in text:
                    self.log_to_axiom_sync({
                        'event': 'order.checkout',
                        'receipt_no': receipt_no,
                        'table_no': table_no
                    })
                return {'success': True, 'message': skip_reason}
            
            # Check if this is a return slip
            if self.is_return_slip(text):
                return self.process_return_slip(receipt_data, text, table_no)
            
            # Process based on type
            if self.is_kitchen_slip(receipt_data):
                return self.process_kitchen_slip(receipt_data, text, table_no)
            else:
                return self.process_customer_order(receipt_data, text, table_no)
                
        except Exception as e:
            logger.error(f"Order processing failed for {receipt_data.get('receipt_no')}: {e}")
            # Add to retry queue
            self.retry_queue.put(receipt_data)
            
            self.log_to_axiom_sync({
                'event': 'order.error',
                'error': str(e),
                'receipt_no': receipt_data.get('receipt_no')
            })
            
            raise
    
    def process_return_slip(self, receipt_data: Dict, text: str, table_no: str) -> Dict:
        """Process return dish slip (退菜单)"""
        logger.info(f"Processing return slip for table {table_no}")
        
        # Extract return reason
        return_reason = self.extract_return_reason(text)
        logger.info(f"Return reason: {return_reason}")
        
        # Parse returned dishes (will have is_return=True)
        dishes = self.parse_kitchen_slip_dishes(text)
        
        if not dishes:
            return {'success': True, 'message': 'No dishes to return'}
        
        return_results = []
        
        for dish in dishes:
            if not dish.is_return:
                continue
                
            try:
                # Find the most recent matching dish for this table
                # Query order_dishes table for pending/preparing dishes
                result = self.supabase.table('order_dishes').select("*").eq(
                    'table_no', table_no
                ).eq(
                    'name', dish.name
                ).in_(
                    'status', ['pending', 'preparing']
                ).order(
                    'created_at', desc=True
                ).limit(1).execute()
                
                if result.data and len(result.data) > 0:
                    dish_record = result.data[0]
                    
                    # Update the dish status to 'returned'
                    update_result = self.supabase.table('order_dishes').update({
                        'status': 'returned',
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('id', dish_record['id']).execute()
                    
                    logger.info(f"Marked dish {dish.name} (id: {dish_record['id']}) as returned")
                    return_results.append({
                        'dish': dish.name,
                        'status': 'updated',
                        'original_id': dish_record['id']
                    })
                    
                    # Log the return event
                    self.log_to_axiom_sync({
                        'event': 'dish.returned',
                        'dish_id': dish_record['id'],
                        'dish_name': dish.name,
                        'table_no': table_no,
                        'return_reason': return_reason,
                        'receipt_no': receipt_data.get('receipt_no')
                    })
                else:
                    # No matching dish found - log warning but still track
                    logger.warning(f"No matching dish found for return: {dish.name} at table {table_no}")
                    
                    # Insert as a return record with negative quantity
                    self.supabase.table('order_dishes').insert({
                        'restaurant_id': self.RESTAURANT_ID,
                        'receipt_no': receipt_data.get('receipt_no'),
                        'name': dish.name,
                        'quantity': -dish.quantity,  # Negative to indicate return
                        'table_no': table_no,
                        'status': 'returned',
                        'station_id': None,
                        'prep_time_minutes': 0,
                        'urgency_level': 'normal'
                    }).execute()
                    
                    return_results.append({
                        'dish': dish.name,
                        'status': 'no_match_recorded'
                    })
                    
            except Exception as e:
                logger.error(f"Failed to process return for {dish.name}: {e}")
                return_results.append({
                    'dish': dish.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'success': True,
            'message': 'Return slip processed',
            'return_count': len([d for d in dishes if d.is_return]),
            'return_reason': return_reason,
            'results': return_results
        }
    
    def process_kitchen_slip(self, receipt_data: Dict, text: str, table_no: str) -> Dict:
        """Process kitchen slip (制作分单)"""
        logger.info(f"Processing kitchen slip for table {table_no}")
        
        # Get station info
        station_name, station_id = self.get_station_from_text(text)
        
        if not station_id:
            logger.warning(f"No station found for kitchen slip {receipt_data.get('receipt_no')}")
            return {'success': False, 'error': 'Station not found'}
        
        # Parse dishes
        dishes = self.parse_kitchen_slip_dishes(text)
        
        if not dishes:
            logger.warning(f"No dishes found in kitchen slip {receipt_data.get('receipt_no')}")
            return {'success': True, 'message': 'No dishes to process'}
        
        # Insert dishes to Supabase
        if self.supabase:
            dish_data = []
            for dish in dishes:
                # Check if this dish should be overridden to cold dishes station
                final_station_id = station_id
                final_station_name = station_name
                
                if dish.name in self.COLD_DISHES_OVERRIDE:
                    final_station_id = self.STATION_MAP['凉菜']
                    final_station_name = '凉菜'
                    logger.info(f"Overriding station for {dish.name}: {station_name} -> 凉菜")
                
                dish_data.append({
                    'restaurant_id': self.RESTAURANT_ID,
                    'receipt_no': receipt_data.get('receipt_no'),
                    'name': dish.name,
                    'quantity': dish.quantity,
                    'station_id': final_station_id,
                    'table_no': table_no,
                    'status': 'pending',
                    'prep_time_minutes': 10,
                    'urgency_level': 'normal'
                })
            
            try:
                result = self.supabase.table('order_dishes').insert(dish_data).execute()
                logger.info(f"Inserted {len(dishes)} kitchen dishes to Supabase")
                
                self.log_to_axiom_sync({
                    'event': 'kitchen_slip.processed',
                    'station': station_name,
                    'station_id': station_id,
                    'dish_count': len(dishes),
                    'table_no': table_no,
                    'receipt_no': receipt_data.get('receipt_no')
                })
                
                return {
                    'success': True,
                    'message': 'Kitchen slip processed',
                    'station': station_name,
                    'table_no': table_no,
                    'dish_count': len(dishes)
                }
            except Exception as e:
                logger.error(f"Failed to insert kitchen slip dishes: {e}")
                raise
        
        return {'success': False, 'error': 'Supabase not configured'}
    
    def process_customer_order(self, receipt_data: Dict, text: str, table_no: str) -> Dict:
        """Process customer order (客单)"""
        logger.info(f"Processing customer order for table {table_no}")
        
        if not self.supabase:
            return {'success': False, 'error': 'Supabase not configured'}
        
        # Create order record
        order_data = {
            'restaurant_id': self.RESTAURANT_ID,
            'receipt_no': receipt_data.get('receipt_no'),
            'table_no': table_no,
            'order_type': 'dine_in',
            'status': 'pending',
            'raw_data': {'text': text},
            'ordered_at': self.parse_timestamp(receipt_data.get('timestamp')),
            'source': 'printer_api'
        }
        
        try:
            # Insert order
            order_result = self.supabase.table('order_orders').insert(order_data).execute()
            order_id = order_result.data[0]['id']
            logger.info(f"Created order {order_id} in Supabase")
            
            # Parse and insert dishes
            dishes = self.parse_customer_dishes(text)
            
            if dishes:
                dish_data = []
                for dish in dishes:
                    dish_data.append({
                        'order_id': order_id,
                        'restaurant_id': self.RESTAURANT_ID,
                        'receipt_no': receipt_data.get('receipt_no'),
                        'name': dish.name,
                        'quantity': dish.quantity,
                        'station_id': None,  # Will be determined by kitchen
                        'table_no': table_no,
                        'status': 'pending',
                        'prep_time_minutes': 10,
                        'urgency_level': 'normal'
                    })
                
                self.supabase.table('order_dishes').insert(dish_data).execute()
                logger.info(f"Inserted {len(dishes)} customer dishes to Supabase")
            
            self.log_to_axiom_sync({
                'event': 'order.processed',
                'order_id': order_id,
                'receipt_no': receipt_data.get('receipt_no'),
                'table_no': table_no,
                'dish_count': len(dishes)
            })
            
            return {
                'success': True,
                'order_id': order_id,
                'table_no': table_no,
                'dish_count': len(dishes)
            }
            
        except Exception as e:
            logger.error(f"Failed to insert customer order: {e}")
            raise


# Test function
def test_processor():
    """Test the order processor with sample data"""
    processor = OrderProcessor()
    
    # Test customer order
    customer_receipt = {
        'receipt_no': 'TEST001',
        'timestamp': datetime.now().isoformat(),
        'plain_text': '''桌号: 8
菜品单价数量小计
野菜卷181份18
木姜子鲜黄牛肉521份52
菜品价格合计: 70'''
    }
    
    # Test kitchen slip
    kitchen_receipt = {
        'receipt_no': 'TEST002',
        'timestamp': datetime.now().isoformat(),
        'plain_text': '''制作分单
档口: 荤菜
桌号: 8
菜品数量
木姜子鲜黄牛肉1/份
单号: TEST002'''
    }
    
    try:
        result1 = processor.process_receipt(customer_receipt)
        print(f"Customer order result: {result1}")
        
        result2 = processor.process_receipt(kitchen_receipt)
        print(f"Kitchen slip result: {result2}")
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        processor.stop()


if __name__ == "__main__":
    # Run test if executed directly
    test_processor()