import requests
import json

# Keys
KEY_THEME = "KEY307_1185ed78902b4a7f9cae95692a7518e3"  # 테마 발급키
KEY_OPEN = "KEY307_d81072bd7b324b9399789a4530aaa095"   # 발급키

THEME_ID = "1668482721443"

def try_url(name, url, params):
    print(f"\n[{name}] Requesting: {url}")
    try:
        resp = requests.get(url, params=params, timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:300]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Case 1: Base URL with Theme Key (User's instruction)
    # v5, public, theme_id or no
    base_v5_theme_public = f"https://map.seoul.go.kr/openapi/v5/{KEY_THEME}/public"
    try_url("v5_ThemeKey_Public_no", base_v5_theme_public, {"no": THEME_ID})
    try_url("v5_ThemeKey_Public_id", base_v5_theme_public, {"id": THEME_ID})
    try_url("v5_ThemeKey_Public_theme_id", base_v5_theme_public, {"theme_id": THEME_ID})
    try_url("v5_ThemeKey_Public_tid", base_v5_theme_public, {"tid": THEME_ID}) # Some docs use tid

    # Case 2: Base URL with Open Key
    base_v5_open_public = f"https://map.seoul.go.kr/openapi/v5/{KEY_OPEN}/public"
    try_url("v5_OpenKey_Public_no", base_v5_open_public, {"no": THEME_ID})

    # Case 3: JSON endpoint structure (Common in Seoul API)
    # /openapi/v5/{Key}/json/{ThemeId}/1/100
    base_v5_json_path = f"https://map.seoul.go.kr/openapi/v5/{KEY_THEME}/json/{THEME_ID}/1/5"
    try_url("v5_ThemeKey_JSON_Path", base_v5_json_path, {})
    
    base_v5_open_json_path = f"https://map.seoul.go.kr/openapi/v5/{KEY_OPEN}/json/{THEME_ID}/1/5"
    try_url("v5_OpenKey_JSON_Path", base_v5_open_json_path, {})
    
