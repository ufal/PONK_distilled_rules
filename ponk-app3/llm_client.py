"""
LLM client for speech act annotation
"""
import os
import json
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for UFAL LLM API to get speech act annotations"""
    
    SYSTEM_MESSAGE = """You are an expert legal document annotator. Your task is to analyze documents and provide structured JSON annotations. Always respond with valid JSON only, no additional text."""
    
    USER_MESSAGE_TEMPLATE = """# Task: Annotate Legal Document with Speech Acts

You are an expert annotator tasked with identifying and labeling text spans in a legal advice document according to a predefined set of speech act categories. Your goal is to segment the document into meaningful spans and assign each span the most appropriate speech act label.

## Speech Acts Definitions

### 01_Situace (Situation)
Snippets of text indicating what situation (and goal) the advice applies to.

### 02_Kontext (Context)
Snippets of text giving the broader picture, for instance precedent cases or typical procedures and their outcomes.

### 03_Postup (Procedure)
Snippets of text describing what the recipient is advised to do.

### 04_Proces (Process)
Snippets of text describing the expected responses of authorities or other parties to steps taken by the recipient.

### 05_Podmínky (Conditions, options)
Snippets of text specifying circumstances under which an action can or cannot be taken.

### 06_Doporučení (Recommendations)
Snippets of text that recommend additional actions or compare the individual options with respect to their desired impact.

### 07_Odkazy (Links)
Explicit textual links to other documents in Frank Bold's knowledge base of legal advice.

### 08_Prameny (References)
References to external documents, particularly laws and regulations.

### 09_Nezařaditelné (Not classified)
Any other text.

## Instructions

1. Read through the entire document carefully
2. Identify meaningful text spans that correspond to one of the speech act categories above
3. Spans can be of any length (words, sentences, paragraphs) - prefer smaller, more granular spans over large sections
4. **Each category can and should be used multiple times throughout the document** - do not try to use each category only once
5. Spans may overlap if a text segment serves multiple functions
6. Every part of the document should be covered by at least one annotation

## Output Format

Return a JSON object with this structure:
{{
  "annotations": [
    {{
      "start": 0,
      "end": 100,
      "label": "01_Situace"
    }},
    ...
  ]
}}

Where:
- "start": character offset where the span begins (inclusive)
- "end": character offset where the span ends (exclusive)
- "label": one of the speech act labels (01_Situace, 02_Kontext, etc.)

## Document to Annotate

{text}
"""
    
    def __init__(self):
        self.api_endpoint = os.getenv('UFAL_LLM_ENDPOINT', 'http://localhost:8080/v1/chat/completions')
        self.api_key = os.getenv('UFAL_LLM_API_KEY', '')
        self.model = os.getenv('UFAL_LLM_MODEL', 'gpt-4-turbo-preview')
        
    def get_annotations(self, text: str) -> List[Dict]:
        """
        Call LLM to get speech act annotations for text
        
        Args:
            text: Raw text to annotate
            
        Returns:
            List of annotations: [{"start": int, "end": int, "label": str}, ...]
        """
        # TODO: Implement actual LLM API call
        # For now, return mock annotations for testing
        logger.warning("Using mock LLM response - implement actual API call")
        
        return self._mock_annotations(text)
    
    def _mock_annotations(self, text: str) -> List[Dict]:
        """Generate mock annotations for testing"""
        # Simple heuristic: annotate first 30% as Situace, rest as Postup
        text_len = len(text)
        
        return [
            {
                "start": 0,
                "end": min(int(text_len * 0.3), text_len),
                "label": "01_Situace"
            },
            {
                "start": min(int(text_len * 0.3), text_len),
                "end": text_len,
                "label": "03_Postup"
            }
        ]
    
    def _call_llm_api(self, text: str) -> Dict:
        """
        Make actual API call to UFAL LLM
        
        To implement:
        1. Format request with system message and user prompt
        2. Make HTTP POST to self.api_endpoint
        3. Parse JSON response
        4. Extract annotations from response
        """
        import requests
        
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self.SYSTEM_MESSAGE},
                {"role": "user", "content": self.USER_MESSAGE_TEMPLATE.format(text=text)}
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers=headers,
                timeout=300  # 5 min timeout
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            annotations_data = json.loads(content)
            
            return annotations_data['annotations']
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
