import os
import json
import google.generativeai as genai
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from dotenv import load_dotenv

# Load environment variables from .env file (for local testing)
load_dotenv()

# --- Configuration ---
# These should be set in Cloud Run Environment Variables
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "YOUR_PROJECT_ID")
LOCATION = "global" 
# Support Multiple Data Stores
DATA_STORES = {
    "DEKA": os.getenv("DATA_STORE_ID_DEKA"),
    "LAW": os.getenv("DATA_STORE_ID_LAW")
}
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def smart_query_optimizer(user_question, history=None):
    """
    Translates user query into an optimized keyword/natural language query for Vertex AI Search.
    Uses Chat History to handle follow-up questions (e.g., "What about murder?" -> "Supreme Court rulings on murder").
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        
        history_context = ""
        if history:
            # Take last 2 turns to avoid context bloat
            recent_history = history[-4:] 
            history_context = f"Conversation History:\n{json.dumps(recent_history, ensure_ascii=False)}\n"

        prompt = f"""
        Role: You are an expert Lawyer Search Operator.
        Task: Rewrite the user's natural language query into an OPTIMIZED SEARCH QUERY for a Thai Legal Database.
        
        {history_context}
        Current User Query: "{user_question}"
        
        Refinement Rules:
        1. **Contextualize**: If the user asks a follow-up (e.g., "What is the penalty?", "Explain point 2"), use the History to make the query specific (e.g., "Penalty for Theft in Thailand").
        2. **Standalone**: The output must be a standalone search query that makes sense without history.
        3. **Legal Expansion**: Expand legal keywords (e.g., "hit by car" -> "driving negligence collision damage").
        4. **Formalize**: Convert colloquial Thai to Formal Legal Thai.
        5. **Output**: ONLY the refined search string. No JSON.
        
        Optimized Query:
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Optimization Failed: {e}")
        return user_question  # Fallback to original

