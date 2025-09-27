from flask import Flask, jsonify, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import atexit
import sys, os

# Đảm bảo thêm project root vào sys.path khi chạy trực tiếp bằng đường dẫn tuyệt đối
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Microservices.manager import MicroserviceManager

app = Flask(__name__)
manager = MicroserviceManager()
manager.start_enabled_services()

scheduler = BackgroundScheduler(timezone="UTC")

# Lịch snapshot vào 02:00,10:00,18:00 UTC (có thể đổi sang giờ địa phương nếu cần)
SNAPSHOT_HOURS = [2, 10, 18]

def schedule_snapshots():
    for h in SNAPSHOT_HOURS:
        scheduler.add_job(take_and_log_snapshot, 'cron', hour=h, minute=0, id=f"snapshot_{h}", replace_existing=True)

def take_and_log_snapshot():
    snap = manager.asset_snapshot()
    app.logger.info(f"Asset snapshot: total={snap['total_usdt']}")

schedule_snapshots()
scheduler.start()
atexit.register(lambda: scheduler.shutdown(wait=False))

@app.route('/api/services', methods=['GET'])
def list_services():
    return jsonify(manager.list_services())

@app.route('/api/services/<name>/start', methods=['POST'])
def start_service(name):
    ok = manager.start_service(name)
    return (jsonify({"status": "started"}), 200) if ok else (jsonify({"error": "not found or already running"}), 404)

@app.route('/api/services/<name>/stop', methods=['POST'])
def stop_service(name):
    ok = manager.stop_service(name)
    return (jsonify({"status": "stopped"}), 200) if ok else (jsonify({"error": "not found or already stopped"}), 404)

@app.route('/api/asset/snapshot', methods=['POST'])
def manual_snapshot():
    snap = manager.asset_snapshot()
    return jsonify(snap)

@app.route('/api/asset/history', methods=['GET'])
def asset_history():
    limit = request.args.get('limit')
    limit_int = int(limit) if limit else None
    data = manager.load_history(limit_int)
    return jsonify(data)

@app.route('/api/ping')
def ping():
    return jsonify({"time": datetime.utcnow().isoformat() + 'Z'})

@app.route('/')
def dashboard():
    """Trang chủ hiển thị dashboard"""
    services = manager.list_services()
    return render_template('dashboard.html', services=services, request=request)

@app.route('/history')
def history_page():
    """Trang xem lịch sử tài sản"""
    return render_template('history.html')

@app.route('/positions')
def positions_page():
    """Trang xem position và earn/stake"""
    return render_template('positions.html')

@app.route('/api/exchanges/binance/positions', methods=['GET'])
def get_binance_positions():
    """API lấy thông tin position và earn từ Binance"""
    try:
        # Lấy service binance từ manager
        binance_service = None
        for service_name, service_obj in manager.services.items():
            if service_name == 'binance' and hasattr(service_obj, 'get_position_data'):
                binance_service = service_obj
                break

        if not binance_service:
            return jsonify({
                'error': 'Binance service not available',
                'total_balance': 0,
                'futures_pnl': 0,
                'simple_earn_total': 0,
                'cross_margin_loan': 0,
                'positions': []
            }), 200

        # Gọi method để lấy dữ liệu
        data = binance_service.get_position_data()
        return jsonify(data)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'total_balance': 0,
            'futures_pnl': 0,
            'simple_earn_total': 0,
            'cross_margin_loan': 0,
            'positions': []
        }), 200

@app.route('/api/exchanges/okx/positions', methods=['GET'])
def get_okx_positions():
    """API lấy thông tin position và stake từ OKX"""
    try:
        # Lấy service okx từ manager
        okx_service = None
        for service_name, service_obj in manager.services.items():
            if service_name == 'okx' and hasattr(service_obj, 'get_position_data'):
                okx_service = service_obj
                break

        if not okx_service:
            return jsonify({
                'error': 'OKX service not available',
                'total_balance': 0,
                'futures_pnl': 0,
                'staking_total': 0,
                'launchpool_total': 0,
                'positions': []
            }), 200

        # Gọi method để lấy dữ liệu
        data = okx_service.get_position_data()
        return jsonify(data)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'total_balance': 0,
            'futures_pnl': 0,
            'staking_total': 0,
            'launchpool_total': 0,
            'positions': []
        }), 200

@app.route('/api/exchanges/bitget/positions', methods=['GET'])
def get_bitget_positions():
    """API lấy thông tin position và stake từ Bitget"""
    try:
        # Lấy service bitget từ manager
        bitget_service = None
        for service_name, service_obj in manager.services.items():
            if service_name == 'bitget' and hasattr(service_obj, 'get_position_data'):
                bitget_service = service_obj
                break

        if not bitget_service:
            return jsonify({
                'error': 'Bitget service not available',
                'total_balance': 0,
                'futures_pnl': 0,
                'staking_total': 0,
                'launchpool_total': 0,
                'positions': []
            }), 200

        # Gọi method để lấy dữ liệu
        data = bitget_service.get_position_data()
        return jsonify(data)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'total_balance': 0,
            'futures_pnl': 0,
            'staking_total': 0,
            'launchpool_total': 0,
            'positions': []
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
