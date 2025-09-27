#!/usr/bin/env python3
"""
Entrypoint chạy đơn lẻ một microservice (binance|okx|bitget) trong container.
Cách dùng:
  python run_microservice.py --service binance
Hoặc qua biến môi trường:
  SERVICE=binance python run_microservice.py

Script sẽ:
  - Đọc _settings/hedge.json để lấy strategy/coins.
  - Cho phép override một số tham số bằng biến môi trường:
      FUTURES_BAL_LOWER, FUTURES_BAL_UPPER
  - Ghi log chung vào logs/shared.log (mount ra ngoài để Discord đọc).

Thoát an toàn: gửi SIGTERM / SIGINT -> dừng service rồi exit.
"""
from __future__ import annotations
import os
import json
import time
import argparse
import signal
import threading
from typing import Dict, Any, Type

# Import các lớp microservice
from Microservices.binance_service import BinanceMicroservice
from Microservices.okx_service import OKXMicroservice
from Microservices.bitget_service import BitgetMicroservice

SERVICE_MAP: Dict[str, Type] = {
    'binance': BinanceMicroservice,
    'okx': OKXMicroservice,
    'bitget': BitgetMicroservice,
}

HEDGE_CANDIDATES = [
    os.path.join('_settings', 'hedge.json'),
    os.path.join('code', '_settings', 'hedge.json'),
]

def load_strategy() -> Dict[str, Any]:
    for p in HEDGE_CANDIDATES:
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('strategy', {})
            except Exception:
                continue
    return {}

def build_service_config(name: str, shared_log: str) -> Dict[str, Any]:
    strategy = load_strategy()
    strat_cfg = strategy.get(name, {}) if strategy else {}
    cfg: Dict[str, Any] = {
        'coins': strat_cfg.get('coins', []),
        'futures_balance_lower': float(os.environ.get('FUTURES_BAL_LOWER', strat_cfg.get('futures_balance_lower', 50))),
        'futures_balance_upper': float(os.environ.get('FUTURES_BAL_UPPER', strat_cfg.get('futures_balance_upper', 100))),
        'shared_log_path': shared_log,
    }
    return cfg

def main():
    parser = argparse.ArgumentParser(description='Run single exchange microservice')
    parser.add_argument('--service', '-s', required=False, default=os.environ.get('SERVICE'), choices=SERVICE_MAP.keys(), help='Tên microservice: binance|okx|bitget')
    parser.add_argument('--log', default=os.environ.get('SHARED_LOG', 'logs/shared.log'), help='Đường dẫn shared log')
    args = parser.parse_args()
    if not args.service:
        raise SystemExit('Thiếu --service hoặc biến môi trường SERVICE')

    os.makedirs(os.path.dirname(args.log), exist_ok=True)

    svc_cls = SERVICE_MAP[args.service]
    cfg = build_service_config(args.service, args.log)

    service = svc_cls(args.service, cfg)

    stop_event = threading.Event()

    def handle_signal(signum, frame):
        print(f"[ENTRYPOINT] Nhận signal {signum}, stopping service...")
        if service.state.running:
            try:
                service.stop()
            except Exception as e:
                print(f"[ENTRYPOINT] Lỗi stop: {e}")
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    print(f"[ENTRYPOINT] Starting service '{args.service}' với config: {cfg}")
    service.start()

    # Vòng lặp chờ
    try:
        while not stop_event.is_set():
            time.sleep(2)
    finally:
        if service.state.running:
            service.stop()
        print('[ENTRYPOINT] Thoát.')

if __name__ == '__main__':
    main()

