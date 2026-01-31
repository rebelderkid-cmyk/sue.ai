import sys
import os
from rag_core import retriever

# Add current directory to sys.path so we can import rag_core
sys.path.append(os.path.join(os.getcwd(), 'src', 'backend'))

def test_search_ordering():
    query = "ฎีกา" # Generic query to get broad results
    print(f"🔎 Testing Search with Query: '{query}'")
    print("⏳ Retrieving docs (expecting Order By: Year DESC)...")
    
    results = retriever(query)
    
    if not results:
        print("❌ No results found. Ingestion might have failed or index is empty.")
        return

    print(f"✅ Found {len(results)} documents.")
    
    years = []
    print("\n--- Top 5 Results ---")
    for i, doc in enumerate(results[:5]):
        y = doc.get('year', 'N/A')
        years.append(str(y))
        print(f"{i+1}. ID: {doc['id']} | Year: {y} | Outcome: {doc['outcome']}")
        
    # Validation Logic
    # Check if years are roughly descending
    # Note: 'N/A' or mixed types might mess this up, but usually we expect ints
    
    print("\n--- Validation ---")
    print(f"Years found: {years}")
    
    # Simple check: Is the first result 2568? (Since we just ingested it)
    if "2568" in years:
        print("✅ SUCCESS: Found Year 2568 in top results!")
    else:
        print("⚠️ WARNING: Year 2568 not found in top results. Indexing might take a few seconds.")

if __name__ == "__main__":
    test_search_ordering()
