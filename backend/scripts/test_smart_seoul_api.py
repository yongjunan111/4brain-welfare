import requests
import json
import time

# User provided keys
OPEN_API_KEY = "KEY307_d81072bd7b324b9399789a4530aaa095"
THEME_KEY = "KEY307_1185ed78902b4a7f9cae95692a7518e3"

# Theme List provided by user
THEMES = [
    {"id": "1668482721443", "name": "[동행]한 곳에 담은 청년공간"},
    {"id": "1766482359787", "name": "[성북] 청년지원(임대주택, 일자리) 공간"},
    {"id": "100996", "name": "관악구 청년 중개보수 감면 사무소"},
    {"id": "1714614097459", "name": "창업지원시설"},
    {"id": "1670291660555", "name": "마음건강검진 정신의료기관"},
    {"id": "1743137980198", "name": "서울마음편의점"},
    {"id": "1722228181633", "name": "마음투자지원 서비스제공기관"},
]

BASE_URL = "http://map.seoul.go.kr/smgis/apps/theme.do"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'http://localhost:8000'
}

def test_theme_content(theme_id, theme_name):
    print(f"\n--- Testing Theme: {theme_name} ({theme_id}) ---")
    
    # Potential commands from documentation and common patterns
    # Documentation mentions: contentsList, getContentsList all
    # Also seen: themeContentsList
    
    commands_to_try = [
        {"cmd": "getContentsListAll", "id_param": "theme_id"},
        {"cmd": "contentsList", "id_param": "theme_id"},
        {"cmd": "getContentsList", "id_param": "theme_id"},
        {"cmd": "themeContentsList", "id_param": "no"}, # Sometimes 'no' is used
    ]

    for attempt in commands_to_try:
        cmd = attempt["cmd"]
        id_param = attempt["id_param"]
        
        params = {
            "cmd": cmd,
            "key": THEME_KEY,
            id_param: theme_id
        }
        
        try:
            print(f"Trying cmd={cmd}...")
            response = requests.post(BASE_URL, data=params, headers=HEADERS, timeout=5)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Check if we have a valid body or list
                    if isinstance(data, dict):
                        body = data.get('body')
                        if body and len(body) > 0:
                            print(f"SUCCESS with cmd={cmd}!")
                            print(f"Found {len(body)} items.")
                            example = body[0]
                            print("Example Item Keys:", example.keys())
                            print("Example Item COT_COORD_DATA:", example.get('COT_COORD_DATA'))
                            print("Example Item COT_COORD_TYPE:", example.get('COT_COORD_TYPE'))
                            return True
                        elif 'head' in data and data['head'].get('retcode') != '0':
                             print(f"API Error: {data['head'].get('retmsg')}")
                        else:
                             print("Response valid but empty body or unexpected format.")
                    
                    elif isinstance(data, list) and len(data) > 0:
                         print(f"SUCCESS with cmd={cmd} (returned direct list)!")
                         return True

                except json.JSONDecodeError:
                    print(f"Failed to decode JSON. Response start: {response.text[:100]}")
            else:
                print(f"HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Request failed: {e}")
        
        time.sleep(0.5)
    
    return False

if __name__ == "__main__":
    # Test all themes
    for theme in THEMES:
        test_theme_content(theme['id'], theme['name'])
        time.sleep(1)
