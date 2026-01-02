import requests
import json

try:
    r = requests.get('http://localhost:8000/api/predictions/daily')
    data = r.json()
    found = False
    for p in data['predictions']:
        if p['symbol'] == 'TCS':
            print(f"TCS Target: {p['prediction'].get('target_date')}")
            found = True
    if not found:
        print("TCS not found in response")
except Exception as e:
    print(f"Error: {e}")
