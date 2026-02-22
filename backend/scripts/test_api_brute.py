import requests

KEY_THEME = "KEY307_1185ed78902b4a7f9cae95692a7518e3"
THEME_ID = "1668482721443"

def test():
    protocols = ["http", "https"]
    versions = ["v1", "v2", "v3", "v4", "v5", "v6"]
    
    for proto in protocols:
        for ver in versions:
            url = f"{proto}://map.seoul.go.kr/openapi/{ver}/{KEY_THEME}/public"
            print(f"Testing: {url}")
            try:
                resp = requests.get(url, params={"no": THEME_ID}, timeout=2)
                print(f"[{resp.status_code}] {resp.text[:100]}")
                if resp.status_code == 200 and "RETCODE" not in resp.text:
                    print("!!! POTENTIAL SUCCESS !!!")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    test()