def retriever(query_str, filters=None):
    """
    Searches documents using Google Vertex AI Search (Discovery Engine).
    Now supports MULTIPLE Data Stores (Deka + Law).
    """
    all_results = []
    
    try:
        # Fix: If global, use default endpoint (None) instead of forcing 'global-discoveryengine'
        client_opts = (
            ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
            if LOCATION != "global"
            else None
        )
        client = discoveryengine.SearchServiceClient(client_options=client_opts)
        
        # Iterate over both Data Stores
        for store_name, store_id in DATA_STORES.items():
            if not store_id:
                print(f"⚠️ Skipping {store_name} search (No ID configured)")
                continue
                
            print(f"🔎 Searching {store_name} (ID: {store_id})...")
            
            serving_config = client.serving_config_path(
                project=PROJECT_ID,
                location=LOCATION,
                data_store=store_id,
                serving_config="default_search",
            )
            
            # Fetch less per store since we combine them
            MAX_PAGES = 2 
            page_token = None
            
            for _ in range(MAX_PAGES):
                request = discoveryengine.SearchRequest(
                    serving_config=serving_config,
                    query=query_str,
                    page_size=10, # 10 from Deka, 10 from Law
                    page_token=page_token if page_token else None,
                    content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                        snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                            return_snippet=True
                        ),
                        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                            summary_result_count=3,
                            include_citations=True
                        )
                    )
                )
                
                try:
                    response = client.search(request)
                except Exception as e:
                     print(f"❌ Error searching {store_name}: {e}")
                     break
                
                for result in response.results:
                    data = {}
                    if hasattr(result.document, "struct_data"):
                         data = dict(result.document.struct_data)
                    if not data and hasattr(result.document, "derived_struct_data"):
                         data = dict(result.document.derived_struct_data)

                    if not data: continue

                    doc_id = result.document.id
                    # Try both 'file_name' (standard) and 'filename' (custom schema)
                    filename = data.get("file_name") or data.get("filename")
                    
                    # Determine PDF URL (Law files might not have PDFs properly named yet, but Deka does)
                    pdf_url = ""
                    # Determine PDF URL based on Filename Prefix (Multi-Bucket Strategy)
                    pdf_url = ""
                    if filename and filename.endswith(".pdf"):
                        if filename.startswith("Deka_"):
                            # Deka files are in 'sue-ai-pdfs-storage'
                            pdf_url = f"https://storage.googleapis.com/sue-ai-pdfs-storage/{filename}"
                        else:
                            # Law/Other files are in 'deka-legal-search-data/pdfs' (Fallback)
                            pdf_url = f"https://storage.googleapis.com/deka-legal-search-data/pdfs/{filename}"

                    # Extract KG Fields for Rich Context
                    # Note: Vertex returns MapComposite/RepeatedComposite which are not directly JSON serializable
                    entities = data.get("entities", {})
                    if hasattr(entities, "_pb"): entities = dict(entities) # Convert to dict if proto 
                    
                    legal_provisions = data.get("legal_provisions", [])
                    if hasattr(legal_provisions, "_pb"): legal_provisions = list(legal_provisions) # Convert to list if proto
                    
                    summary = data.get("summary", "")
                    
                    # Create Rich Text for Logic
                     # Tag the source type for LLM context
                    rich_text = f"[{store_name}] Title: {data.get('document_meta', {}).get('title', 'N/A')}\n"
                    rich_text += f"Summary: {summary}\n"
                    # Safe string conversion
                    rich_text += f"Entities: {str(entities)}\n" 
                    
                    item = {
                        "id": doc_id,
                        "year": data.get("document_meta", {}).get("issue_date", "N/A"),
                        "outcome": data.get("document_meta", {}).get("doc_type", store_name), # 'DEKA' or 'LAW' if not specified
                        "text": rich_text,
                        "pdf_url": pdf_url, 
                        "source_type": store_name
                    }
                    all_results.append(item)
                    
                page_token = response.next_page_token
                if not page_token:
                    break
        
        return all_results
            
    except Exception as e:
        print(f"⚠️ Vertex Search Critical Error: {e}")
        return []

