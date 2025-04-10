import threading
import time
from datetime import datetime
import os

class Logger:
    def __init__(self, log_file="app.log", username="SYSTEM", max_log_size=5*1024*1024):  
        self.log_file = log_file
        self.username = username
        self.max_log_size = max_log_size
        self.log_queue = []
        self.lock = threading.Lock()
        self.running = True

        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w'): pass

        self.thread = threading.Thread(target=self._log_worker, daemon=True)
        self.thread.start()

    def _check_log_size(self):
        if os.path.getsize(self.log_file) >= self.max_log_size:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = f"{os.path.splitext(self.log_file)[0]}_{timestamp}.log"
            os.rename(self.log_file, archive_file)
            with open(self.log_file, 'w'): pass

    def _log_worker(self):
        while self.running or self.log_queue:
            if self.log_queue:
                with self.lock:
                    logs_to_write = self.log_queue[:]
                    self.log_queue.clear()

                try:
                    self._check_log_size()
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        for log in logs_to_write:
                            f.write(f"{log}\n")
                except Exception as e:
                    print(f"Ошибка записи лога: {e}")

            time.sleep(0.5)

    def _format_log(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] [{level}] [{self.username}] {message}"

    def log_info(self, action):
        with self.lock:
            formatted = self._format_log("INFO", action)
            self.log_queue.append(formatted)

    def log_error(self, location, error):
        with self.lock:
            formatted = self._format_log("ERROR", f"{location}: {error}")
            self.log_queue.append(formatted)

    def stop(self):
        self.running = False
        self.thread.join()