import requests
import json
import os

OPEN_API_KEY = "KEY307_d81072bd7b324b9399789a4530aaa095"
THEME_KEY = "KEY307_1185ed78902b4a7f9cae95692a7518e3"
THEME_ID = "1668482721443"

ENDPOINTS = [
    "http://map.seoul.go.kr/smgis/apps/theme.do",
    "https://map.seoul.go.kr/smgis/apps/theme.do",
    "http://map.seoul.go.kr/smgis/apps/poi.do",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'http://map.seoul.go.kr/'
}

def log_response(name, method, url, params, resp):
    print(f"\n[{name}] {method} {url}")
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")
    
    filename = f"debug_resp_{name}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n")
        f.write(f"Params: {params}\n")
        f.write(f"Status: {resp.status_code}\n")
        f.write(f"Headers: {dict(resp.headers)}\n")
        f.write("\nBODY:\n")
        f.write(resp.text)
    print(f"Saved response to {filename}")

if __name__ == "__main__":
    # Test 1: themeListNew with OPEN_API_KEY (Exact parameters from user)
    try:
        url = ENDPOINTS[0]
        params = {"cmd": "themeListNew", "key": OPEN_API_KEY, "theme_type": "2,3,4", "page_size": 10, "page_no": 1}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        log_response("themeListNew_Exact", "GET", url, params, resp)
    except Exception as e:
        print(f"Test 1 Error: {e}")

    # Test 2: contentsList with THEME_KEY on theme.do (GET this time)
    try:
        url = ENDPOINTS[0]
        # Try GET
        params = {"cmd": "contentsList", "key": THEME_KEY, "no": THEME_ID}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        log_response("contentsList_GET", "GET", url, params, resp)
    except Exception as e:
        print(f"Test 2 Error: {e}")

    # Test 3: getContentsListAll with THEME_KEY on theme.do (GET)
    try:
        url = ENDPOINTS[0]
        params = {"cmd": "getContentsListAll", "key": THEME_KEY, "no": THEME_ID}
        # Also try 'theme_id' key just in case
        # params = {"cmd": "getContentsListAll", "key": THEME_KEY, "theme_id": THEME_ID} 
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        log_response("getContentsListAll_GET", "GET", url, params, resp)
    except Exception as e:
        print(f"Test 3 Error: {e}")
