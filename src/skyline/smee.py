import json
import logging
import threading
import time
import requests
import sseclient
from urllib.parse import urlparse

logging.basicConfig(format='[%(asctime)s %(threadName)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SmeeClient:
    """A simple client for smee.io that forwards webhooks to a target URL."""
    
    def __init__(self, target_url):
        """Initialize the client with a target URL to forward webhooks to."""
        self.target_url = target_url
        self.should_stop = False
        self.connected = False
        self._thread = None
    
    def create_channel(self):
        """Create a new smee.io channel and return its URL."""
        # First make a GET request to get redirected to a new channel
        response = requests.get("https://smee.io/new", allow_redirects=True)
        # The final URL after redirect is our channel
        channel_url = response.url
        # Verify it's a valid smee.io URL
        parsed = urlparse(channel_url)
        if not parsed.netloc.endswith('smee.io'):
            raise ValueError(f"Invalid smee.io URL: {channel_url}")
        return channel_url
    
    def start(self, source_url):
        """Start listening for events on the source URL and forward them to target."""
        def _run():
            logger.info(f"Connecting to {source_url}")
            
            while not self.should_stop:
                try:
                    # Get the response object first
                    response = requests.get(source_url, stream=True)
                    client = sseclient.SSEClient(response)
                    self.connected = True
                    
                    # Use client.events() for iteration
                    for msg in client.events():
                        if self.should_stop:
                            self.connected = False
                            return
                            
                        if msg.event == 'ping':
                            logger.debug(f'Received ping {msg.id}')
                        elif msg.event == 'message':
                            self._forward_webhook(msg.data)
                        elif msg.event == 'ready':
                            logger.info(f'Connected to {source_url}')
                        elif msg.event == 'error':
                            logger.error(f'Error received: {msg}')
                        else:
                            logger.warning(f'Unknown event {msg.event}: {msg}')
                            
                except Exception as e:
                    logger.error(f'Connection error: {e}')
                    self.connected = False
                    if not self.should_stop:
                        time.sleep(3)  # Wait before reconnecting
        
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        
        # Wait for initial connection
        start_time = time.time()
        while not self.connected and (time.time() - start_time) < 10:
            if self.should_stop:
                break
            time.sleep(0.1)
        
        return self.connected
    
    def _forward_webhook(self, data):
        """Forward a webhook payload to the target URL."""
        try:
            # Parse the smee.io event data
            event_data = json.loads(data)
            
            # Extract headers and body
            headers = {k: str(v) for k, v in event_data.items() 
                      if k not in ('query', 'body', 'host')}
            body = event_data.get('body', {})
            
            # Forward to target
            response = requests.post(self.target_url, 
                                   json=body,
                                   headers=headers)
            
            logger.info(f'Forwarded webhook to {self.target_url} - {response.status_code}')
            
        except Exception as e:
            logger.error(f'Error forwarding webhook: {e}')
    
    def stop(self):
        """Stop the client."""
        self.should_stop = True
        if self._thread:
            self._thread.join(timeout=1)
