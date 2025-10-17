import logging
import os
import time
import pickle
from collections import OrderedDict
from threading import RLock
import hashlib

class LoggerCacheSingleton:
    LOG_FILE = "logs/app.log"
    MAX_LOG_SIZE_MB = 10
    MAX_LOG_AGE_HOURS = 5
    CACHE_MAX_ITEMS = 100
    CACHE_PERSISTENT_DIR = "cache/queries"

    class _Helper:
        instance = None

    def __new__(cls):
        if not LoggerCacheSingleton._Helper.instance:
            LoggerCacheSingleton._Helper.instance = super().__new__(cls)
            LoggerCacheSingleton._Helper.instance._initialize()
        return LoggerCacheSingleton._Helper.instance

    def _initialize(self):
        # -------- Logger setup --------
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
        self.logger = logging.getLogger("HybridChatLogger")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fh = logging.FileHandler(self.LOG_FILE)
            formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        self._cleanup_log_file()

        # -------- Cache setup --------
        self._cache = OrderedDict()
        self._cache_lock = RLock()
        self.cache_hits = 0
        self.cache_misses = 0

        # Persistent cache folder
        os.makedirs(self.CACHE_PERSISTENT_DIR, exist_ok=True)

    # -------- Logger Methods --------
    def info(self, msg):
        self._cleanup_log_file()
        self.logger.info(msg)

    def error(self, msg):
        self._cleanup_log_file()
        self.logger.error(msg)

    def debug(self, msg):
        self._cleanup_log_file()
        self.logger.debug(msg)

    def _cleanup_log_file(self):
        try:
            if os.path.exists(self.LOG_FILE):
                stat = os.stat(self.LOG_FILE)
                file_age_hours = (time.time() - stat.st_mtime) / 3600
                file_size_mb = stat.st_size / (1024 * 1024)
                if file_age_hours > self.MAX_LOG_AGE_HOURS or file_size_mb > self.MAX_LOG_SIZE_MB:
                    os.remove(self.LOG_FILE)
        except Exception:
            pass

    # -------- In-memory Cache Methods --------
    def put_cache(self, key, value):
        with self._cache_lock:
            if key in self._cache:
                self._cache.pop(key)
            elif len(self._cache) >= self.CACHE_MAX_ITEMS:
                self._cache.popitem(last=False)  # LRU eviction
            self._cache[key] = value

    def get_cache(self, key):
        with self._cache_lock:
            if key in self._cache:
                value = self._cache.pop(key)
                self._cache[key] = value
                self.cache_hits += 1
                return value
            else:
                self.cache_misses += 1
                return None

    def cache_stats(self):
        with self._cache_lock:
            return {"hits": self.cache_hits, "misses": self.cache_misses, "size": len(self._cache)}

    def clear_cache(self):
        with self._cache_lock:
            self._cache.clear()
            self.cache_hits = 0
            self.cache_misses = 0

    # -------- Persistent Query Cache --------
    def _get_query_file(self, query):
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return os.path.join(self.CACHE_PERSISTENT_DIR, f"{query_hash}.pkl")

    def put_persistent_query(self, query, result):
        file_path = self._get_query_file(query)
        try:
            with open(file_path, "wb") as f:
                pickle.dump(result, f)
            self.put_cache(query, result)  # also store in memory
        except Exception as e:
            self.error(f"Failed to write persistent cache: {e}")

    def get_persistent_query(self, query):
        # First check in-memory cache
        result = self.get_cache(query)
        if result is not None:
            self.info(f"Cache hit for query (memory): {query}")
            return result

        # Then check disk
        file_path = self._get_query_file(query)
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    result = pickle.load(f)
                self.put_cache(query, result)  # store in memory
                self.info(f"Cache hit for query (disk): {query}")
                return result
            except Exception as e:
                self.error(f"Failed to read persistent cache: {e}")

        # Cache miss
        self.cache_misses += 1
        self.info(f"Cache miss for query: {query}")
        return None
