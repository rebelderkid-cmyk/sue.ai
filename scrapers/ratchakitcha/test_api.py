import json
import requests
import re

def test_access():
    print("🔓 Loading session...")
    with open("scrapers/ratchakitcha/session.json", "r") as f:
        session_data = json.load(f)

    # Convert playwright cookies to requests cookies
    jar = requests.cookies.RequestsCookieJar()
    for cookie in session_data["cookies"]:
        jar.set(cookie["name"], cookie["value"], domain=cookie["domain"], path=cookie["path"])

    headers = {
        "User-Agent": session_data["user_agent"],
        "Referer": "https://ratchakitcha.soc.go.th/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    print("📡 Sending request to search-result page...")
    try:
        url = "https://ratchakitcha.soc.go.th/search-result"
        resp = requests.get(url, cookies=jar, headers=headers, timeout=15)
        
        print(f"📄 Status Code: {resp.status_code}")
        
        if "Just a moment" in resp.text:
            print("❌ Still blocked by Cloudflare (Challenge Page detected).")
        elif resp.status_code == 200:
            print("✅ Access Granted!")
            print(f"📄 Page content length: {len(resp.text)}")
            
            # Inspect for API calls in JS
            api_matches = re.findall(r"['\"]/api/[\w/]+['\"]", resp.text)
            if api_matches:
                print("🔎 Found potential API endpoints in HTML:")
                for match in set(api_matches):
                    print(f"   - {match}")
            else:
                print("ℹ️ No obvious API endpoints found in regex scan.")
                
            # Save HTML for inspection
            with open("scrapers/ratchakitcha/debug_page.html", "w") as f:
                f.write(resp.text)
            print("💾 Saved HTML to debug_page.html")
            
        else:
            print("⚠️ Unexpected status.")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_access()
