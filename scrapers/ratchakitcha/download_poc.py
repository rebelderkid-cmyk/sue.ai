import os
import json
import requests
import time
from scrape_ratchakitcha import scrape_page, load_session

DOWNLOAD_DIR = "scrapers/ratchakitcha/downloads_poc"

def download_pdf(url, title, session_cookies):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    
    # Clean filename: Keep Thai characters, remove invalid FS chars
    invalid_chars = '<>:"/\\|?*'
    safe_title = "".join([c for c in title if c not in invalid_chars])
    safe_title = safe_title.strip()[:150] # Limit length
    
    filename = os.path.join(DOWNLOAD_DIR, f"{safe_title}.pdf")
    
    if os.path.exists(filename):
        print(f"⏩ Skipping {filename} (Already exists)")
        return True

    print(f"⬇️ Downloading: {title}...")
    try:
        # Use cookies for download request too, to mimic browser
        jar = requests.cookies.RequestsCookieJar()
        for cookie in session_cookies["cookies"]:
            jar.set(cookie["name"], cookie["value"], domain=cookie["domain"], path=cookie["path"])
            
        headers = {
            "User-Agent": session_cookies["user_agent"],
            "Referer": "https://ratchakitcha.soc.go.th/search-result"
        }

        resp = requests.get(url, cookies=jar, headers=headers, stream=True, timeout=60)
        if resp.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Saved to {filename}")
            return True
        else:
            print(f"❌ Failed to download {url}: Status {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Download Error: {e}")
        return False

def run_poc():
    print("🚀 Starting POC: Category 'กฎหมาย/คำวินิจฉัย'")
    
    # 1. Scrape Metadata (First 1 page only for POC)
    print("Phase 1: Fetching Metadata...")
    items = scrape_page(0) 
    
    if not items:
        print("❌ No items found. Check session or filter.")
        return

    # 2. Download PDFs
    print(f"\nPhase 2: Downloading {len(items)} PDFs...")
    session_data = load_session()
    
    success_count = 0
    for item in items:
        if download_pdf(item["pdf_url"], item["title"], session_data):
            success_count += 1
        time.sleep(1) # Polite delay
        
    print(f"\n🎉 POC Complete. Downloaded {success_count}/{len(items)} files.")
    print(f"📂 Files are in: {os.path.abspath(DOWNLOAD_DIR)}")

if __name__ == "__main__":
    run_poc()
