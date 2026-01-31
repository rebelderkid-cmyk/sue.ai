
import urllib.request
import json

REPO_ID = "open-law-data-thailand/soc-ratchakitcha"
API_URL = f"https://huggingface.co/api/datasets/{REPO_ID}/tree/main"

def list_files(path=""):
    url = API_URL
    if path:
        url += f"/{path}"
    
    print(f"Inspecting: {url}")
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            for item in data:
                print(f"- {item['type']}: {item['path']}")
                if item['type'] == 'directory':
                     print(f"  [Drilling down into {item['path']}...]")
                     list_files_recursive(item['path'])
                     break 
    except Exception as e:
        print(f"Error accessing {url}: {e}")

def list_files_recursive(path):
    url = API_URL + f"/{path}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            for item in data:
                print(f"  - {item['type']}: {item['path']}")
    except Exception as e:
        print(f"Error accessing {url}: {e}")

print("--- PDF ---")
list_files("pdf")
