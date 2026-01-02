import requests

try:
    print("Checking Archive Page...")
    r = requests.get("http://localhost:8000/archive")
    if r.status_code == 200:
        print("Success: /archive returned 200 OK")
        print("Title check:", "<title>Archive | Nifty-5 AI</title>" in r.text)
    else:
        print(f"Failed: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")
