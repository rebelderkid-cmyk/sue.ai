from google.cloud import discoveryengine_v1beta as discoveryengine
from google.api_core.client_options import ClientOptions
import os
from dotenv import load_dotenv

load_dotenv("src/backend/.env")

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
# DATA_STORE_ID = os.getenv("DATA_STORE_ID") 
DATA_STORE_ID = "deka_1768730204117" # Force Deka Store
LOCATION = "global"

def search_sample():
    client_options = (
        ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
        if LOCATION != "global"
        else None
    )
    
    client = discoveryengine.SearchServiceClient(client_options=client_options)
    
    serving_config = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/servingConfigs/default_search"
    
    print(f"🔎 Searching in: {serving_config}")
    
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query="ฆ่าผู้อื่น",
        page_size=3,
    )
    
    try:
        response = client.search(request=request)
        print(f"✅ Found {len(response.results)} results.")
        for result in response.results:
            data = {}
            if hasattr(result.document, "struct_data"):
                 data = dict(result.document.struct_data)
            if not data and hasattr(result.document, "derived_struct_data"):
                 data = dict(result.document.derived_struct_data)
                 
            print(f" - ID: {result.document.id}")
            # print(f" - Title: {data.get('title', 'No Title')}")
            # print(f" - File Name (Vertex): {data.get('file_name', 'N/A')}")
            print(f" - DATA KEYs: {list(data.keys())}")
            print(f" - FULL DATA: {data}")
            print("-" * 20)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    search_sample()
