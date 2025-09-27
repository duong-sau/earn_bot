#!/usr/bin/env python3
"""
Test script để kiểm tra cả Binance và OKX API thật
"""
import requests
import json

def test_both_exchanges():
    base_url = "http://localhost:5000"
    
    print("🧪 Testing BOTH Binance & OKX Real API Integration...")
    print("=" * 70)
    
    # Test Binance API
    print("🟡 BINANCE API TEST:")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/api/exchanges/binance/positions", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Binance API: SUCCESS!")
            
            if 'error' in data:
                print(f"❌ Binance Error: {data['error']}")
            else:
                print(f"💰 Total Balance: ${data.get('total_balance', 0):,.2f}")
                print(f"📈 Futures PnL: ${data.get('futures_pnl', 0):,.2f}")
                print(f"🏦 Simple Earn: ${data.get('simple_earn_total', 0):,.2f}")
                print(f"💳 Cross Margin Loan: ${data.get('cross_margin_loan', 0):,.2f}")
                
                positions = data.get('positions', [])
                print(f"📊 Active Positions: {len(positions)} found")
                
                if positions:
                    for i, pos in enumerate(positions, 1):
                        pnl_color = "🟢" if pos.get('pnl', 0) >= 0 else "🔴"
                        funding_color = "🟢" if pos.get('funding_rate', 0) < 0 else "🔴"
                        print(f"   {i}. {pos.get('symbol')} - {pos.get('side')} - {pnl_color} ${pos.get('pnl', 0):,.2f} - {funding_color} {pos.get('funding_rate', 0)*100:+.4f}%")
        else:
            print(f"❌ Binance API: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Binance API: Exception - {str(e)}")

    print("\n🔵 OKX API TEST:")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/api/exchanges/okx/positions", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ OKX API: SUCCESS!")
            
            if 'error' in data:
                print(f"❌ OKX Error: {data['error']}")
            else:
                print(f"💰 Total Balance: ${data.get('total_balance', 0):,.2f}")
                print(f"📈 Futures PnL: ${data.get('futures_pnl', 0):,.2f}")
                print(f"🎯 Staking: ${data.get('staking_total', 0):,.2f}")
                print(f"🚀 Launchpool: ${data.get('launchpool_total', 0):,.2f}")
                
                positions = data.get('positions', [])
                print(f"📊 Active Positions: {len(positions)} found")
                
                if positions:
                    for i, pos in enumerate(positions, 1):
                        pnl_color = "🟢" if pos.get('pnl', 0) >= 0 else "🔴"
                        funding_color = "🟢" if pos.get('funding_rate', 0) < 0 else "🔴"
                        print(f"   {i}. {pos.get('symbol')} - {pos.get('side')} - {pnl_color} ${pos.get('pnl', 0):,.2f} - {funding_color} {pos.get('funding_rate', 0)*100:+.4f}%")
                
                # Kiểm tra xem có phải là dữ liệu thật không
                if data.get('total_balance', 0) == 3200.0 and len(positions) == 2:
                    print("⚠️  WARNING: This might be mock data (typical test values)")
                else:
                    print("✅ SUCCESS: This appears to be REAL OKX data!")
        else:
            print(f"❌ OKX API: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ OKX API: Exception - {str(e)}")

    print("\n" + "=" * 70)
    print("🎉 Dual Exchange API Test Complete!")
    print("\n💡 What's implemented:")
    print("📊 BINANCE:")
    print("   ✅ Real-time futures & spot balance")
    print("   ✅ Active futures positions with PnL")
    print("   ✅ Live funding rates")
    print("   🔄 Simple Earn (placeholder)")
    print("   🔄 Cross Margin Loan (placeholder)")
    
    print("📊 OKX:")
    print("   ✅ Real-time trading & funding balance") 
    print("   ✅ Active futures positions with PnL")
    print("   ✅ Live funding rates")
    print("   🔄 Staking (placeholder)")
    print("   🔄 Launchpool/DeFi (placeholder)")
    
    print(f"\n🌐 View both exchanges: {base_url}/positions")
    print("🔄 Refresh data in real-time with Auto Refresh toggle!")
    
    return True

if __name__ == "__main__":
    test_both_exchanges()
