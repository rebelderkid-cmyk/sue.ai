import os
import json
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from rag_core import chat_workflow, chat_workflow_stream

app = Flask(__name__)
# Enable CORS for all domains (or restrict to sue-ai.vercel.app in production)
CORS(app)

@app.route('/')
def index():
    return "Sue.AI Cloud API is Running! 🚀 (Use POST /api/chat)"

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        question = data.get('question', '')
        filters = data.get('filters', None) # Extract filters
        history = data.get('history', [])  # Extract history (default empty)

        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        # Use Streaming Workflow
        sources, generator = chat_workflow_stream(question, filters=filters, history=history)
        
        def generate():
            # 1. Send Answer Chunks
            for chunk in generator:
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk}, ensure_ascii=False)}\n\n"
            
            # 2. Send Sources (After generation logic)
            yield f"data: {json.dumps({'type': 'sources', 'data': sources}, ensure_ascii=False)}\n\n"
            
            # 3. Done Signal
            yield "data: [DONE]\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Cloud Run injects PORT environment variable
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Sue.AI Cloud Server starting on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
