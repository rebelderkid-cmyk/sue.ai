import os
import json
import time
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = "global" # Vertex AI Search data stores are usually global
DATA_STORE_ID = os.getenv("DATA_STORE_ID")

def import_documents(jsonl_file):
    """
    Imports documents from a JSONL file to Vertex AI Search.
    """
    client = discoveryengine.DocumentServiceClient(
        client_options=ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
    )

    parent = client.branch_path(
        project=PROJECT_ID,
        location=LOCATION,
        data_store=DATA_STORE_ID,
        branch="default_branch",
    )

    print(f"🚀 Starting Import to: {parent}")
    
    # Read JSONL and convert to Discovery Engine Documents
    documents = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                
                # Dynamic mapping based on our Schema
                doc_id = f"Deka_{data.get('decision_no', '').replace('/', '-')}"
                if not data.get('decision_no'):
                     # Fallback for OCR files without decision_no yet
                     doc_id = f"File_{data.get('source_file')}"

                # Construct StructData (The payload)
                struct_data = {
                    "year": int(data.get("year", 0)) if data.get("year") else 0,
                    "outcome": data.get("outcome", "N/A"),
                    "full_text": data.get("full_text_snippet") or data.get("content", ""),
                    "filename": data.get("source_file", ""),
                    "sections": data.get("sections_found", [])
                }
                
                # Create Document Object
                doc = discoveryengine.Document(
                    id=doc_id,
                    struct_data=struct_data
                    # Content removed due to Data Store config restriction
                )
                documents.append(doc)
                
            except Exception as e:
                print(f"Skipping line error: {e}")

    # Batch Import (Vertex AI handles batching, but good to chunk locally if massive)
    # Ideally, use GCS Import for massive datasets. For < 10k files, inline is fine.
    
    print(f"📦 Prepared {len(documents)} documents for upload...")
    
    # Maximum 100 docs per request recommended or use ImportDocuments API with GCS
    # Here we use inline import for simplicity of the script
    
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        inline_source=discoveryengine.ImportDocumentsRequest.InlineSource(
            documents=documents
        ),
        # SET RECONCILIATION_MODE to UPSERT to allow updates
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
    )

    operation = client.import_documents(request=request)
    print(f"⏳ Operation started: {operation.operation.name}")
    
    # Wait for result
    response = operation.result()
    print(f"✅ Import Complete!")
    print(response)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ingest_to_vertex.py <path_to_jsonl_or_json>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    
    # Convert single JSON to list for the function if needed, or handle directory
    # For now, assume input is a JSONL or a single JSON we want to test
    
    # Check if single JSON
    if input_path.endswith('.json') and not input_path.endswith('.jsonl'):
        # Convert single JSON to a temp JSONL list for the function
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        # Normalize data format if coming from 'Old Deka' structure
        # Old Deka might need mapping. Let's inspect one first usually.
        # Assuming minimal mapping for test:
        norm_data = {
            "decision_no": data.get("decision_no", "Test-1"),
            "year": data.get("year", 2568),
            "outcome": data.get("outcome", "Test Outcome"),
            "content": data.get("content", str(data)), # Dump all as content if schema varies
            "source_file": os.path.basename(input_path)
        }
        
        temp_file = "temp_ingest.jsonl"
        with open(temp_file, 'w') as f:
            f.write(json.dumps(norm_data) + "\n")
            
        import_documents(temp_file)
        os.remove(temp_file)
        
    else:
        import_documents(input_path)
