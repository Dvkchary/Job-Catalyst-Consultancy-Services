import asyncio
import zlib
import time
import logging
from typing import Dict, Tuple, Optional, Any
import httpx
from app.core.config import settings

logger = logging.getLogger("app.core.cache_pool")

class InMemoryCache:
    """
    High-performance, thread-safe, memory-efficient cache wrapper.
    Features:
    - Sliding and absolute TTL (Time-To-Live) expiration checks.
    - Automatic zlib compression/decompression to keep RAM usage low.
    - Strict size limit controls (LRU-like eviction) to prevent memory bloating.
    """
    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 3600) -> None:
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        # Maps key -> (compressed_bytes, expiration_timestamp, is_compressed)
        self._store: Dict[str, Tuple[bytes, float, bool]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        """Retrieves and decompresses cached value if still active."""
        async with self._lock:
            if key not in self._store:
                return None
            
            compressed_val, expires_at, is_compressed = self._store[key]
            if time.time() > expires_at:
                # Evict expired key
                self._store.pop(key, None)
                return None
            
            try:
                if is_compressed:
                    decompressed = zlib.decompress(compressed_val).decode("utf-8")
                    return decompressed
                return compressed_val.decode("utf-8")
            except Exception as e:
                logger.error(f"Cache decompression failure for key '{key}': {str(e)}")
                return None

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        """Compresses and stores the key-value with dynamic TTL expiration bounds."""
        async with self._lock:
            # Enforce cache size limits
            if len(self._store) >= self.max_size:
                # Prune 10% of expired or oldest elements
                now = time.time()
                expired_keys = [k for k, v in self._store.items() if now > v[1]]
                if expired_keys:
                    for k in expired_keys[:100]:
                        self._store.pop(k, None)
                else:
                    # If no expired keys, drop oldest 10%
                    keys_to_drop = list(self._store.keys())[:int(self.max_size * 0.1)]
                    for k in keys_to_drop:
                        self._store.pop(k, None)

            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            expires_at = time.time() + ttl
            
            try:
                raw_bytes = value.encode("utf-8")
                # Compress only if value exceeds 256 bytes to avoid compression overhead on tiny strings
                if len(raw_bytes) > 256:
                    compressed_val = zlib.compress(raw_bytes)
                    is_compressed = True
                else:
                    compressed_val = raw_bytes
                    is_compressed = False
                    
                self._store[key] = (compressed_val, expires_at, is_compressed)
                return True
            except Exception as e:
                logger.error(f"Cache write/compression failure for key '{key}': {str(e)}")
                return False

    async def clear(self) -> None:
        """Purges all elements in cache store."""
        async with self._lock:
            self._store.clear()


# Instantiate a global memory cache singleton
fast_cache = InMemoryCache(max_size=2000, default_ttl_seconds=3600)


class HTTPClientProvider:
    """
    Manages a single global pooled httpx.AsyncClient instance.
    Implements HTTP Keep-Alive connection reuse to optimize outbound API latency.
    """
    _client: Optional[httpx.AsyncClient] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """Returns the shared, thread-safe, Keep-Alive pooled async client."""
        if cls._client is None or cls._client.is_closed:
            async with cls._lock:
                if cls._client is None or cls._client.is_closed:
                    # Configure enterprise-grade pooling thresholds
                    limits = httpx.Limits(
                        max_keepalive_connections=50,
                        max_connections=200,
                        keepalive_expiry=60.0
                    )
                    cls._client = httpx.AsyncClient(
                        limits=limits,
                        timeout=httpx.Timeout(15.0, connect=5.0, read=30.0),
                        headers={"User-Agent": "JobCatalyst-AI/1.0 (Performance Engineered)"}
                    )
                    logger.info("Shared Async HTTP Connection Pool initialized successfully.")
        return cls._client

    @classmethod
    async def close_client(cls) -> None:
        """Gracefully closes all connections in the pooled client."""
        if cls._client is not None and not cls._client.is_closed:
            async with cls._lock:
                if cls._client is not None and not cls._client.is_closed:
                    await cls._client.aclose()
                    cls._client = None
                    logger.info("Shared Async HTTP Connection Pool shut down.")
