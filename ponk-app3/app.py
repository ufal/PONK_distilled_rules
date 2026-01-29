#!/usr/bin/env python3
"""
PONK Module 3 - Speech Acts Annotation Service
Receives CoNLL-U, annotates with speech acts, returns annotated CoNLL-U
"""
from dotenv import load_dotenv
from flask import Flask, request, jsonify, make_response
from conllu_processor import CoNLLUProcessor
from llm_client import LLMClient
import logging
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Ensure non-ASCII characters are not escaped
processor = CoNLLUProcessor()
llm_client = LLMClient()

@app.route('/')
def index():
    return jsonify({
        'service': 'PONK Module 3 - Speech Acts',
        'version': '0.1.0',
        'endpoints': ['/api/annotate', '/api/health']
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'ponk-app3'})

@app.route('/api/annotate', methods=['POST'])
def annotate():
    """
    Main endpoint: receives CoNLL-U, returns annotated CoNLL-U
    Expected JSON: {"result": "<conllu_text>"}
    Returns JSON: {"result": "<annotated_conllu>", "colours": {...}}
    """
    try:
        data = request.get_json()
        if not data or 'result' not in data:
            return jsonify({'error': 'Missing "result" field with CoNLL-U data'}), 400
        
        conllu_text = data['result']
        logger.info(f"Received CoNLL-U, length: {len(conllu_text)} chars")
        
        # Step 1: Parse CoNLL-U and extract text
        sentences, text, token_map = processor.parse_and_extract_text(conllu_text)
        logger.info(f"Extracted text, length: {len(text)} chars, {len(sentences)} sentences")
        
        # Step 2: Call LLM for annotations (character offsets)
        annotations = llm_client.get_annotations(text)
        logger.info(f"Received {len(annotations)} annotations from LLM")
        
        # Step 3: Map character offsets to tokens
        annotated_sentences = processor.map_annotations_to_tokens(
            sentences, annotations, token_map
        )
        
        # Step 4: Serialize back to CoNLL-U
        annotated_conllu = processor.serialize_conllu(annotated_sentences)
        
        # Return with color palette - use manual JSON encoding to ensure UTF-8
        data = {
            'result': annotated_conllu,
            'colours': processor.get_color_palette()
        }
        response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    debug = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=8000, debug=debug)
