"""Caching utilities for the Ticketing API using Redis.

This module provides a Redis-based caching layer for improving
API performance by caching frequently accessed resources.
"""
import json
import redis
from flask import current_app

class Cache:
    """Redis cache wrapper for the Ticketing API.
    
    Provides methods for getting, setting, and deleting cached values.
    Gracefully handles cases when Redis is unavailable.
    """
    
    def __init__(self, app=None):
        """Initialize the Cache.

        Args:
            app: Optional Flask app to initialize with
        """
        self.redis_client = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the cache with app config.

        Args:
            app: Flask application instance
        """
        try:
            redis_host = app.config.get("REDIS_HOST", "localhost")
            redis_port = app.config.get("REDIS_PORT", 6379)
            redis_db = app.config.get("REDIS_DB", 0)
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            self.redis_client.ping()
        except Exception:
            self.redis_client = None
    
    def get(self, key):
        """Get a value from cache.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value as dictionary, or None if not found
        """
        if self.redis_client is None:
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            pass
        return None
    
    def set(self, key, value, ttl=None):
        """Set a value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        if self.redis_client is None:
            return False
        try:
            serialized = json.dumps(value)
            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)
            return True
        except Exception:
            return False
    
    def delete(self, key):
        """Delete a key from cache.

        Args:
            key: Cache key to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if self.redis_client is None:
            return False
        try:
            self.redis_client.delete(key)
            return True
        except Exception:
            return False
    
    def invalidate_pattern(self, pattern):
        """Invalidate all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., 'user:*')

        Returns:
            bool: True if successful, False otherwise
        """
        if self.redis_client is None:
            return False
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception:
            return False

cache = Cache()
"""Global cache instance."""

def get_cache():
    """Get the cache instance.

    Returns:
        Cache: The global cache instance
    """
    return cache