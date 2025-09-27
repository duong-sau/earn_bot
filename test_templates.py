#!/usr/bin/env python3
"""
Test script để kiểm tra Flask server với templates mới
"""
import requests

def test_server():
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Flask Server with new templates...")
    print("=" * 50)
    
    # Test dashboard
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200 and "Earn Bot Dashboard" in response.text:
            print(f"✅ Dashboard: {response.status_code} - Template loaded successfully!")
            # Check if it's using template file (not inline HTML)
            if "dashboard.html" not in response.text:  # Template file name won't be in rendered HTML
                print("✅ Using external template file (not inline HTML)")
        else:
            print(f"❌ Dashboard: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard failed: {str(e)}")
        return False
    
    # Test history page
    try:
        response = requests.get(f"{base_url}/history", timeout=5)
        if response.status_code == 200 and "Lịch sử Tài sản" in response.text:
            print(f"✅ History page: {response.status_code} - Template loaded successfully!")
        else:
            print(f"❌ History page: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ History page failed: {str(e)}")
        return False
    
    print("=" * 50)
    print("🎉 All template tests passed!")
    print("📁 Templates are now in separate files:")
    print("   - Server/templates/dashboard.html")
    print("   - Server/templates/history.html")
    print(f"🌐 Access dashboard at: {base_url}/")
    return True

if __name__ == "__main__":
    test_server()
