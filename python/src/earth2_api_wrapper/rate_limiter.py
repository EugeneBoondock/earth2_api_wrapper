"""
Rate limiting and abuse prevention for Earth2 API wrapper.
Protects Earth2's bandwidth by implementing multiple safeguards.
"""

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple
import hashlib
import os


class RateLimiter:
    """
    Multi-tier rate limiter to prevent API abuse and protect Earth2's bandwidth.
    
    Implements:
    - Per-endpoint rate limiting
    - Global request throttling
    - Burst protection
    - Exponential backoff on errors
    - Request caching
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # Per-endpoint rate limits (requests per minute)
        self._endpoint_limits = {
            'auth': 5,           # Authentication attempts
            'search': 30,        # Market searches
            'property': 60,      # Property lookups
            'leaderboard': 20,   # Leaderboard queries
            'user': 40,          # User info requests
            'resources': 30,     # Resource queries
            'default': 50        # Default for other endpoints
        }
        
        # Global limits
        self._global_limit = 200  # Total requests per minute
        self._burst_limit = 10    # Max requests in 10 seconds
        
        # Tracking structures
        self._endpoint_requests: Dict[str, deque] = defaultdict(lambda: deque())
        self._global_requests: deque = deque()
        self._burst_requests: deque = deque()
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._last_error_time: Dict[str, float] = defaultdict(float)
        
        # Simple in-memory cache for GET requests
        self._cache: Dict[str, Tuple[float, any]] = {}
        self._cache_ttl = 300  # 5 minutes default TTL
        
        # Usage tracking
        self._total_requests = 0
        self._blocked_requests = 0
        
    def _get_endpoint_category(self, url: str) -> str:
        """Categorize endpoint for rate limiting."""
        url_lower = url.lower()
        
        if 'auth' in url_lower or 'login' in url_lower:
            return 'auth'
        elif 'marketplace' in url_lower or 'search' in url_lower:
            return 'search'
        elif 'landfields' in url_lower and '/resources' not in url_lower:
            return 'property'
        elif 'leaderboard' in url_lower:
            return 'leaderboard'
        elif 'user_info' in url_lower or 'users' in url_lower:
            return 'user'
        elif 'resources' in url_lower:
            return 'resources'
        else:
            return 'default'
    
    def _clean_old_requests(self, request_queue: deque, window_seconds: int):
        """Remove requests older than the time window."""
        current_time = time.time()
        while request_queue and current_time - request_queue[0] > window_seconds:
            request_queue.popleft()
    
    def _get_cache_key(self, url: str, method: str = 'GET') -> str:
        """Generate cache key for request."""
        return hashlib.md5(f"{method}:{url}".encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[any]:
        """Get cached response if still valid."""
        if cache_key in self._cache:
            timestamp, response = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return response
            else:
                del self._cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, response: any):
        """Cache response with timestamp."""
        # Limit cache size to prevent memory issues
        if len(self._cache) > 1000:
            # Remove oldest 20% of entries
            sorted_items = sorted(self._cache.items(), key=lambda x: x[1][0])
            for key, _ in sorted_items[:200]:
                del self._cache[key]
        
        self._cache[cache_key] = (time.time(), response)
    
    def can_make_request(self, url: str, method: str = 'GET') -> Tuple[bool, Optional[str], Optional[any]]:
        """
        Check if request can be made and return cached response if available.
        
        Returns:
            (can_proceed, reason_if_blocked, cached_response)
        """
        with self._lock:
            current_time = time.time()
            endpoint_category = self._get_endpoint_category(url)
            
            # Check cache first for GET requests
            cached_response = None
            if method.upper() == 'GET':
                cache_key = self._get_cache_key(url, method)
                cached_response = self._get_cached_response(cache_key)
                if cached_response is not None:
                    return True, None, cached_response
            
            # Clean old requests
            self._clean_old_requests(self._global_requests, 60)
            self._clean_old_requests(self._burst_requests, 10)
            self._clean_old_requests(self._endpoint_requests[endpoint_category], 60)
            
            # Check for exponential backoff on errors
            if endpoint_category in self._last_error_time:
                error_count = self._error_counts[endpoint_category]
                if error_count > 0:
                    backoff_time = min(2 ** error_count, 300)  # Max 5 minutes
                    if current_time - self._last_error_time[endpoint_category] < backoff_time:
                        self._blocked_requests += 1
                        return False, f"Backing off due to errors (wait {int(backoff_time)}s)", None
            
            # Check burst limit
            if len(self._burst_requests) >= self._burst_limit:
                self._blocked_requests += 1
                return False, "Burst limit exceeded (max 10 requests per 10 seconds)", None
            
            # Check global rate limit
            if len(self._global_requests) >= self._global_limit:
                self._blocked_requests += 1
                return False, f"Global rate limit exceeded (max {self._global_limit} requests per minute)", None
            
            # Check endpoint-specific rate limit
            endpoint_limit = self._endpoint_limits.get(endpoint_category, self._endpoint_limits['default'])
            if len(self._endpoint_requests[endpoint_category]) >= endpoint_limit:
                self._blocked_requests += 1
                return False, f"Endpoint rate limit exceeded (max {endpoint_limit} requests per minute for {endpoint_category})", None
            
            return True, None, cached_response
    
    def record_request(self, url: str, method: str = 'GET'):
        """Record a successful request."""
        with self._lock:
            current_time = time.time()
            endpoint_category = self._get_endpoint_category(url)
            
            self._global_requests.append(current_time)
            self._burst_requests.append(current_time)
            self._endpoint_requests[endpoint_category].append(current_time)
            self._total_requests += 1
            
            # Reset error count on successful request
            if endpoint_category in self._error_counts:
                self._error_counts[endpoint_category] = 0
    
    def record_error(self, url: str, status_code: Optional[int] = None):
        """Record a failed request for backoff calculation."""
        with self._lock:
            endpoint_category = self._get_endpoint_category(url)
            self._error_counts[endpoint_category] += 1
            self._last_error_time[endpoint_category] = time.time()
    
    def cache_response(self, url: str, method: str, response: any):
        """Cache a successful response."""
        if method.upper() == 'GET':
            cache_key = self._get_cache_key(url, method)
            self._cache_response(cache_key, response)
    
    def get_stats(self) -> Dict[str, any]:
        """Get usage statistics."""
        with self._lock:
            current_time = time.time()
            
            # Clean old requests for accurate counts
            self._clean_old_requests(self._global_requests, 60)
            
            return {
                'total_requests': self._total_requests,
                'blocked_requests': self._blocked_requests,
                'current_rpm': len(self._global_requests),
                'cache_size': len(self._cache),
                'error_counts': dict(self._error_counts),
                'efficiency': (1 - self._blocked_requests / max(1, self._total_requests + self._blocked_requests)) * 100
            }
    
    def clear_cache(self):
        """Clear the response cache."""
        with self._lock:
            self._cache.clear()


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter