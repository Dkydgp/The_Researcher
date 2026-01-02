import requests

base_url = "http://localhost:8000/api/history/dates"
timeframes = ["DAILY", "WEEKLY", "MONTHLY"]

print("Checking Archive API...")
for tf in timeframes:
    try:
        r = requests.get(f"{base_url}?timeframe={tf}")
        data = r.json()
        print(f"{tf}: {data.get('dates')}")
    except Exception as e:
        print(f"{tf} Error: {e}")
