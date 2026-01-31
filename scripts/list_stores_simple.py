from google.cloud import discoveryengine_v1 as ds

def list_stores():
    client = ds.DataStoreServiceClient()
    parent = "projects/gen-lang-client-0464468580/locations/global/collections/default_collection"
    
    for s in client.list_data_stores(parent=parent):
        print(f"{s.display_name}: {s.name.split('/')[-1]}")

if __name__ == '__main__':
    list_stores()
