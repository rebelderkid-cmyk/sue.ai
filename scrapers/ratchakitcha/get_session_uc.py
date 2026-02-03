import undetected_chromedriver as uc
import time
import json
import os

def save_session():
    print("🚀 Launching Undetected Chrome...")
    print("👉 Please SOLVE the Cloudflare Challenge in the opened window.")
    
    # Create a user data folder to save state
    user_data_dir = os.path.abspath("scrapers/ratchakitcha/chrome_profile")
    
    options = uc.ChromeOptions()
    # options.add_argument(f"--user-data-dir={user_data_dir}") # Optional: Keeps login state
    
    # Initialize driver - version_main=144 ensures compatibility with your installed Chrome
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=144)

    try:
        print("🌐 Navigating to Ratchakitcha...")
        driver.get("https://ratchakitcha.soc.go.th/search-result")

        # Wait loop
        print("⏳ Waiting for you to solve the captcha...")
        print("   (I am watching for the 'inputs' to appear on the page)")
        
        while True:
            try:
                # Check if the search input exists
                inputs = driver.find_elements("css selector", "input.form-control")
                if len(inputs) > 0:
                    print("✅ CAPTCHA BYPASSED! Search box found.")
                    break
            except:
                pass
            time.sleep(1)
        
        # Success! Save cookies
        print("💾 Saving Session...")
        cookies = driver.get_cookies()
        user_agent = driver.execute_script("return navigator.userAgent;")
        
        session_data = {
            "cookies": cookies,
            "user_agent": user_agent
        }

        with open("scrapers/ratchakitcha/session.json", "w") as f:
            json.dump(session_data, f, indent=2)
            
        print("🎉 Session saved to 'scrapers/ratchakitcha/session.json'")
        print("⚠️ Closing browser in 5 seconds...")
        time.sleep(5)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    save_session()
