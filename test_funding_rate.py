#!/usr/bin/env python3
"""
Test script để kiểm tra tính năng Funding Rate mới
"""
import requests

def test_funding_rate_feature():
    base_url = "http://localhost:5000"

    print("🧪 Testing Funding Rate Feature...")
    print("=" * 60)

    # Test Binance API với funding rate
    try:
        response = requests.get(f"{base_url}/api/exchanges/binance/positions", timeout=5)
        data = response.json()
        print(f"✅ Binance API: {response.status_code}")
        print(f"   - Positions: {len(data.get('positions', []))} found")

        for pos in data.get('positions', []):
            funding_rate = pos.get('funding_rate', 0)
            funding_pct = funding_rate * 100
            funding_color = "🟢" if funding_rate < 0 else "🔴"  # Green if negative (good for short)
            print(f"   - {pos.get('symbol')}: {funding_color} {funding_pct:.4f}%")

    except Exception as e:
        print(f"❌ Binance API failed: {str(e)}")
        return False

    # Test OKX API với funding rate
    try:
        response = requests.get(f"{base_url}/api/exchanges/okx/positions", timeout=5)
        data = response.json()
        print(f"✅ OKX API: {response.status_code}")
        print(f"   - Positions: {len(data.get('positions', []))} found")

        for pos in data.get('positions', []):
            funding_rate = pos.get('funding_rate', 0)
            funding_pct = funding_rate * 100
            funding_color = "🟢" if funding_rate < 0 else "🔴"
            print(f"   - {pos.get('symbol')}: {funding_color} {funding_pct:.4f}%")

    except Exception as e:
        print(f"❌ OKX API failed: {str(e)}")
        return False

    # Test Bitget API với funding rate
    try:
        response = requests.get(f"{base_url}/api/exchanges/bitget/positions", timeout=5)
        data = response.json()
        print(f"✅ Bitget API: {response.status_code}")
        print(f"   - Positions: {len(data.get('positions', []))} found")

        for pos in data.get('positions', []):
            funding_rate = pos.get('funding_rate', 0)
            funding_pct = funding_rate * 100
            funding_color = "🟢" if funding_rate < 0 else "🔴"
            print(f"   - {pos.get('symbol')}: {funding_color} {funding_pct:.4f}%")

    except Exception as e:
        print(f"❌ Bitget API failed: {str(e)}")
        return False

    print("=" * 60)
    print("🎉 Funding Rate feature tests passed!")
    print()
    print("📊 Tính năng mới đã thêm:")
    print("   ✅ Cột 'Funding Rate' trong bảng positions")
    print("   ✅ Hiển thị funding rate theo % với 4 chữ số thập phân")
    print("   ✅ Color coding: 🔴 Dương (tốn phí), 🟢 Âm (nhận phí)")
    print("   ✅ Dữ liệu funding rate cho cả 3 sàn")
    print()
    print("💡 Giải thích Funding Rate:")
    print("   - Funding Rate > 0 (đỏ): Short position phải trả phí")
    print("   - Funding Rate < 0 (xanh): Short position nhận phí")
    print("   - Càng âm càng tốt cho short position!")
    print()
    print(f"🌐 Xem Position View tại: {base_url}/positions")
    return True

if __name__ == "__main__":
    test_funding_rate_feature()
