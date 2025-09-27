from .base import BaseMicroservice
from typing import Dict, Any
import time

class BitgetMicroservice(BaseMicroservice):
    """Quản lý position short + stake ở Bitget (khung).
    Tương lai: thêm launchpool / staking API thực tế.
    """

    def fetch_assets(self) -> Dict[str, Any]:
        # TODO: Gọi API Bitget future + stake/earn
        return {
            "balances": {
                "USDT": 9000,
                "STAKED_COIN": 500,
            },
            "positions": self.positions,
        }

    def risk_check(self, assets: Dict[str, Any]):
        # TODO: margin requirements
        return

    def rebalance_if_needed(self, assets: Dict[str, Any]):
        # TODO: tự động unstake khi thiếu margin
        return

    def maintain_short_positions(self, assets: Dict[str, Any]):
        super().maintain_short_positions(assets)
        # Giả lập stake reward claim
        if int(time.time()) % 2700 == 0:  # 45 phút
            self._log_event(f"{self.name} simulate stake reward Bitget")


import os
import json
import asyncio
import time
import logging
import threading
import contextlib
from typing import Dict, Any, Optional, List

import ccxt.pro as ccxtpro
import ccxt.async_support as ccxt_async

from .base import BaseMicroservice

try:
    from Define import root_path
except Exception:
    root_path = os.getcwd()

logger = logging.getLogger("bitget_ms")

