import requests
import json

try:
    print("Fetching WEEKLY data...")
    # Get Date
    r = requests.get('http://localhost:8000/api/history/dates?timeframe=WEEKLY')
    dates = r.json().get('dates')
    print(f"Weekly Dates: {dates}")
    
    if dates:
        date = dates[0]
        print(f"Fetching Weekly data for {date}...")
        r = requests.get(f"http://localhost:8000/api/history/{date}?timeframe=WEEKLY")
        data = r.json()
        if data.get('data'):
            item = data['data'][0]
            print(f"Sample Item Keys: {item['prediction'].keys()}")
            print(f"Week Low Target: {item['prediction'].get('week_low_target')}")
        else:
            print("No data in weekly response")
            
except Exception as e:
    print(f"Error: {e}")
