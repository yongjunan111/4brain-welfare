import requests
import json

OPEN_API_KEY = "KEY307_d81072bd7b324b9399789a4530aaa095"
THEME_KEY = "KEY307_1185ed78902b4a7f9cae95692a7518e3"
BASE_URL = "http://map.seoul.go.kr/smgis/apps/theme.do"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def test_key(name, key, cmd, params):
    print(f"\n--- Testing {name} ---")
    all_params = {"cmd": cmd, "key": key}
    all_params.update(params)
    
    try:
        # Try both GET and POST
        print(f"Trying GET with {all_params}...")
        resp = requests.get(BASE_URL, params=all_params, headers=HEADERS, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Content Type: {resp.headers.get('Content-Type')}")
        print(f"Response Preview: {resp.text[:500]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test 1: Open API Key with themeListNew
    test_key("Open API Key", OPEN_API_KEY, "themeListNew", {"theme_type": "1,2,3,4,5", "page_size": 1, "page_no": 1})
    
    # Test 2: Theme Key with contentsList (using one valid ID from their list)
    # Theme: [동행]한 곳에 담은 청년공간 1668482721443
    test_key("Theme Key", THEME_KEY, "contentsList", {"theme_id": "1668482721443"})
