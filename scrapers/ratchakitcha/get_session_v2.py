import time
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def save_session():
    print("🚀 Launching STEALTH Browser...")
    print("👉 Please SOLVE the Cloudflare Challenge manually.")
    
    with sync_playwright() as p:
        # Launch with arguments to hide automation flags
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox", 
                "--disable-infobars"
            ]
        )
        
        # Create context with realistic user agent and viewport
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="th-TH",
            timezone_id="Asia/Bangkok"
        )
        
        # Apply stealth scripts to the page
        page = context.new_page()
        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        # Navigate
        print("🌐 Navigating to Ratchakitcha...")
        try:
            page.goto("https://ratchakitcha.soc.go.th/search-result", timeout=90000)
        except Exception as e:
            print(f"⚠️ Navigation note: {e}")

        # Wait indefinitely for success signal (user solves captcha)
        print("⏳ Waiting for you to solve the captcha... (I will wait until I see the search box)")
        
        try:
            # Wait for the search input box to appear
            page.wait_for_selector("input.form-control", state="visible", timeout=0) 
            print("✅ CAPTCHA BYPASSED! Search box detected.")
            
            # Allow a moment for cookies to settle
            time.sleep(3)

            # Extract Data
            cookies = context.cookies()
            user_agent = page.evaluate("navigator.userAgent")
            
            session_data = {
                "cookies": cookies,
                "user_agent": user_agent
            }

            # Save
            with open("scrapers/ratchakitcha/session.json", "w") as f:
                json.dump(session_data, f, indent=2)
                
            print("💾 Session saved successfully to 'scrapers/ratchakitcha/session.json'")
            
        except Exception as e:
            print(f"❌ Error or Window Closed: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    save_session()
