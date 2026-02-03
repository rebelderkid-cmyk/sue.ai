from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time

def run():
    with sync_playwright() as p:
        print("🚀 Launching Browser (Attempt 2)...")
        # Use args to mimic real browser better
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        ) 
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="th-TH",
            timezone_id="Asia/Bangkok"
        )
        
        # Apply stealth
        page = context.new_page()
        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        print("🌐 Navigating to Home Page (to warm up cookies)...")
        
        # Monitor Requests
        page.on("request", lambda request: print(f"REQ: {request.url}") if "json" in request.url or "api" in request.url else None)
        
        try:
            page.goto("https://ratchakitcha.soc.go.th/", timeout=60000)
            time.sleep(5)
            
            # Simulate Interaction
            page.mouse.move(100, 100)
            page.mouse.down()
            time.sleep(0.5)
            page.mouse.up()
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Home navigation error: {e}")

        print("🌐 Navigating to Search Result...")
        try:
            page.goto("https://ratchakitcha.soc.go.th/search-result", timeout=60000)
        except Exception as e:
            print(f"⚠️ Search navigation error: {e}")

        print("⏳ Waiting for Cloudflare/Page Load (30s)...")
        time.sleep(30)

        # Screenshot
        print("📸 Taking screenshot...")
        page.screenshot(path="scrapers/ratchakitcha/debug_screenshot.png")

        print(f"📄 Page Title: {page.title()}")
        
        # Check content
        if page.locator("input.form-control").count() > 0:
             print("✅ Found Search Input Box (Success!)")
        
        # Print HTML snippet to be sure
        print("Snippet:", page.content()[:500])
        
        browser.close()

if __name__ == "__main__":
    run()
