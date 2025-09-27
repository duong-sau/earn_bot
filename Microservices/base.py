import threading
import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger("microservice")
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')

class ServiceState:
    def __init__(self):
        self.running = False
        self.last_cycle_time = None
        self.extra: Dict[str, Any] = {}

class BaseMicroservice:
    """Base class cho các microservice exchange.
    Nhiệm vụ chung:
    - Vòng lặp mỗi 10s (có thể điều chỉnh) gọi: fetch_assets -> risk_check -> rebalance -> maintain_short_position.
    - Placeholder websocket lắng nghe giá (có thể triển khai sau bằng thread riêng / ccxt.pro).
    - Ghi log sự kiện chung vào shared log (để Discord service đọc).
    """
    LOOP_INTERVAL = 10

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.state = ServiceState()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.positions: Dict[str, Dict[str, Any]] = {}  # symbol -> info
        self.coins: List[Dict[str, Any]] = config.get("coins", [])  # each: {symbol, short_size}
        self.shared_log_path = config.get("shared_log_path", "logs/shared.log")
        self.lock = threading.Lock()

    # ---- Lifecycle ----
    def start(self):
        if self.state.running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name=f"{self.name}-loop", daemon=True)
        self.state.running = True
        self._thread.start()
        self._log_event(f"{self.name} started")
        return True

    def stop(self):
        if not self.state.running:
            return False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self.state.running = False
        self._log_event(f"{self.name} stopped")
        return True

    # ---- Core Loop ----
    def _run_loop(self):
        while not self._stop_event.is_set():
            cycle_start = time.time()
            try:
                self._cycle()
            except Exception as e:
                logger.exception(f"[{self.name}] Cycle error: {e}")
                self._log_event(f"[{self.name}] cycle_error: {e}")
            self.state.last_cycle_time = time.time()
            elapsed = self.state.last_cycle_time - cycle_start
            sleep_time = max(0, self.LOOP_INTERVAL - elapsed)
            self._stop_event.wait(timeout=sleep_time)

    def _cycle(self):
        assets = self.fetch_assets()
        self.risk_check(assets)
        self.rebalance_if_needed(assets)
        self.maintain_short_positions(assets)

    # ---- Extension Points ----
    def fetch_assets(self) -> Dict[str, Any]:
        return {"balances": {}, "positions": self.positions}

    def risk_check(self, assets: Dict[str, Any]):
        # Placeholder: implement kiểm tra margin, health factor...
        return

    def rebalance_if_needed(self, assets: Dict[str, Any]):
        # Placeholder: adjust margin / chuyển vốn earn <-> future
        return

    def maintain_short_positions(self, assets: Dict[str, Any]):
        # Placeholder: kiểm tra mỗi coin trong self.coins có đủ short size chưa
        for c in self.coins:
            sym = c.get("symbol")
            target = float(c.get("short_size", 0))
            cur = self.positions.get(sym, {}).get("short_size", 0.0)
            if abs(cur - target) > 1e-8:
                # giả lập điều chỉnh
                self.positions[sym] = {"short_size": target}
                self._log_event(f"{self.name} adjust short {sym} -> {target}")

    # ---- Logging ----
    def _log_event(self, msg: str):
        try:
            with open(self.shared_log_path, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except Exception:
            logger.warning(f"Cannot write shared log at {self.shared_log_path}")
        logger.info(msg)

    # ---- Public Info ----
    def info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "running": self.state.running,
            "last_cycle": self.state.last_cycle_time,
            "coins": self.coins,
            "positions": self.positions,
        }

