from google.cloud import discoveryengine_v1 as ds
from google.protobuf.json_format import MessageToDict
import json

PROJECT_ID = "gen-lang-client-0464468580"
ENGINE_ID = "law-criminal-only"

def dump_doc():
    client = ds.SearchServiceClient()
    serving_config = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/engines/{ENGINE_ID}/servingConfigs/default_config"
    
    req = ds.SearchRequest(
        serving_config=serving_config,
        query="มาตรา 288",
        page_size=1
    )
    
    res = client.search(request=req)
    for r in res.results:
        doc_dict = MessageToDict(r.document._pb)
        print(json.dumps(doc_dict, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    dump_doc()
