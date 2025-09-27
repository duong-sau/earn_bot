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
    from Define import root_path  # nếu có
except Exception:
    root_path = os.getcwd()

logger = logging.getLogger("binance_ms")

class BinanceMicroservice(BaseMicroservice):
    """BinanceMicroservice (async)
    Nhiệm vụ:
      - Duy trì short cho mỗi perp_symbol trong config['coins'].
      - Watch positions (websocket) -> nếu short < target => market sell bù (theo step).
      - Collateral watcher: kiểm tra số dư USDT futures; nếu < lower -> vay + transfer; nếu > upper -> repay.
      - Ghi log vào shared_log_path để Discord đọc.

    Cấu hình coin ví dụ:
      {"symbol": "SXP/USDT", "perp_symbol": "SXP/USDT:USDT", "short_size":15000, "step":10}
    Nếu không có perp_symbol sẽ tự suy ra symbol+':USDT'.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.futures_lower = float(config.get('futures_balance_lower', 50))
        self.futures_upper = float(config.get('futures_balance_upper', 100))
        self.api_key, self.api_secret = self._load_keys(config)
        self._short_cache: Dict[str, float] = {}

        # Async infra
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_async: Optional[asyncio.Event] = None
        self._position_tasks: List[asyncio.Task] = []
        self._collateral_task: Optional[asyncio.Task] = None
        self.binance_spot = None
        self.binance_fut = None

    # ---------- Lifecycle override ----------
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
            try:
                self._loop.run_until_complete(self._cleanup())
            except Exception:
                pass
            self._loop.close()

    # ---------- Setup / Cleanup ----------
    def _load_keys(self, config: Dict[str, Any]):
        if config.get('api_key') and config.get('api_secret'):
            return config['api_key'], config['api_secret']
        candidates = [
            os.path.join(root_path, '_settings', 'hedge.json'),
            os.path.join(root_path, 'code', '_settings', 'hedge.json'),
            os.path.join('_settings', 'hedge.json'),
        ]
        for p in candidates:
            if os.path.exists(p):
                with contextlib.suppress(Exception):
                    with open(p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    bk = data.get('binance', {})
                    k = bk.get('api_key') or bk.get('key')
                    s = bk.get('api_secret') or bk.get('secret')
                    if k and s:
                        return k, s
        self._log_event('[WARN] Không tìm thấy API key Binance')
        return None, None

    async def _create_clients(self):
        if not (self.api_key and self.api_secret):
            return
        self.binance_spot = ccxt_async.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        self.binance_fut = ccxtpro.binanceusdm({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })
        await self.binance_fut.load_markets()
        self._log_event('Binance clients ready')

    async def _cleanup(self):
        with contextlib.suppress(Exception):
            if self.binance_fut:
                await self.binance_fut.close()
        with contextlib.suppress(Exception):
            if self.binance_spot:
                await self.binance_spot.close()

    # ---------- Main async orchestrator ----------
    async def _async_main(self):
        if not (self.api_key and self.api_secret):
            self._log_event('[ERROR] No API key => exit')
            return
        await self._create_clients()
        # tasks
        self._collateral_task = asyncio.create_task(self._collateral_watcher())
        for coin in self.coins:
            perp = coin.get('perp_symbol') or self._infer_perp_symbol(coin.get('symbol'))
            t = asyncio.create_task(self._position_watcher(perp, coin))
            self._position_tasks.append(t)
        await self._stop_async.wait()
        # cancel tasks
        for t in self._position_tasks:
            t.cancel()
        if self._collateral_task:
            self._collateral_task.cancel()
        await asyncio.gather(*self._position_tasks, return_exceptions=True)
        if self._collateral_task:
            with contextlib.suppress(Exception):
                await self._collateral_task

    # ---------- Helpers ----------
    def _infer_perp_symbol(self, symbol: str) -> str:
        if not symbol:
            return ''
        if ':USDT' in symbol:
            return symbol
        if symbol.endswith('/USDT'):
            return symbol + ':USDT'
        return symbol

    async def _get_futures_available_usdt(self) -> float:
        with contextlib.suppress(Exception):
            bal = await self.binance_fut.fetch_balance()
            info = bal.get('info', {})
            if 'assets' in info:
                for a in info['assets']:
                    if a.get('asset') == 'USDT':
                        return float(a.get('availableBalance') or a.get('walletBalance') or 0)
            return float(bal.get('free', {}).get('USDT', 0) or 0)
        return 0.0

    async def _borrow_and_transfer(self, amount: float):
        amount = max(1, round(amount))
        try:
            params = {'loanCoin': 'USDT', 'loanAmount': amount, 'collateralCoin': 'SXP'}
            r = await self.binance_spot.sapiv2_post_loan_flexible_borrow(params)
            self._log_event(f"Borrow {amount} USDT ok")
            await self.binance_spot.sapi_post_futures_transfer({'asset': 'USDT', 'amount': str(amount), 'type': 1})
            self._log_event(f"Transfer {amount} USDT spot->futures")
        except Exception as e:
            self._log_event(f"[ERROR] borrow failed: {e}")

    async def _repay(self, amount: float):
        amount = max(1, round(amount))
        try:
            await self.binance_spot.sapi_post_futures_transfer({'asset': 'USDT', 'amount': str(amount), 'type': 2})
            await asyncio.sleep(2)
            params = {'loanCoin': 'USDT', 'repayAmount': amount, 'collateralCoin': 'SXP'}
            await self.binance_spot.sapiv2_post_loan_flexible_repay(params)
            self._log_event(f"Repay {amount} USDT ok")
        except Exception as e:
            self._log_event(f"[ERROR] repay failed: {e}")

    async def _open_short(self, perp: str, target: float, step: int):
        cur = self._short_cache.get(perp, 0.0)
        need = target - cur
        if need <= 0:
            return
        if step > 0:
            rounded = int(need / step) * step
            if rounded <= 0:
                rounded = step
        else:
            rounded = need
        try:
            await self.binance_fut.create_order(perp, 'market', 'sell', rounded, params={'reduceOnly': False})
            self._log_event(f"Open short {perp} {rounded} (cur={cur} target={target})")
        except Exception as e:
            self._log_event(f"[ERROR] open short {perp}: {e}")

    # ---------- Watchers ----------
    async def _collateral_watcher(self):
        POLL = 30
        while not self._stop_async.is_set():
            try:
                avail = await self._get_futures_available_usdt()
                self._log_event(f"[binance] futures avail USDT={avail:.2f}")
                if avail < self.futures_lower - 20:
                    need = self.futures_upper - avail
                    need = max(20, need)
                    self._log_event(f"Low balance -> borrow {need}")
                    await self._borrow_and_transfer(need)
                elif avail > self.futures_upper + 20:
                    repay = min(avail - self.futures_upper, avail)
                    if repay >= 20:
                        self._log_event(f"High balance -> repay {repay}")
                        await self._repay(repay)
            except Exception as e:
                self._log_event(f"[WARN] collateral watcher: {e}")
            await asyncio.wait([self._stop_async.wait()], timeout=POLL)

    async def _position_watcher(self, perp: str, coin_cfg: Dict[str, Any]):
        target = float(coin_cfg.get('short_size', 0))
        step = int(coin_cfg.get('step', 1) or 1)
        while not self._stop_async.is_set():
            try:
                positions = await self.binance_fut.watch_positions([perp])
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
                    self._log_event(f"[binance] {perp} short={short_qty} target={target}")
                if short_qty < target - step:
                    await self._open_short(perp, target, step)
            except Exception as e:
                self._log_event(f"[ERROR] watcher {perp}: {e}")
                await asyncio.sleep(5)

    # ---------- Overrides ----------
    def fetch_assets(self) -> Dict[str, Any]:
        return {"balances": {}, "positions": self.positions}

    def get_position_data(self) -> Dict[str, Any]:
        """Lấy thông tin position và earn cho API"""
        try:
            # Mock data cho demo - sau này anh có thể thay bằng API thực
            return {
                "total_balance": 5000.0,
                "futures_pnl": 150.75,
                "simple_earn_total": 2500.0,
                "cross_margin_loan": -800.0,
                "positions": [
                    {
                        "symbol": "BTC/USDT:USDT",
                        "side": "SHORT",
                        "size": 0.1,
                        "entry_price": 67000.0,
                        "mark_price": 66500.0,
                        "pnl": 50.0,
                        "roe": 1.25,
                        "funding_rate": 0.0001  # 0.01% funding rate
                    },
                    {
                        "symbol": "ETH/USDT:USDT",
                        "side": "SHORT",
                        "size": 2.5,
                        "entry_price": 2600.0,
                        "mark_price": 2580.0,
                        "pnl": 50.0,
                        "roe": 1.92,
                        "funding_rate": -0.0025  # -0.25% funding rate (negative = good for short)
                    }
                ]
            }
        except Exception as e:
            return {
                "error": str(e),
                "total_balance": 0,
                "futures_pnl": 0,
                "simple_earn_total": 0,
                "cross_margin_loan": 0,
                "positions": []
            }
