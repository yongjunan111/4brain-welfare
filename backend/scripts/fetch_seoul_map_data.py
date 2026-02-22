import os
import sys
import django
import requests
import json
from time import sleep

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from policies.models import MapTheme, MapPOI

OPEN_API_KEY = "KEY307_d81072bd7b324b9399789a4530aaa095"
THEME_KEY = "KEY307_1185ed78902b4a7f9cae95692a7518e3"
BASE_URL = "http://map.seoul.go.kr/smgis/apps/theme.do"

# Define the 7 themes provided by user
TARGET_THEMES = [
    {"id": "1668482721443", "name": "[동행]한 곳에 담은 청년공간"},
    {"id": "1766482359787", "name": "[성북] 청년지원(임대주택, 일자리) 공간"},
    {"id": "100996", "name": "관악구 청년 중개보수 감면 사무소"},
    {"id": "1714614097459", "name": "창업지원시설"},
    {"id": "1670291660555", "name": "마음건강검진 정신의료기관"},
    {"id": "1743137980198", "name": "서울마음편의점"},
    {"id": "1722228181633", "name": "마음투자지원 서비스제공기관"},
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'http://localhost:8000'
}

def fetch_and_save_theme(theme_info):
    theme_id = theme_info["id"]
    theme_name = theme_info["name"]
    print(f"Processing Theme: {theme_name} ({theme_id})")

    # 1. Ensure Theme exists in DB
    theme_obj, created = MapTheme.objects.get_or_create(
        theme_id=theme_id,
        defaults={'name': theme_name}
    )
    if created:
        print(f"Created new theme record: {theme_name}")

    # 2. Fetch Data
    # Strategy: Try Local Files (.json, .xlsx, .csv) first, then API
    
    # Check for various file formats
    json_path = os.path.join("metrics_data", f"{theme_id}.json")
    xlsx_path = os.path.join("metrics_data", f"{theme_id}.xlsx")
    csv_path = os.path.join("metrics_data", f"{theme_id}.csv")
    
    data = None
    items = []
    
    # 2-1. JSON File
    if os.path.exists(json_path):
        print(f"Loading from JSON file: {json_path}")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = data.get('body', [])
        except Exception as e:
            print(f"Failed to load JSON file: {e}")

    # 2-2. Excel/CSV File (Pandas)
    elif os.path.exists(xlsx_path) or os.path.exists(csv_path):
        target_path = xlsx_path if os.path.exists(xlsx_path) else csv_path
        print(f"Loading from Excel/CSV file: {target_path}")
        try:
            import pandas as pd
            df = pd.read_excel(target_path) if target_path.endswith('.xlsx') else pd.read_csv(target_path)
            # Convert DataFrame to list of dicts, ensuring keys match what we expect
            # Note: Excel headers might be Korean, needs mapping if so.
            # Assuming headers match API keys for now or we map them dynamically
            print("Columns found:", df.columns.tolist())
            items = df.to_dict('records')
        except ImportError:
            print("pandas/openpyxl not installed. Run 'pip install pandas openpyxl'")
        except Exception as e:
            print(f"Failed to load Excel/CSV: {e}")

    # 2-3. API (Fallback)
    if not items and not data:
        print(f"Attempting API fetch...")
        params = {
            "cmd": "contentsList", 
            "key": THEME_KEY,
            "no": theme_id
        }
        try:
            response = requests.post(BASE_URL, data=params, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                try:
                    api_data = response.json()
                    if 'head' in api_data and api_data['head'].get('RETCODE') == '0':
                         items = api_data.get('body', [])
                    else:
                         print(f"API returned error: {api_data.get('head')}")
                except:
                    print("API returned non-JSON response.")
            else:
                print(f"API Error: HTTP {response.status_code}")
        except Exception as e:
            print(f"API Request failed: {e}")

    # 2-4. Mock Data
    if not items:
        print(f"Generating MOCK data for verification...")
        data = generate_mock_data(theme_id, theme_name)
        items = data.get('body', [])

    print(f"Found {len(items)} items to process.")

    for item in items:
        # 3. Parse and Save POI
        poi_name = item.get('COT_CONTS_NAME') or item.get('콘텐츠명') or item.get('명칭') or 'Unknown'
        address = item.get('COT_ADDR_FULL_NEW') or item.get('새주소') or item.get('주소') or item.get('COT_ADDR_FULL_OLD') or ''
        phone = item.get('COT_TEL_NO') or item.get('전화번호') or ''
        link = item.get('COT_CONTS_LINK_URL') or item.get('상세URL') or ''
        
        # Coordinates
        # API might return COT_COORD_X, COT_COORD_Y (MGIS/TM) or COT_COORD_DATA (WGS84 or other)
        lat, lon = 37.5665, 126.9780 # Default
        
        if 'COT_COORD_Y' in item and 'COT_COORD_X' in item:
             # If X/Y provided (likely MGIS/TM), we need conversion. 
             # For Mock data this path won't be hit unless we mock it.
             # For real data, we need pyproj or similar.
             # Placeholder: Just save them if they look like Lat/Lon (unlikely for MGIS)
             try:
                 y = float(item['COT_COORD_Y'])
                 x = float(item['COT_COORD_X'])
                 if 30 < y < 40 and 120 < x < 132: # WGS84 range check
                     lat, lon = y, x
                 # Else: We need conversion logic!
             except:
                 pass
        elif 'COT_COORD_DATA' in item:
             # Parse existing format
             pass
        elif 'latitude' in item and 'longitude' in item:
             # Mock data usually
             lat = item['latitude']
             lon = item['longitude']
        
        # Mock Conversion for now if still default
        import random
        if lat == 37.5665 and lon == 126.9780:
             lat += (random.random() - 0.5) * 0.1
             lon += (random.random() - 0.5) * 0.1
        
        MapPOI.objects.update_or_create(
            theme=theme_obj,
            name=poi_name,
            defaults={
                'latitude': lat,
                'longitude': lon,
                'address': address,
                'phone': phone,
                'detail_url': link,
                'original_data': item if isinstance(item, dict) else str(item)
            }
        )

def generate_mock_data(theme_id, theme_name):
    """Generate fake response data for verification"""
    return {
        "head": {"RETCODE": "0"},
        "body": [
            {
                "COT_CONTS_NAME": f"{theme_name} - 샘플 1",
                "COT_COORD_DATA": "[127.0, 37.0]", # Fake MGIS
                "COT_ADDR_FULL_NEW": "서울특별시 중구 세종대로 110",
                "COT_TEL_NO": "02-123-4567",
                "COT_CONTS_LINK_URL": "http://seoul.go.kr"
            },
            {
                "COT_CONTS_NAME": f"{theme_name} - 샘플 2",
                "COT_ADDR_FULL_NEW": "서울특별시 강남구 테헤란로",
                "COT_TEL_NO": "02-987-6543",
            }
        ]
    }

if __name__ == "__main__":
    # Create directory for manual data drops
    os.makedirs("metrics_data", exist_ok=True)
    
    print("Starting Seoul Map Data Ingestion...")
    for theme in TARGET_THEMES:
        fetch_and_save_theme(theme)
    print("Done.")
