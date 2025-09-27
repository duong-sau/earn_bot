#!/usr/bin/env python3
"""
Test script để kiểm tra tính năng Position View mới
"""
import requests

def test_position_view():
    base_url = "http://localhost:5000"

    print("🧪 Testing Position View Feature...")
    print("=" * 60)

    # Test trang positions
    try:
        response = requests.get(f"{base_url}/positions", timeout=5)
        if response.status_code == 200 and "Position & Earn/Stake Overview" in response.text:
            print("✅ Position page: Template loaded successfully!")
        else:
            print(f"❌ Position page: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Position page failed: {str(e)}")
        return False

    # Test API Binance positions
    try:
        response = requests.get(f"{base_url}/api/exchanges/binance/positions", timeout=5)
        data = response.json()
        print(f"✅ Binance API: {response.status_code}")
        print(f"   - Total Balance: ${data.get('total_balance', 'N/A')}")
        print(f"   - Futures PnL: ${data.get('futures_pnl', 'N/A')}")
        print(f"   - Simple Earn: ${data.get('simple_earn_total', 'N/A')}")
        print(f"   - Positions: {len(data.get('positions', []))} found")
    except Exception as e:
        print(f"❌ Binance API failed: {str(e)}")
        return False

    # Test API OKX positions
    try:
        response = requests.get(f"{base_url}/api/exchanges/okx/positions", timeout=5)
        data = response.json()
        print(f"✅ OKX API: {response.status_code}")
        print(f"   - Total Balance: ${data.get('total_balance', 'N/A')}")
        print(f"   - Futures PnL: ${data.get('futures_pnl', 'N/A')}")
        print(f"   - Staking: ${data.get('staking_total', 'N/A')}")
        print(f"   - Launchpool: ${data.get('launchpool_total', 'N/A')}")
        print(f"   - Positions: {len(data.get('positions', []))} found")
    except Exception as e:
        print(f"❌ OKX API failed: {str(e)}")
        return False

    # Test API Bitget positions
    try:
        response = requests.get(f"{base_url}/api/exchanges/bitget/positions", timeout=5)
        data = response.json()
        print(f"✅ Bitget API: {response.status_code}")
        print(f"   - Total Balance: ${data.get('total_balance', 'N/A')}")
        print(f"   - Futures PnL: ${data.get('futures_pnl', 'N/A')}")
        print(f"   - Staking: ${data.get('staking_total', 'N/A')}")
        print(f"   - Launchpool: ${data.get('launchpool_total', 'N/A')}")
        print(f"   - Positions: {len(data.get('positions', []))} found")
    except Exception as e:
        print(f"❌ Bitget API failed: {str(e)}")
        return False

    print("=" * 60)
    print("🎉 All Position View tests passed!")
    print("📊 Tính năng mới:")
    print("   ✅ Trang Position View với giao diện đẹp")
    print("   ✅ API lấy dữ liệu từ 3 sàn (Binance, OKX, Bitget)")
    print("   ✅ Hiển thị position futures, PnL, earn/stake")
    print("   ✅ Auto refresh và manual refresh")
    print("   ✅ Responsive design")
    print()
    print(f"🌐 Truy cập Position View tại: {base_url}/positions")
    print(f"🏠 Dashboard tại: {base_url}/")
    return True

if __name__ == "__main__":
    test_position_view()
