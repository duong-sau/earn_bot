import ccxt
import ccxt.pro
import Config

from Core.Define import EXCHANGE

class ExchangeManager:
    def __init__(self, exchange1: EXCHANGE, exchange2: EXCHANGE):
        Config.load_config(exchange1, exchange2)
        targets = {exchange1, exchange2}

        # Khởi tạo tuỳ thuộc sàn được chọn để giảm kết nối không cần
        if EXCHANGE.BINANCE in targets:
            self.binance_exchange = ccxt.binanceusdm({
                'apiKey': Config.binance_api_key,
                'secret': Config.binance_api_secret,
                'enableRateLimit': True,
            })
        else:
            self.binance_exchange = None

        if EXCHANGE.BITGET in targets or EXCHANGE.BITGET_SUB in targets:
            self.bitget_exchange = ccxt.bitget({
                'apiKey': Config.bitget_api_key,
                'secret': Config.bitget_api_secret,
                'password': Config.bitget_password,
                'enableRateLimit': True,
            })
            self.bitget_exchange.options['defaultType'] = 'swap'
            self.bitget_pro = ccxt.pro.bitget({
                'apiKey': Config.bitget_api_key,
                'secret': Config.bitget_api_secret,
                'password': Config.bitget_password,
                'options': {'defaultType': 'swap'}
            })
        else:
            self.bitget_exchange = None
            self.bitget_pro = None

        if EXCHANGE.GATE in targets:
            self.gate_exchange = ccxt.gateio({
                'apiKey': Config.gate_api_key,
                'secret': Config.gate_api_secret,
                'enableRateLimit': True,
            })
            self.gate_exchange.options['defaultType'] = 'swap'
            self.gate_pro = ccxt.pro.gateio({
                'apiKey': Config.gate_api_key,
                'secret': Config.gate_api_secret,
                'uid': "22397301",
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap'
                }
            })
        else:
            self.gate_exchange = None
            self.gate_pro = None

        if EXCHANGE.OKX in targets:
            # okx unified
            self.okx_exchange = ccxt.okx({
                'apiKey': Config.okx_api_key,
                'secret': Config.okx_api_secret,
                'password': Config.okx_password,
                'enableRateLimit': True,
            })
            # ccxt.pro okx
            try:
                self.okx_pro = ccxt.pro.okx({
                    'apiKey': Config.okx_api_key,
                    'secret': Config.okx_api_secret,
                    'password': Config.okx_password,
                    'enableRateLimit': True,
                })
            except Exception:
                self.okx_pro = None
        else:
            self.okx_exchange = None
            self.okx_pro = None

        # Dễ tra cứu tập hợp
        self._map = {
            'binance': self.binance_exchange,
            'bitget': self.bitget_exchange,
            'gate': self.gate_exchange,
            'okx': self.okx_exchange,
        }

    def get(self, name: str):
        return self._map.get(name)
