import json
import os
import threading
import time
from typing import Dict, Any, List

from .binance_service import BinanceMicroservice
from .okx_service import OKXMicroservice
from .bitget_service import BitgetMicroservice
from Notification.discord_service import DiscordMicroservice
from .base import BaseMicroservice

CONFIG_PATH_CANDIDATES = [
    os.path.join("_settings", "microservices_config.json"),
    os.path.join("config", "microservices_config.json"),
]

DEFAULT_CONFIG = {
    "shared_log_path": "logs/shared.log",
    "services": {
        "binance": {
            # giá trị này sẽ bị override nếu hedge.json có strategy.binance
            "enabled": True,
            "coins": [],
            "futures_balance_lower": 50.0,
            "futures_balance_upper": 100.0
        },
        "okx": {"enabled": False, "coins": []},
        "bitget": {"enabled": True, "coins": []},
        "discord": {"enabled": True, "webhook": ""}
    }
}

class MicroserviceManager:
    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or self._resolve_config_path()
        self.config: Dict[str, Any] = self._load_or_create_config()
        self.shared_log_path = self.config.get("shared_log_path", "logs/shared.log")
        os.makedirs(os.path.dirname(self.shared_log_path), exist_ok=True)
        self.services: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._apply_strategy_overrides()
        self._init_services()
        self.asset_history_file = "logs/asset_history.jsonl"

    # ---------- Hedge strategy loader ----------
    def _load_hedge_strategy(self) -> Dict[str, Any]:
        candidates = [
            os.path.join("_settings", "hedge.json"),
            os.path.join("code", "_settings", "hedge.json"),
        ]
        for p in candidates:
            if os.path.exists(p):
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return data.get('strategy', {})
                except Exception:
                    continue
        return {}

    def _apply_strategy_overrides(self):
        strategy = self._load_hedge_strategy()
        if not strategy:
            return
        sv_cfg = self.config.get('services', {})
        # Binance
        strat_binance = strategy.get('binance')
        if strat_binance:
            binance_cfg = sv_cfg.setdefault('binance', {})
            coins = strat_binance.get('coins')
            if coins:
                binance_cfg['coins'] = coins
            if 'futures_balance_lower' in strat_binance:
                binance_cfg['futures_balance_lower'] = strat_binance['futures_balance_lower']
            if 'futures_balance_upper' in strat_binance:
                binance_cfg['futures_balance_upper'] = strat_binance['futures_balance_upper']
            binance_cfg['enabled'] = strat_binance.get('enabled', True)
        # OKX
        strat_okx = strategy.get('okx')
        if strat_okx:
            okx_cfg = sv_cfg.setdefault('okx', {})
            coins = strat_okx.get('coins')
            if coins:
                okx_cfg['coins'] = coins
            if 'futures_balance_lower' in strat_okx:
                okx_cfg['futures_balance_lower'] = strat_okx['futures_balance_lower']
            if 'futures_balance_upper' in strat_okx:
                okx_cfg['futures_balance_upper'] = strat_okx['futures_balance_upper']
            okx_cfg['enabled'] = strat_okx.get('enabled', True)
        # Bitget
        strat_bitget = strategy.get('bitget')
        if strat_bitget:
            bitget_cfg = sv_cfg.setdefault('bitget', {})
            coins = strat_bitget.get('coins')
            if coins:
                bitget_cfg['coins'] = coins
            if 'futures_balance_lower' in strat_bitget:
                bitget_cfg['futures_balance_lower'] = strat_bitget['futures_balance_lower']
            if 'futures_balance_upper' in strat_bitget:
                bitget_cfg['futures_balance_upper'] = strat_bitget['futures_balance_upper']
            bitget_cfg['enabled'] = strat_bitget.get('enabled', True)

    def _resolve_config_path(self) -> str:
        for p in CONFIG_PATH_CANDIDATES:
            if os.path.exists(p):
                return p
        return CONFIG_PATH_CANDIDATES[0]

    def _load_or_create_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            return DEFAULT_CONFIG
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _init_services(self):
        sv_cfg: Dict[str, Any] = self.config.get("services", {})
        shared = {"shared_log_path": self.shared_log_path}
        # Binance
        if "binance" in sv_cfg:
            cfg = {**shared, **sv_cfg["binance"]}
            self.services["binance"] = BinanceMicroservice("binance", cfg)
        # OKX
        if "okx" in sv_cfg:
            cfg = {**shared, **sv_cfg["okx"]}
            self.services["okx"] = OKXMicroservice("okx", cfg)
        # Bitget
        if "bitget" in sv_cfg:
            cfg = {**shared, **sv_cfg["bitget"]}
            self.services["bitget"] = BitgetMicroservice("bitget", cfg)
        # Discord
        if "discord" in sv_cfg:
            cfg = {**shared, **sv_cfg["discord"]}
            self.services["discord"] = DiscordMicroservice(shared_log_path=self.shared_log_path, webhook_url=cfg.get("webhook"))

    # -------- Auto start --------
    def start_enabled_services(self):
        sv_cfg: Dict[str, Any] = self.config.get("services", {})
        for name, cfg in sv_cfg.items():
            if cfg.get("enabled"):
                self.start_service(name)

    # -------- Control --------
    def start_service(self, name: str) -> bool:
        with self._lock:
            svc = self.services.get(name)
            if not svc:
                return False
            if isinstance(svc, DiscordMicroservice):
                return svc.start()
            if isinstance(svc, BaseMicroservice):
                return svc.start()
            return False

    def stop_service(self, name: str) -> bool:
        with self._lock:
            svc = self.services.get(name)
            if not svc:
                return False
            if isinstance(svc, DiscordMicroservice):
                return svc.stop()
            if isinstance(svc, BaseMicroservice):
                return svc.stop()
            return False

    def start_all(self):
        for n in list(self.services.keys()):
            self.start_service(n)

    def stop_all(self):
        for n in list(self.services.keys()):
            self.stop_service(n)

    # -------- Info --------
    def list_services(self) -> List[Dict[str, Any]]:
        out = []
        for name, svc in self.services.items():
            if isinstance(svc, DiscordMicroservice):
                out.append(svc.info())
            elif isinstance(svc, BaseMicroservice):
                out.append(svc.info())
        return out

    # -------- Asset Snapshot --------
    def asset_snapshot(self) -> Dict[str, Any]:
        total_usdt = 0.0
        positions: Dict[str, Dict[str, float]] = {}
        details: Dict[str, Any] = {}
        ts = int(time.time())

        for name, svc in self.services.items():
            if isinstance(svc, BaseMicroservice) and svc.state.running:
                assets = svc.fetch_assets()
                bal = assets.get("balances", {})
                usdt_val = float(bal.get("USDT", 0)) + float(bal.get("EARN_USDT", 0))
                total_usdt += usdt_val
                details[name] = {"balances": bal, "positions": assets.get("positions", {})}
                for sym, pos in assets.get("positions", {}).items():
                    positions.setdefault(sym, {"short_total": 0.0})
                    positions[sym]["short_total"] += float(pos.get("short_size", 0))

        snapshot = {
            "timestamp": ts,
            "total_usdt": total_usdt,
            "positions": positions,
            "details": details,
        }
        try:
            os.makedirs(os.path.dirname(self.asset_history_file), exist_ok=True)
            with open(self.asset_history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(snapshot) + "\n")
        except Exception:
            pass
        # ghi tóm tắt vào shared log cho Discord
        try:
            with open(self.shared_log_path, 'a', encoding='utf-8') as f:
                f.write(f"ASSET_SNAPSHOT ts={ts} total_usdt={total_usdt}\n")
        except Exception:
            pass
        return snapshot

    def asset_current(self) -> Dict[str, Any]:
        """Lấy nhanh trạng thái tài sản mà không ghi lịch sử hay log."""
        total_usdt = 0.0
        positions: Dict[str, Dict[str, float]] = {}
        details: Dict[str, Any] = {}
        ts = int(time.time())
        for name, svc in self.services.items():
            if isinstance(svc, BaseMicroservice) and svc.state.running:
                assets = svc.fetch_assets()
                bal = assets.get("balances", {})
                usdt_val = float(bal.get("USDT", 0)) + float(bal.get("EARN_USDT", 0))
                total_usdt += usdt_val
                details[name] = {"balances": bal, "positions": assets.get("positions", {})}
                for sym, pos in assets.get("positions", {}).items():
                    positions.setdefault(sym, {"short_total": 0.0})
                    positions[sym]["short_total"] += float(pos.get("short_size", 0))
        return {
            "timestamp": ts,
            "total_usdt": total_usdt,
            "positions": positions,
            "details": details,
        }

    def load_history(self, limit: int | None = None) -> List[Dict[str, Any]]:
        if not os.path.exists(self.asset_history_file):
            return []
        lines = []
        with open(self.asset_history_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    lines.append(json.loads(line))
                except Exception:
                    continue
        if limit:
            return lines[-limit:]
        return lines
