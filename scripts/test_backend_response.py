
import requests
import json
import os

# Backend URL (Cloud Run)
URL = "https://sue-ai-backend-289893785097.asia-southeast1.run.app/api/chat"
# Local Test (ถ้าอยากเทส local)
# URL = "http://localhost:8000/api/chat"

payload = {
    "question": "ฆ่าผู้อื่นโดยเจตนา",
    "history": []
}

try:
    print(f"📡 Sending request to {URL}...")
    response = requests.post(URL, json=payload, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Response Received!")
        
        sources = data.get("sources", [])
        if not sources:
            print("❌ No sources found.")
        else:
            print(f"📚 Found {len(sources)} sources.")
            for i, src in enumerate(sources):
                print(f"\n--- Source {i+1} ---")
                print(f"ID: {src.get('id')}")
                print(f"PDF URL: {src.get('pdf_url')}")
                print(f"Snippet: {src.get('text')[:100]}...")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"💥 Exception: {e}")
