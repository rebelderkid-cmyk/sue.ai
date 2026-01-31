import os
import time
import glob
import sys

# --- Configuration ---
SOURCE_DIR = "downloads"
OUTPUT_DIR = "cleaned_output"

def get_file_count_recursive(directory, extension):
    return len(glob.glob(os.path.join(directory, "**", f"*.{extension}"), recursive=True))

def monitor():
    print("📊 Deka Processing Monitor")
    print("--------------------------")
    print("Scanning total PDF files... (This may take a moment)")
    
    total_pdfs = get_file_count_recursive(SOURCE_DIR, "pdf")
    
    if total_pdfs == 0:
        print("❌ No PDFs found in source directory.")
        return

    print(f"🎯 Total Target: {total_pdfs} files")
    
    start_time = time.time()
    
    try:
        while True:
            processed_count = get_file_count_recursive(OUTPUT_DIR, "json")
            
            # Calculate metrics
            progress = (processed_count / total_pdfs) * 100 if total_pdfs > 0 else 0
            elapsed = time.time() - start_time
            speed = processed_count / elapsed if elapsed > 0 else 0
            eta = (total_pdfs - processed_count) / speed if speed > 0 else 0
            eta_str = time.strftime("%H:%M:%S", time.gmtime(eta))
            
            # Read Last Processed File from Log
            last_file = "Waiting..."
            try:
                if os.path.exists("processing.log"):
                    # Quick way to get last line
                    with open("processing.log", "rb") as f:
                        try:
                            f.seek(-200, os.SEEK_END)
                            tail = f.read().decode('utf-8', errors='ignore')
                            lines = tail.strip().split('\n')
                            if lines: last_file = lines[-1][:80] # Truncate if too long (Show last 80 chars)
                        except:
                            pass # File might be too short
            except Exception: pass

            # Display (Overwriting line)
            # Use extra spaces to clear previous longer lines
            sys.stdout.write(f"\r🚀 {processed_count}/{total_pdfs} [{progress:.2f}%] | ⚡ {speed:.2f}/s | {eta_str} | 📄 {last_file}      ")
            sys.stdout.flush()
            
            if processed_count >= total_pdfs and total_pdfs > 0:
                print("\n\n✅ Job Complete!")
                break
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor Stopped.")

if __name__ == "__main__":
    monitor()
