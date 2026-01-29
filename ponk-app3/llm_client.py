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
    
    UFAL_API_ENDPOINT = "https://ai.ufal.mff.cuni.cz/api/chat/completions"
    DEFAULT_MODEL = "LLM3-AMD-MI210.gpt-oss:120b"
    
    SYSTEM_MESSAGE = """You are an expert legal document annotator. Your task is to analyze Czech legal documents and provide structured JSON annotations. Always respond with valid JSON only, no additional text."""
    
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
5. **Spans must NOT overlap** - each character position belongs to at most one annotation
6. Every part of the document should ideally be covered by at least one annotation

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
- "start": character offset where the span begins (inclusive, 0-indexed)
- "end": character offset where the span ends (exclusive)
- "label": one of the speech act labels (01_Situace, 02_Kontext, etc.)

**IMPORTANT: Spans must NOT overlap.** Each character position should belong to at most one annotation. If text could fit multiple categories, choose the most specific one.

## Document to Annotate

{text}
"""
    
    def __init__(self):
        self.api_endpoint = os.getenv('AIUFAL_ENDPOINT', self.UFAL_API_ENDPOINT)
        self.api_key = os.getenv('AIUFAL_API_KEY', '')
        self.model = os.getenv('AIUFAL_MODEL', self.DEFAULT_MODEL)
        self.use_mock = os.getenv('AIUFAL_USE_MOCK', '').lower() in ('1', 'true', 'yes')
        
    def get_annotations(self, text: str) -> List[Dict]:
        """
        Call LLM to get speech act annotations for text
        
        Args:
            text: Raw text to annotate
            
        Returns:
            List of annotations: [{"start": int, "end": int, "label": str}, ...]
        """
        if self.use_mock or not self.api_key:
            if self.use_mock:
                logger.info("AIUFAL_USE_MOCK enabled - using mock LLM response")
            else:
                logger.warning("AIUFAL_API_KEY not set - using mock LLM response")
            return self._mock_annotations(text)
        
        return self._call_llm_api(text)
    
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
    
    def _call_llm_api(self, text: str) -> List[Dict]:
        """
        Make actual API call to UFAL LLM
        
        Returns:
            List of annotations: [{"start": int, "end": int, "label": str}, ...]
        """
        import requests
        
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "max_tokens": 8192,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self.SYSTEM_MESSAGE},
                {"role": "user", "content": self.USER_MESSAGE_TEMPLATE.format(text=text)}
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        logger.info(f"Calling UFAL LLM API ({self.model}) for {len(text)} chars...")
        
        try:
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers=headers,
                timeout=600  # 10 min timeout for long documents
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parse JSON response - handle both raw and markdown-wrapped JSON
            content = content.strip()
            if content.startswith('```'):
                # Remove markdown code block wrapper
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1]) if lines[-1].startswith('```') else '\n'.join(lines[1:])
            
            annotations_data = json.loads(content)
            
            # Handle both {"annotations": [...]} and direct [...] format
            if isinstance(annotations_data, list):
                annotations = annotations_data
            else:
                annotations = annotations_data.get('annotations', [])
            
            logger.info(f"LLM returned {len(annotations)} annotations")
            return annotations
            
        except requests.exceptions.Timeout:
            logger.error("LLM API call timed out after 600 seconds")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"LLM API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw content: {content[:500]}...")
            raise
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
