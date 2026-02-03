import json
import requests
from bs4 import BeautifulSoup
import time
import os

SESSION_FILE = "scrapers/ratchakitcha/session.json"
OUTPUT_FILE = "scrapers/ratchakitcha/ratchakitcha_data.jsonl"

def load_session():
    with open(SESSION_FILE, "r") as f:
        return json.load(f)

def scrape_page(page_no=0):
    session_data = load_session()
    
    # Setup Cookies
    jar = requests.cookies.RequestsCookieJar()
    for cookie in session_data["cookies"]:
        jar.set(cookie["name"], cookie["value"], domain=cookie["domain"], path=cookie["path"])

    headers = {
        "User-Agent": session_data["user_agent"],
        "Referer": "https://ratchakitcha.soc.go.th/search-result",
        "Origin": "https://ratchakitcha.soc.go.th",
        "Content-Type": "application/x-www-form-urlencoded" # Form submit
    }

    # Form Data
    payload = {
        "action": "search",
        "search-type": "",
        "page_no": str(page_no),
        "search-keyword": "", 
        "search-field": "content",
        "sort": "desc",
        "tab-value": "1",
        "date-from": "",
        "date-to": "",
        "category[]": "กฎหมาย/คำวินิจฉัย",
        "sub-category[]": "รัฐธรรมนูญ" # Targeted Sub-Category
    }

    print(f"📡 Scraping Page {page_no} (Sub-Category: รัฐธรรมนูญ)...")
    resp = requests.post("https://ratchakitcha.soc.go.th/search-result", 
                         data=payload, 
                         cookies=jar, 
                         headers=headers, 
                         timeout=30)

    if resp.status_code != 200:
        print(f"❌ Error: Status {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    entries = soup.find_all("div", class_="post-thumbnail-entry")
    
    results = []
    for entry in entries:
        try:
            link_tag = entry.find("a", class_="m-b-10")
            if not link_tag: continue
            
            title = link_tag.get_text(strip=True)
            pdf_url = link_tag["href"]
            
            meta_div = entry.find("div", class_="m-t-10")
            date_text = meta_div.find("span", class_="post-date").get_text(strip=True) if meta_div else ""
            
            # Extract Volume/Section info
            cats = meta_div.find_all("span", class_="post-category")
            book_info = cats[0].get_text(strip=True) if cats else ""
            
            results.append({
                "title": title,
                "pdf_url": pdf_url,
                "date": date_text,
                "book_info": book_info,
                "page": page_no
            })
        except Exception as e:
            print(f"⚠️ Parse error: {e}")
            continue

    print(f"✅ Found {len(results)} items on page {page_no}")
    return results

def run_scraper(max_pages=3):
    all_data = []
    for i in range(max_pages):
        data = scrape_page(i)
        if not data:
            print("🛑 No more data or error.")
            break
        all_data.extend(data)
        
        # Save incrementally
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        time.sleep(2) # Polite delay

if __name__ == "__main__":
    # Clear old output
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    run_scraper(max_pages=2)
