import requests

THEME_KEY = "KEY307_1185ed78902b4a7f9cae95692a7518e3"
THEME_ID = "1668482721443"
BASE_URL = "http://map.seoul.go.kr/smgis/apps/theme.do"

def test():
    referers = [
        "http://localhost:8000",
        "http://localhost:8000/",
        "http://localhost:3000",
        "http://localhost:3000/",
        "http://localhost",
        "http://map.seoul.go.kr/",
        "https://map.seoul.go.kr/"
    ]
    
    params = {
        "cmd": "contentsList",
        "key": THEME_KEY,
        "no": THEME_ID
    }
    
    for ref in referers:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Referer': ref
        }
        print(f"Testing Referer: {ref}")
        try:
            # POST is often required for theme.do
            resp = requests.post(BASE_URL, data=params, headers=headers, timeout=3)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    code = data.get('head', {}).get('RETCODE')
                    print(f"Result: {code}")
                    if code == '0': 
                         print(">>> SUCCESS <<<")
                         return
                except:
                    print(f"Non-JSON response (Length: {len(resp.text)})")
            else:
                print(f"Status: {resp.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test()