def answer_synthesizer(user_question, docs):
    """
    Synthesizes the answer using Gemini, acting as a Paralegal.
    Same logic as the local version but uses the docs from Vertex.
    """
    if not docs:
        return "ไม่พบข้อมูลฎีกาที่เกี่ยวข้อง (No relevant cases found in Vertex AI)."

    # Prepare Context
    context_str = ""
    for i, doc in enumerate(docs):
        context_str += f"\n[Case {i+1}] ID: {doc.get('id')} (Year: {doc.get('year')})\nOutcome: {doc.get('outcome')}\nContent: {doc.get('text')[:3000]}...\n" # Limit char count per doc to fit context window

    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
    
    prompt = f"""
    Role: You are a highly skilled **Thai Legal Assistant** (ผู้ช่วยทนายความ).
    User: A Lawyer (ทนายความ) who is working on a case.
    Task: Help the lawyer finding relevant legal authorities, including **Supreme Court Opinions (Deka)**, **Legislation (Acts/Codes)**, and **Royal Gazette Announcements**.
    
    Context (Retrieved Legal Documents):
    {context_str}
    
    Lawyer's Query/Facts: "{user_question}"
    
    Instructions:
    1. **Analyze**: Identify the key legal issues from the lawyer's query.
    2. **Synthesize**: Summarize key principles from the retrieved documents.
       - If the document is a **Deka**: Cite the Case ID (e.g., ฎีกาที่ 123/2566) and the ruling/outcome.
       - If the document is a **Law/Act/Regulation**: Cite the Section (มาตรา) and the Act Name (ชื่อกฎหมาย) clearly.
    3. **Application**: Explain how these laws or rulings apply to the user's query.
    4. **Tone**: Professional, Concise, Supportive.
    5. **Language**: Primary language is **Thai (Formal Legal)**.
       - **EXCEPTION**: If the user asks in English or requests a translation, you MUST reply in English or provide the requested translation.
       - If the user asks a question in English, answer in English.
    7. **Formatting (DYNAMIC)**:
       - **For Initial/Complex Legal Queries**: Use the structured format (Headers `###`, Tables).
       - **For Follow-ups / Conversational / Simple Explanations**: **DROP THE STRUCTURE**. Answer naturally in paragraphs. Do not use headers like "### สรุป" if the user just asks to "explain simply".
       - **Bold** key terms.
    8. **Proactive Engagement (Important)**:
       - After the legal analysis, **always** offer to explain further in simple terms ("ภาษาชาวบ้าน") or expand on specific points.
       - Example closing: "หากท่านต้องการให้ดิฉันอธิบายหลักกฎหมายนี้ในภาษาที่เข้าใจง่ายขึ้น หรือต้องการทราบรายละเอียดในประเด็นใดเพิ่มเติม สอบถามได้ทันทีค่ะ"
    
    Output Format (STRICTLY FOLLOW THESE RULES):
    
    [MODE A: RICH DOCUMENTATION]
    **Trigger:** ONLY when User asking for a "Summary", "List of Cases", "Comparison", or a "Broad Search" (e.g., "Find cases about...", "Summarize theft laws").
    **Format:**
    ### 📝 สรุปหลักกฎหมาย
    ...
    ### 🛡️ กลยุทธ์ทางคดี
    ...
    
    [MODE B: CONVERSATIONAL ADVICE]
    **Trigger:** When User asks a Specific Question, Follow-up, "How to", "How much", "What if", or "Explain".
    **Format:**
    - **NO MARKDOWN HEADERS (###)**.
    - **NO TABLES**.
    - **NO LISTS** unless necessary.
    - Write in **PARAGRAPHS**. Talk directly to the lawyer.
    - Start with the answer directly.
    - Example: "สำหรับประเด็นเรื่องค่าเสียหายนั้น จากฎีกาที่พบ ศาลมักจะกำหนดตามจริงครับ โดยดูจาก..."
    
    ---
    *Closing*
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Synthesis Error: {e}"

def chat_workflow(user_question):
    print(f"🌐 Cloud Request: {user_question}")
    
    # 1. Optimize Query
    print(f"🤖 (Agent Cloud) Refining Query...")
    optimized_query = smart_query_optimizer(user_question)
    print(f"🔹 Optimized Query: {optimized_query}")
    
    # 2. Retrieve from Vertex AI
    docs = retriever(optimized_query)
    print(f"🤖 (Agent Cloud) Found {len(docs)} docs from Vertex")
    for d in docs:
        print(f"   - Found: {d.get('id')} | PDF: {d.get('pdf_url')}")
    
    # 3. Synthesize
    print(f"🤖 (Agent Cloud) Synthesizing Answer...")
    answer = answer_synthesizer(user_question, docs)
    
    # Return structure for UI
    return {
        "answer": answer,
        "sources": [{"id": d['id'], "year": d['year'], "outcome": d['outcome'], "text": d['text']} for d in docs]
    }

def answer_synthesizer_stream(user_question, docs, history=None):
    """
    Generator function that yields chunks of the answer.
    """
    if not docs:
        yield "ไม่พบข้อมูลฎีกาที่เกี่ยวข้อง (No relevant cases found in Vertex AI)."
        return

    # Prepare Context
    context_str = ""
    for i, doc in enumerate(docs):
        context_str += f"\n[Case {i+1}] ID: {doc.get('id')} (Year: {doc.get('year')})\nOutcome: {doc.get('outcome')}\nContent: {doc.get('text')[:3000]}...\n"

    # Prepare History
    history_str = ""
    if history:
         # Format history for the prompt
         for msg in history[-6:]: # Last 3 turns
             role = "Lawyer (User)" if msg.get("role") == "user" else "Paralegal (AI)"
             history_str += f"{role}: {msg.get('content')}\n"

    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025') # Using Flash for speed/cost or Pro for quality
    
    prompt = f"""
    Role: You are a highly skilled **Thai Legal Assistant** (ผู้ช่วยทนายความ).
    User: A Lawyer (ทนายความ) who is working on a case.
    Task: Discuss with the lawyer and help them find relevant legal authorities, including **Supreme Court Opinions (Deka)**, **Legislation (Acts/Codes)**, and **Royal Gazette Announcements**.
    
    Previous Conversation:
    {history_str}
    
    Context (Retrieved Legal Documents):
    {context_str}
    
    Lawyer's Current Query: "{user_question}"
    
    Instructions:
    1. **Analyze**: Identify the key legal issues.
    2. **Synthesize**: Summarize key principles from the retrieved documents.
       - If the document is a **Deka**: Cite the Case ID (e.g., ฎีกาที่ 123/2566) and the ruling/outcome.
       - If the document is a **Law/Act/Regulation**: Cite the Section (มาตรา) and the Act Name (ชื่อกฎหมาย) clearly.
    3. **Application**: Explain how these laws or rulings apply to the user's query.
    4. **Tone**: Professional, Concise, Supportive.
    5. **Language**: Primary language is **Thai (Formal Legal)**.
       - **EXCEPTION**: If the user asks in English or requests a translation, reply in English.
    7. **Formatting (DYNAMIC)**:
       - **For Initial/Complex Legal Queries**: Use the structured format (Headers `###`, Tables).
       - **For Follow-ups / Conversational / Simple Explanations**: **DROP THE STRUCTURE**. Answer naturally in paragraphs. Do not use headers like "### สรุป" if the user just asks to "explain simply".
       - **Bold** key terms.
    
    Output Format (STRICTLY FOLLOW THESE RULES):
    
    [MODE A: RICH DOCUMENTATION]
    **Trigger:** ONLY when User asking for a "Summary", "List of Cases", "Comparison", or a "Broad Search" (e.g., "Find cases about...", "Summarize theft laws").
    **Format:**
    ### 📝 สรุปหลักกฎหมาย
    ...
    ### 🛡️ กลยุทธ์ทางคดี
    ...
    
    [MODE B: CONVERSATIONAL ADVICE]
    **Trigger:** When User asks a Specific Question, Follow-up, "How to", "How much", "What if", or "Explain".
    **Format:**
    - **NO MARKDOWN HEADERS (###)**.
    - **NO TABLES**.
    - **NO LISTS** unless necessary.
    - Write in **PARAGRAPHS**. Talk directly to the lawyer.
    - Start with the answer directly.
    - Example: "สำหรับประเด็นเรื่องค่าเสียหายนั้น จากฎีกาที่พบ ศาลมักจะกำหนดตามจริงครับ โดยดูจาก..."
    
    ---
    *Closing*
    """
    
    try:
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"⚠️ Synthesis Error: {e}"

def chat_workflow_stream(user_question, filters=None, history=None):
    # 1. Optimize Query (with History)
    optimized_query = smart_query_optimizer(user_question, history=history)
    print(f"🔹 Optimized Query: {optimized_query}")
    
    # 2. Retrieve from Vertex AI
    docs = retriever(optimized_query, filters=filters)
    print(f"🤖 (Stream) Found {len(docs)} docs")
    if docs:
        print(f"   - Sample PDF: {docs[0].get('pdf_url')}")
    
    # 3. Return (Sources, Generator)
    sources = [{"id": d['id'], "year": d['year'], "outcome": d['outcome'], "text": d['text'], "pdf_url": d.get('pdf_url')} for d in docs]
    generator = answer_synthesizer_stream(user_question, docs, history=history)
    
    return sources, generator
