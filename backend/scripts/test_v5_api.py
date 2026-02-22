import requests
import json

# Keys
THEME_KEY = "KEY307_1185ed78902b4a7f9cae95692a7518e3" # User said "OpenAPIThemeKey"
OPEN_API_KEY = "KEY307_d81072bd7b324b9399789a4530aaa095"

# The user provided Base URL
BASE_URL = f"https://map.seoul.go.kr/openapi/v5/{THEME_KEY}/public"

# Target Theme ID (Youth Space)
THEME_ID = "1668482721443"

def test_v5_endpoint():
    print(f"Testing Base URL: {BASE_URL}")
    
    # Try different parameter names for Theme ID since the doc snippet is vague
    param_candidates = ['id', 'no', 'theme_id', 'themeId', 'tid']
    
    for param in param_candidates:
        print(f"\n--- Testing param: {param} ---")
        params = {
            param: THEME_ID,
            "page_no": 1,
            "page_size": 5
        }
        
        try:
            # User said GET method
            resp = requests.get(BASE_URL, params=params, timeout=10)
            print(f"Status: {resp.status_code}")
            print(f"URL: {resp.url}")
            print(f"Response: {resp.text[:500]}")
            
            if resp.status_code == 200 and "RETCODE" not in resp.text:
                print(">>> SUCCESS POSSIBLE <<<")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_v5_endpoint()
