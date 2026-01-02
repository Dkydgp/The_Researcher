import requests
import json

try:
    r = requests.get('http://localhost:8000/api/predictions/daily')
    data = r.json()
    if 'predictions' in data:
        print(f"Found {len(data['predictions'])} predictions")
        for p in data['predictions']:
            print(f"Symbol: {p['symbol']} | Target: {p['prediction'].get('target_date')}")
            
except Exception as e:
    print(f"Error: {e}")
