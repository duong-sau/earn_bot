import threading
import time
import logging
import os
from typing import Dict, Any, Optional
import requests

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s discord: %(message)s')
logger = logging.getLogger("discord")

class DiscordMicroservice:
    """Đọc shared log và gửi dòng mới lên Discord webhook.
    Cơ chế:
    - Giữ offset (số byte) đã đọc.
    - Mỗi POLL_INTERVAL giây kiểm tra file grow -> đọc phần mới -> gửi từng dòng.
    - Có rate limit đơn giản (max lines / chu kỳ) để tránh spam.
    """
    POLL_INTERVAL = 5
    MAX_LINES_PER_CYCLE = 10

    def __init__(self, shared_log_path: str, webhook_url: Optional[str] = None):
        self.shared_log_path = shared_log_path
        self.webhook_url = webhook_url or os.environ.get("DISCORD_WEBHOOK")
        self._offset = 0
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self):
        if self._running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="discord-loop", daemon=True)
        self._running = True
        self._thread.start()
        logger.info("DiscordMicroservice started")
        return True

    def stop(self):
        if not self._running:
            return False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._running = False
        logger.info("DiscordMicroservice stopped")
        return True

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                self._process_new_lines()
            except Exception as e:
                logger.exception(f"discord loop error: {e}")
            self._stop_event.wait(self.POLL_INTERVAL)

    def _process_new_lines(self):
        if not os.path.exists(self.shared_log_path):
            return
        size = os.path.getsize(self.shared_log_path)
        if size < self._offset:
            # file rotated
            self._offset = 0
        if size == self._offset:
            return
        # đọc phần mới
        with open(self.shared_log_path, 'r', encoding='utf-8') as f:
            f.seek(self._offset)
            data = f.read()
            self._offset = f.tell()
        lines = [l.strip() for l in data.splitlines() if l.strip()]
        lines = lines[-self.MAX_LINES_PER_CYCLE:]
        for line in lines:
            self._send_discord(line)

    def _send_discord(self, content: str):
        if not self.webhook_url:
            logger.debug(f"(no webhook) {content}")
            return
        try:
            resp = requests.post(self.webhook_url, json={"content": content}, timeout=5)
            if resp.status_code >= 300:
                logger.warning(f"discord send fail {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"discord exception: {e}")

    def info(self) -> Dict[str, Any]:
        return {
            "name": "discord",
            "running": self._running,
            "webhook": bool(self.webhook_url),
            "offset": self._offset,
        }

