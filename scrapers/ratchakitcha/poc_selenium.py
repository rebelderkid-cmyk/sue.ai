import undetected_chromedriver as uc
import time
import json

def run():
    print("🚀 Launching Undetected Chrome...")
    options = uc.ChromeOptions()
    # options.add_argument('--headless=new') # Headless often triggers detection, try with it first.
    # Note: UC in headless mode is tricky.
    
    driver = uc.Chrome(options=options, headless=True, use_subprocess=True, version_main=144)

    try:
        print("🌐 Navigating to Home Page...")
        driver.get("https://ratchakitcha.soc.go.th/")
        time.sleep(10)
        
        print("🌐 Navigating to Search Result...")
        driver.get("https://ratchakitcha.soc.go.th/search-result")
        
        print("⏳ Waiting for Cloudflare (30s)...")
        time.sleep(30)
        
        print(f"📄 Page Title: {driver.title}")
        
        # Check for inputs
        inputs = driver.find_elements("tag name", "input")
        if len(inputs) > 0:
            print(f"✅ Found {len(inputs)} input elements.")
            for i in inputs[:3]:
                print(f"   - Type: {i.get_attribute('type')}, ID: {i.get_attribute('id')}")
        else:
            print("❌ No inputs found (Blocked).")

        # Capture Logs (if possible)
        # UC doesn't make capturing network logs easy without performance logging enabled.
        
        driver.save_screenshot("scrapers/ratchakitcha/debug_selenium.png")
        print("📸 Screenshot saved.")
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
