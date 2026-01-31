import requests
import time
import concurrent.futures

URL = "https://sue-ai-backend-289893785097.us-central1.run.app/"
CONCURRENT_REQUESTS = 50
TOTAL_REQUESTS = 200

def fetch(request_id):
    start = time.time()
    try:
        response = requests.get(URL)
        duration = time.time() - start
        status = response.status_code
        print(f"Request {request_id}: Status {status} ({duration:.2f}s)")
        return status
    except Exception as e:
        print(f"Request {request_id}: Failed - {e}")
        return "ERROR"

def main():
    print(f"🚀 Starting Load Test on {URL}")
    print(f"Concurrency: {CONCURRENT_REQUESTS}, Total: {TOTAL_REQUESTS}")
    
    start_time = time.time()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(fetch, i) for i in range(TOTAL_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    total_time = time.time() - start_time
    success_count = results.count(200)
    print(f"\n✅ Load Test Completed in {total_time:.2f}s")
    print(f"Success Rate: {success_count}/{TOTAL_REQUESTS} ({success_count/TOTAL_REQUESTS*100:.2f}%)")

if __name__ == "__main__":
    main()
