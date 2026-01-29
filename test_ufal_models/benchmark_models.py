#!/usr/bin/env python3
"""Benchmark UFAL LLM models for speech act annotation task."""

import os
import sys
import time
import json
import requests
from pathlib import Path
from typing import List, Optional

# Load .env from ponk-app3 if available
env_file = Path(__file__).parent.parent / "ponk-app3" / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

API_KEY = os.getenv("AIUFAL_API_KEY")
ENDPOINT = os.getenv("AIUFAL_ENDPOINT", "https://ai.ufal.mff.cuni.cz/api")

if not API_KEY:
    print("Error: AIUFAL_API_KEY not set")
    sys.exit(1)

# Czech legal text example
TEST_TEXT = """Pokud jste obdrželi výzvu k zaplacení pokuty za přestupek, měli byste nejprve ověřit, zda je výzva oprávněná. Zkontrolujte datum, místo a popis přestupku. Máte právo podat odpor do 8 dnů od doručení. V odporu uveďte důvody, proč s pokutou nesouhlasíte. Pokud odpor nepodáte včas, pokuta nabude právní moci."""

SYSTEM_PROMPT = """Jste expertní právní anotátor. Analyzujte následující text a identifikujte řečové akty.

Kategorie:
- 01_Situace: Popis výchozí situace
- 02_Kontext: Dodatečné informace
- 03_Postup: Kroky k provedení
- 04_Proces: Popis procesu
- 05_Podmínky: Podmínky a omezení
- 06_Doporučení: Rady a doporučení
- 07_Odkazy: Reference na jiné zdroje
- 08_Prameny: Právní prameny
- 09_Nezařaditelné: Nelze zařadit

Vraťte JSON pole s anotacemi ve formátu:
[{"start": int, "end": int, "label": "kategorie"}]

Pozice jsou znakové offsety od začátku textu."""

# Models to test (from list_models.py output)
# Excluding non-chat models: openwebuidocs, rag-test, rag-test-2
DEFAULT_MODELS = [
    "Apertus-70B-8b_4x3090.RedHatAI/Apertus-70B-Instruct-2509-FP8-dynamic",
    "LLM2-A30.hf.co/bartowski/Qwen2.5-Coder-32B-Instruct-GGUF:Q4_0",
    "LLM3-AMD-MI210.deepseek-r1:70b",
    "LLM3-AMD-MI210.gpt-oss:120b",
    "LLM3-AMD-MI210.llama3.3:latest",
    "LLM5-RTX5000.deepseek-r1:8b",
    "LLM6-2xRTX5000.gemma3:12b-it-qat",
    "Qwen/Qwen2.5-Omni-7B-GPTQ-Int4",
    "VLLM-llm-server2.swiss-ai/Apertus-8B-Instruct-2509",
    "utter-project/EuroLLM-22B-Instruct-2512",
]


def call_model(model: str, text: str, timeout: int = 180) -> dict:
    """Call a model and return timing + response info."""
    result = {
        "model": model,
        "success": False,
        "time_seconds": None,
        "error": None,
        "annotations_count": None,
        "response_preview": None,
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }
    
    start = time.time()
    try:
        response = requests.post(
            f"{ENDPOINT}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        elapsed = time.time() - start
        result["time_seconds"] = round(elapsed, 2)
        
        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
            return result
        
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        result["response_preview"] = content[:200]
        
        # Try to parse annotations
        try:
            # Find JSON array in response
            start_idx = content.find("[")
            end_idx = content.rfind("]") + 1
            if start_idx >= 0 and end_idx > start_idx:
                annotations = json.loads(content[start_idx:end_idx])
                result["annotations_count"] = len(annotations)
                result["success"] = True
        except json.JSONDecodeError:
            result["error"] = "Failed to parse JSON from response"
            
    except requests.Timeout:
        result["time_seconds"] = timeout
        result["error"] = f"Timeout after {timeout}s"
    except requests.RequestException as e:
        result["time_seconds"] = round(time.time() - start, 2)
        result["error"] = str(e)
    
    return result


def main(models: Optional[List[str]] = None):
    """Run benchmark on specified models."""
    if models is None:
        models = DEFAULT_MODELS
    
    print("=" * 70)
    print("UFAL LLM Model Benchmark - Speech Act Annotation")
    print("=" * 70)
    print(f"Endpoint: {ENDPOINT}")
    print(f"Test text: {len(TEST_TEXT)} chars")
    print(f"Models to test: {len(models)}")
    print()
    
    results = []
    for model in models:
        print(f"Testing: {model}")
        print("-" * 50)
        
        result = call_model(model, TEST_TEXT)
        results.append(result)
        
        if result["success"]:
            print(f"  ✓ Success in {result['time_seconds']}s")
            print(f"    Annotations: {result['annotations_count']}")
        else:
            print(f"  ✗ Failed after {result['time_seconds']}s")
            print(f"    Error: {result['error']}")
        
        if result["response_preview"]:
            preview = result["response_preview"].replace("\n", " ")[:100]
            print(f"    Preview: {preview}...")
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Model':<45} {'Time':>8} {'Status':>10}")
    print("-" * 70)
    for r in sorted(results, key=lambda x: x["time_seconds"] or 999):
        status = f"{r['annotations_count']} ann." if r["success"] else "FAILED"
        time_str = f"{r['time_seconds']}s" if r["time_seconds"] else "N/A"
        print(f"{r['model']:<45} {time_str:>8} {status:>10}")


if __name__ == "__main__":
    # Accept model names as command line arguments
    if len(sys.argv) > 1:
        models = sys.argv[1:]
    else:
        models = DEFAULT_MODELS
    
    main(models)
