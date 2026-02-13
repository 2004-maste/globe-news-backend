"""
Custom middleware for the Globe News application.
"""
import time
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Middleware to log all incoming requests and responses."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        request = Request(scope, receive)
        
        # Log request
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = request.url.path
        query_params = str(request.query_params)
        
        logger.info(f"Request: {method} {url}?{query_params} from {client_ip}")
        
        # Process request
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                process_time = time.time() - start_time
                
                logger.info(
                    f"Response: {method} {url} - Status: {status_code} - "
                    f"Time: {process_time:.3f}s"
                )
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


class RateLimitMiddleware:
    """Simple rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute=100):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # Store request counts per IP
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old entries (more than 1 minute old)
        current_time = time.time()
        self.requests = {
            ip: [(t, count) for t, count in times if current_time - t < 60]
            for ip, times in self.requests.items()
        }
        
        # Check rate limit
        if client_ip in self.requests:
            total_requests = sum(count for _, count in self.requests[client_ip])
            if total_requests >= self.requests_per_minute:
                response = Response(
                    content=json.dumps({
                        "detail": "Rate limit exceeded. Please try again later."
                    }),
                    status_code=429,
                    media_type="application/json"
                )
                await response(scope, receive, send)
                return
        
        # Add request to tracking
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append((current_time, 1))
        
        await self.app(scope, receive, send)