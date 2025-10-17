import logging
import os
import time

class LoggerSingleton:
    LOG_FILE = "logs/app.log"
    MAX_SIZE_MB = 10
    MAX_AGE_HOURS = 5

    class _Helper:
        instance = None

    def __new__(cls):
        if not LoggerSingleton._Helper.instance:
            LoggerSingleton._Helper.instance = super(LoggerSingleton, cls).__new__(cls)
            LoggerSingleton._Helper.instance._initialize()
        return LoggerSingleton._Helper.instance

    def _initialize(self):
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
        self.logger = logging.getLogger("HybridChatLogger")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fh = logging.FileHandler(self.LOG_FILE)
            formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        self._cleanup_log_file()

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
        """Delete log file if older than MAX_AGE_HOURS or larger than MAX_SIZE_MB."""
        try:
            if os.path.exists(self.LOG_FILE):
                stat = os.stat(self.LOG_FILE)
                file_age_hours = (time.time() - stat.st_mtime) / 3600
                file_size_mb = stat.st_size / (1024 * 1024)
                if file_age_hours > self.MAX_AGE_HOURS or file_size_mb > self.MAX_SIZE_MB:
                    os.remove(self.LOG_FILE)
        except Exception:
            pass
