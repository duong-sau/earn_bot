#!/usr/bin/env python3
"""
Test script để kiểm tra Binance API thật
"""
import requests
import json

def test_real_binance_api():
    base_url = "http://localhost:5000"
    
    print("🧪 Testing REAL Binance API Integration...")
    print("=" * 60)
    
    # Test Binance API với dữ liệu thật
    try:
        print("🔄 Calling Binance API...")
        response = requests.get(f"{base_url}/api/exchanges/binance/positions", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Binance API: SUCCESS!")
            print(f"📊 Response received:")
            
            # Kiểm tra có lỗi không
            if 'error' in data:
                print(f"❌ API Error: {data['error']}")
                return False
            
            # Hiển thị thông tin account
            print(f"💰 Total Balance: ${data.get('total_balance', 0):,.2f}")
            print(f"📈 Futures PnL: ${data.get('futures_pnl', 0):,.2f}")
            print(f"🏦 Simple Earn: ${data.get('simple_earn_total', 0):,.2f}")
            print(f"💳 Cross Margin Loan: ${data.get('cross_margin_loan', 0):,.2f}")
            
            positions = data.get('positions', [])
            print(f"📊 Active Positions: {len(positions)} found")
            
            if positions:
                print("\n🎯 Position Details:")
                for i, pos in enumerate(positions, 1):
                    symbol = pos.get('symbol', 'N/A')
                    side = pos.get('side', 'N/A')
                    size = pos.get('size', 0)
                    entry_price = pos.get('entry_price', 0)
                    mark_price = pos.get('mark_price', 0)
                    pnl = pos.get('pnl', 0)
                    roe = pos.get('roe', 0)
                    funding_rate = pos.get('funding_rate', 0) * 100
                    
                    pnl_color = "🟢" if pnl >= 0 else "🔴"
                    funding_color = "🟢" if funding_rate < 0 else "🔴"
                    
                    print(f"   {i}. {symbol}")
                    print(f"      Side: {side}")
                    print(f"      Size: {size:,.4f}")
                    print(f"      Entry: ${entry_price:,.4f}")
                    print(f"      Mark: ${mark_price:,.4f}")
                    print(f"      PnL: {pnl_color} ${pnl:,.2f} ({roe:+.2f}%)")
                    print(f"      Funding: {funding_color} {funding_rate:+.4f}%")
                    print()
            else:
                print("   📝 No active positions found")
            
            # Kiểm tra xem có phải là dữ liệu thật không
            if data.get('total_balance', 0) == 5000.0 and len(positions) == 2:
                print("⚠️  WARNING: This might be mock data (typical test values)")
                print("   - Check if API keys are correct")
                print("   - Verify Binance account has positions")
            else:
                print("✅ SUCCESS: This appears to be REAL Binance data!")
                
        else:
            print(f"❌ Binance API: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Binance API: Exception - {str(e)}")
        return False
    
    print("=" * 60)
    print("🎉 Binance API Test Complete!")
    print("\n💡 What's implemented:")
    print("   ✅ Real-time futures balance (USDT)")
    print("   ✅ Real-time spot balance (USDT)") 
    print("   ✅ Active futures positions")
    print("   ✅ Live PnL and ROE calculation")
    print("   ✅ Real funding rates from API")
    print("   🔄 Simple Earn (placeholder)")
    print("   🔄 Cross Margin Loan (placeholder)")
    
    print(f"\n🌐 View in browser: {base_url}/positions")
    return True

if __name__ == "__main__":
    test_real_binance_api()
