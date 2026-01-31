import os
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions

PROJECT_ID = "gen-lang-client-0464468580"
LOCATION = "global"

def list_data_stores():
    client = discoveryengine.DataStoreServiceClient(
        client_options=ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
    )
    
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
    
    print(f"🔎 Listing Data Stores in: {parent}")
    try:
        response = client.list_data_stores(parent=parent)
        for ds in response:
            print(f"✅ Found Data Store Name: {ds.name}")
            # Extract ID from full name: projects/.../dataStores/{ID}
            ds_id = ds.name.split("/")[-1]
            print(f"🔹 Extracted ID: {ds_id}")
            return ds_id
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    list_data_stores()
