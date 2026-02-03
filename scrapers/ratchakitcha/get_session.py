import time
import json
from playwright.sync_api import sync_playwright

def save_session():
    print("🚀 Launching Browser for Manual Authentication...")
    print("👉 Please SOLVE the Cloudflare Challenge manually in the opened window.")
    
    with sync_playwright() as p:
        # Launch non-headless browser so user can interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        # Navigate to target
        print("🌐 Navigating to https://ratchakitcha.soc.go.th/search-result")
        page.goto("https://ratchakitcha.soc.go.th/search-result", timeout=60000)

        # Wait for user to bypass
        print("⏳ Waiting for you to solve the captcha...")
        # We wait until the specific search input appears, indicating success
        try:
            page.wait_for_selector("input.form-control", timeout=120000) # 2 minutes to solve
            print("✅ Success! Search box detected.")
        except:
            print("⚠️ Timed out waiting for bypass. Saving what we have anyway...")

        # Extract Cookies and User Agent
        cookies = context.cookies()
        user_agent = page.evaluate("navigator.userAgent")
        
        session_data = {
            "cookies": cookies,
            "user_agent": user_agent
        }

        # Save to file
        with open("scrapers/ratchakitcha/session.json", "w") as f:
            json.dump(session_data, f, indent=2)
            
        print("💾 Session saved to 'scrapers/ratchakitcha/session.json'")
        print("🎉 You can now run the automated scraper!")
        
        time.sleep(2) # Graceful close
        browser.close()

if __name__ == "__main__":
    save_session()