class BitgetMicroservice(BaseMicroservice):
    """BitgetMicroservice (async)
    Giữ short cho danh sách coin cấu hình (ví dụ BGB, BTC) trên Bitget USDT-M perpetual.
    - Watch positions qua websocket (watch_positions)
    - Auto mở short market nếu short < target
    - Collateral watcher chỉ log free USDT (placeholder)

    Coin config ví dụ strategy.hedge.json:
      {
        "symbol": "BGB/USDT",
        "perp_symbol": "BGB/USDT:USDT",
        "short_size": 5000,
        "step": 10
      }
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.lower = float(config.get('futures_balance_lower', 50))
        self.upper = float(config.get('futures_balance_upper', 100))
        self.api_key, self.api_secret, self.password = self._load_keys(config)
        self._short_cache: Dict[str, float] = {}

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_async: Optional[asyncio.Event] = None
        self._position_tasks: List[asyncio.Task] = []
        self._collateral_task: Optional[asyncio.Task] = None
        self.bitget_rest = None
        self.bitget_fut = None

    # -------- lifecycle override --------
    def start(self):
        if self.state.running:
            return False
        self._stop_event.clear()
        self._loop = asyncio.new_event_loop()
        self._stop_async = asyncio.Event()
        self._thread = threading.Thread(target=self._run_loop, name=f"{self.name}-loop", daemon=True)
        self._thread.start()
        self.state.running = True
        self._log_event(f"{self.name} started async")
        return True

    def stop(self):
        if not self.state.running:
            return False
        if self._loop and self._stop_async and not self._loop.is_closed():
            def _cancel():
                self._stop_async.set()
                for t in list(self._position_tasks):
                    t.cancel()
                if self._collateral_task:
                    self._collateral_task.cancel()
            self._loop.call_soon_threadsafe(_cancel)
        if self._thread:
            self._thread.join(timeout=10)
        self.state.running = False
        self._log_event(f"{self.name} stopped")
        return True

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._async_main())
        finally:
            with contextlib.suppress(Exception):
                self._loop.run_until_complete(self._cleanup())
            self._loop.close()

    # -------- setup / cleanup --------
    def _load_keys(self, config: Dict[str, Any]):
        k = config.get('api_key'); s = config.get('api_secret'); p = config.get('password')
        if k and s and p:
            return k, s, p
        candidates = [
            os.path.join(root_path, '_settings', 'hedge.json'),
            os.path.join(root_path, 'code', '_settings', 'hedge.json'),
            os.path.join('_settings', 'hedge.json'),
        ]
        for path in candidates:
            if os.path.exists(path):
                with contextlib.suppress(Exception):
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    bg = data.get('bitget', {})
                    k = bg.get('api_key'); s = bg.get('api_secret'); p = bg.get('password')
                    if k and s and p:
                        return k, s, p
        self._log_event('[WARN] Không tìm thấy API key Bitget')
        return None, None, None

    async def _create_clients(self):
        if not (self.api_key and self.api_secret and self.password):
            return
        self.bitget_rest = ccxt_async.bitget({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'password': self.password,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        self.bitget_fut = ccxtpro.bitget({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'password': self.password,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        await self.bitget_fut.load_markets()
        self._log_event('Bitget clients ready')

    async def _cleanup(self):
        with contextlib.suppress(Exception):
            if self.bitget_fut:
                await self.bitget_fut.close()
        with contextlib.suppress(Exception):
            if self.bitget_rest:
                await self.bitget_rest.close()

    # -------- main orchestrator --------
    async def _async_main(self):
        if not (self.api_key and self.api_secret and self.password):
            self._log_event('[ERROR] No Bitget API key => exit')
            return
        await self._create_clients()
        self._collateral_task = asyncio.create_task(self._collateral_watcher())
        for coin in self.coins:
            perp = coin.get('perp_symbol') or self._infer_perp_symbol(coin.get('symbol'))
            t = asyncio.create_task(self._position_watcher(perp, coin))
            self._position_tasks.append(t)
        await self._stop_async.wait()
        for t in self._position_tasks:
            t.cancel()
        if self._collateral_task:
            self._collateral_task.cancel()
        await asyncio.gather(*self._position_tasks, return_exceptions=True)
        if self._collateral_task:
            with contextlib.suppress(Exception):
                await self._collateral_task

    # -------- helpers --------
    def _infer_perp_symbol(self, symbol: str) -> str:
        if not symbol:
            return ''
        if ':USDT' in symbol:
            return symbol
        if symbol.endswith('/USDT'):
            return symbol + ':USDT'
        return symbol

    async def _fetch_available_usdt(self) -> float:
        with contextlib.suppress(Exception):
            bal = await self.bitget_fut.fetch_balance()
            return float(bal.get('free', {}).get('USDT', 0) or 0)
        return 0.0

    async def _open_short(self, perp: str, target: float, step: int):
        cur = self._short_cache.get(perp, 0.0)
        need = target - cur
        if need <= 0:
            return
        if step > 0:
            qty = int(need / step) * step
            if qty <= 0:
                qty = step
        else:
            qty = need
        try:
            await self.bitget_fut.create_order(perp, 'market', 'sell', qty, params={'reduceOnly': False})
            self._log_event(f"Open short {perp} {qty} (cur={cur} target={target})")
        except Exception as e:
            self._log_event(f"[ERROR] open short {perp}: {e}")

    # -------- watchers --------
    async def _collateral_watcher(self):
        POLL = 40
        while not self._stop_async.is_set():
            try:
                usdt = await self._fetch_available_usdt()
                self._log_event(f"[bitget] avail USDT={usdt:.2f}")
                if usdt < self.lower * 0.5:
                    self._log_event('[bitget] WARN low collateral (placeholder)')
            except Exception as e:
                self._log_event(f"[WARN] collateral watcher: {e}")
            await asyncio.wait([self._stop_async.wait()], timeout=POLL)

    async def _position_watcher(self, perp: str, coin_cfg: Dict[str, Any]):
        target = float(coin_cfg.get('short_size', 0))
        step = int(coin_cfg.get('step', 1) or 1)
        while not self._stop_async.is_set():
            try:
                positions = await self.bitget_fut.watch_positions([perp])
                short_qty = 0.0
                for p in positions:
                    if p.get('symbol') == perp:
                        side = p.get('side')
                        contracts = float(p.get('contracts') or 0)
                        if side == 'short' or contracts < 0:
                            short_qty += abs(contracts)
                prev = self._short_cache.get(perp)
                self._short_cache[perp] = short_qty
                self.positions[perp] = {"short_size": short_qty}
                if prev is None or abs(short_qty - prev) > 1e-6:
                    self._log_event(f"[bitget] {perp} short={short_qty} target={target}")
                if short_qty < target - step:
                    await self._open_short(perp, target, step)
            except Exception as e:
                self._log_event(f"[ERROR] pos watcher {perp}: {e}")
                await asyncio.sleep(5)

    # -------- overrides --------
    def fetch_assets(self) -> Dict[str, Any]:
        return {"balances": {}, "positions": self.positions}

    def get_position_data(self) -> Dict[str, Any]:
        """Lấy thông tin position và stake cho API"""
        try:
            # Mock data cho demo - sau này anh có thể thay bằng API thực
            return {
                "total_balance": 2800.0,
                "futures_pnl": 95.25,
                "staking_total": 1200.0,
                "launchpool_total": 350.0,
                "positions": [
                    {
                        "symbol": "BGB/USDT:USDT",
                        "side": "SHORT",
                        "size": 500.0,
                        "entry_price": 1.85,
                        "mark_price": 1.82,
                        "pnl": 15.0,
                        "roe": 1.62,
                        "funding_rate": -0.0012  # -0.12% funding rate (good for short)
                    },
                    {
                        "symbol": "ETH/USDT:USDT",
                        "side": "SHORT",
                        "size": 1.2,
                        "entry_price": 2590.0,
                        "mark_price": 2570.0,
                        "pnl": 24.0,
                        "roe": 0.93,
                        "funding_rate": 0.0008  # 0.08% funding rate
                    }
                ]
            }
        except Exception as e:
            return {
                "error": str(e),
                "total_balance": 0,
                "futures_pnl": 0,
                "staking_total": 0,
                "launchpool_total": 0,
                "positions": []
            }
