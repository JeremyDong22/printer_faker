"""
Axiom logging handler for centralized monitoring and observability.
Provides buffered logging with automatic flushing and graceful shutdown.
"""

import os
import logging
import threading
import time
import atexit
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from queue import Queue, Empty
import json

try:
    from axiom_py import Client as AxiomClient
except ImportError:
    print("Warning: axiom-py not installed. Axiom logging disabled.")
    AxiomClient = None


class AxiomHandler(logging.Handler):
    """
    Custom logging handler that sends logs to Axiom with buffering.
    
    Features:
    - Automatic buffering with configurable flush interval
    - Thread-safe batch processing
    - Graceful shutdown with atexit hooks
    - Structured logging with metadata enrichment
    - Automatic retry on failures
    """
    
    def __init__(
        self,
        dataset: str,
        token: Optional[str] = None,
        org_id: Optional[str] = None,
        flush_interval: float = 1.0,
        batch_size: int = 1000,
        max_retries: int = 3
    ):
        """
        Initialize the Axiom handler.
        
        Args:
            dataset: Axiom dataset name
            token: Axiom API token (or from env AXIOM_TOKEN)
            org_id: Axiom organization ID (optional)
            flush_interval: Seconds between automatic flushes
            batch_size: Maximum events before automatic flush
            max_retries: Number of retry attempts on failure
        """
        super().__init__()
        
        if not AxiomClient:
            raise ImportError("axiom-py is required for AxiomHandler")
        
        # Axiom configuration
        self.dataset = dataset
        self.token = token or os.getenv('AXIOM_TOKEN')
        self.org_id = org_id or os.getenv('AXIOM_ORG_ID')
        
        if not self.token:
            raise ValueError("AXIOM_TOKEN must be provided or set in environment")
        
        # Initialize Axiom client
        self.client = AxiomClient(
            token=self.token,
            org_id=self.org_id
        )
        
        # Buffering configuration
        self.flush_interval = flush_interval
        self.batch_size = batch_size
        self.max_retries = max_retries
        
        # Thread-safe event queue
        self.event_queue = Queue()
        self.shutdown_event = threading.Event()
        
        # Start background flush thread
        self.flush_thread = threading.Thread(
            target=self._flush_worker,
            daemon=True,
            name="AxiomFlushThread"
        )
        self.flush_thread.start()
        
        # Register shutdown hook
        atexit.register(self.close)
        
        # Service metadata
        self.service_metadata = {
            'service': 'printer-faker',
            'environment': os.getenv('ENVIRONMENT', 'production'),
            'hostname': os.uname().nodename,
            'version': '2.0'
        }
    
    def emit(self, record: logging.LogRecord):
        """
        Process a log record and add to queue.
        
        Args:
            record: Python LogRecord to process
        """
        try:
            # Format the log record into structured event
            event = self._format_event(record)
            
            # Add to queue (non-blocking)
            self.event_queue.put_nowait(event)
            
            # Trigger immediate flush if queue is full
            if self.event_queue.qsize() >= self.batch_size:
                self._flush_events()
                
        except Exception as e:
            # Fallback to stderr if Axiom fails
            self.handleError(record)
    
    def _format_event(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        Convert LogRecord to Axiom event format.
        
        Args:
            record: Python LogRecord
            
        Returns:
            Structured event dictionary
        """
        # Base event structure
        event = {
            '_time': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': self.format(record),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process,
            **self.service_metadata
        }
        
        # Add exception info if present
        if record.exc_info:
            event['exception'] = self.format(record)
            event['exception_type'] = record.exc_info[0].__name__
        
        # Add custom fields from extra
        if hasattr(record, 'event_type'):
            event['event_type'] = record.event_type
        if hasattr(record, 'receipt_no'):
            event['receipt_no'] = record.receipt_no
        if hasattr(record, 'duration_ms'):
            event['duration_ms'] = record.duration_ms
        if hasattr(record, 'client_ip'):
            event['client_ip'] = record.client_ip
        if hasattr(record, 'station'):
            event['station'] = record.station
        if hasattr(record, 'dishes_count'):
            event['dishes_count'] = record.dishes_count
        if hasattr(record, 'order_type'):
            event['order_type'] = record.order_type
            
        return event
    
    def _flush_worker(self):
        """
        Background thread that periodically flushes events to Axiom.
        """
        while not self.shutdown_event.is_set():
            try:
                # Wait for flush interval or shutdown signal
                if self.shutdown_event.wait(timeout=self.flush_interval):
                    break
                
                # Flush any pending events
                self._flush_events()
                
            except Exception as e:
                # Log error but keep thread running
                print(f"Axiom flush worker error: {e}")
    
    def _flush_events(self):
        """
        Flush all queued events to Axiom.
        """
        if self.event_queue.empty():
            return
        
        # Collect all pending events
        events = []
        try:
            while not self.event_queue.empty() and len(events) < self.batch_size:
                events.append(self.event_queue.get_nowait())
        except Empty:
            pass
        
        if not events:
            return
        
        # Send to Axiom with retries
        for attempt in range(self.max_retries):
            try:
                response = self.client.ingest_events(
                    dataset=self.dataset,
                    events=events
                )
                
                # Success - break retry loop
                break
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Final attempt failed - log error
                    print(f"Failed to send {len(events)} events to Axiom after {self.max_retries} attempts: {e}")
                    # Put events back in queue for next flush
                    for event in events:
                        try:
                            self.event_queue.put_nowait(event)
                        except:
                            pass
                else:
                    # Retry with exponential backoff
                    time.sleep(2 ** attempt)
    
    def flush(self):
        """
        Manually trigger a flush of pending events.
        """
        self._flush_events()
    
    def close(self):
        """
        Gracefully shutdown the handler.
        """
        # Signal shutdown
        self.shutdown_event.set()
        
        # Final flush
        self._flush_events()
        
        # Wait for flush thread to finish
        if self.flush_thread.is_alive():
            self.flush_thread.join(timeout=5)
        
        # Close Axiom client
        if hasattr(self.client, 'close'):
            self.client.close()
        
        super().close()


class AxiomLogger:
    """
    Convenience class for structured logging to Axiom.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Wrap a logger with Axiom-specific methods.
        
        Args:
            logger: Python logger instance
        """
        self.logger = logger
    
    def log_event(
        self,
        event_type: str,
        message: str,
        level: int = logging.INFO,
        **kwargs
    ):
        """
        Log a structured event to Axiom.
        
        Args:
            event_type: Type of event (e.g., 'receipt_processed')
            message: Log message
            level: Log level
            **kwargs: Additional fields to include
        """
        extra = {'event_type': event_type, **kwargs}
        self.logger.log(level, message, extra=extra)
    
    def log_receipt(
        self,
        receipt_no: str,
        order_type: str,
        message: str,
        **kwargs
    ):
        """
        Log receipt processing event.
        """
        self.log_event(
            'receipt_processed',
            message,
            receipt_no=receipt_no,
            order_type=order_type,
            **kwargs
        )
    
    def log_error(
        self,
        error_type: str,
        message: str,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """
        Log error event with context.
        """
        extra = {
            'event_type': f'error_{error_type}',
            **kwargs
        }
        
        if exception:
            self.logger.error(message, exc_info=exception, extra=extra)
        else:
            self.logger.error(message, extra=extra)
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        **kwargs
    ):
        """
        Log performance metrics.
        """
        self.log_event(
            f'performance_{operation}',
            f"{operation} completed in {duration_ms:.2f}ms",
            level=logging.INFO if success else logging.WARNING,
            duration_ms=duration_ms,
            success=success,
            **kwargs
        )


def setup_axiom_logging(
    logger: logging.Logger,
    dataset: str,
    token: Optional[str] = None,
    level: int = logging.INFO
) -> AxiomLogger:
    """
    Setup Axiom logging for a logger.
    
    Args:
        logger: Logger to configure
        dataset: Axiom dataset name
        token: Axiom API token (optional, uses env)
        level: Minimum log level
        
    Returns:
        AxiomLogger wrapper for structured logging
    """
    try:
        # Create and add Axiom handler
        axiom_handler = AxiomHandler(dataset=dataset, token=token)
        axiom_handler.setLevel(level)
        
        # Add formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        axiom_handler.setFormatter(formatter)
        
        # Add to logger
        logger.addHandler(axiom_handler)
        
        # Return wrapper
        return AxiomLogger(logger)
        
    except Exception as e:
        print(f"Failed to setup Axiom logging: {e}")
        # Return wrapper without handler (logs locally only)
        return AxiomLogger(logger)