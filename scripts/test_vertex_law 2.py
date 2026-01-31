from google.cloud import discoveryengine_v1 as ds
import json

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"
COLLECTION = "default_collection"
ENGINE_ID = "law-ultimate-struct"  # The New Law Engine

def test_law_search(query):
    client = ds.SearchServiceClient()
    serving_config = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/engines/{ENGINE_ID}/servingConfigs/default_config"
    
    print(f"🔍 Searching Law Engine: '{query}'")
    
    req = ds.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=5
    )
    
    try:
        res = client.search(request=req)
        print(f"✅ Found {res.total_size} results.")
        for i, r in enumerate(res.results):
            doc = r.document
            data = doc.struct_data or {}
            # Try to find ID or Title
            print(f"[{i+1}] ID: {doc.id}")
            print(f"    - Title: {data.get('title')}")
            # print(f"    - Text Snippet: {str(data.get('text'))[:100]}...")
            if not data:
                print("    ⚠️ No Struct Data!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_law_search("ประมวลกฎหมายอาญา มาตรา 288")
    test_law_search("ลักทรัพย์")
