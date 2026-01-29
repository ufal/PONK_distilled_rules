#!/usr/bin/env python3
"""List available models from UFAL LLM API."""

import os
import sys
import requests
from pathlib import Path

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
    print("Set it via environment variable or in ../ponk-app3/.env")
    sys.exit(1)

print(f"Endpoint: {ENDPOINT}")
print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
print()

try:
    response = requests.get(
        f"{ENDPOINT}/models",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    
    print("Available models:")
    print("-" * 60)
    
    if "data" in data:
        models = data["data"]
        for model in sorted(models, key=lambda m: m.get("id", "")):
            model_id = model.get("id", "unknown")
            owned_by = model.get("owned_by", "")
            print(f"  {model_id}")
            if owned_by:
                print(f"    owned_by: {owned_by}")
    else:
        # Maybe it's a simple list
        print(data)
        
except requests.RequestException as e:
    print(f"Error: {e}")
    sys.exit(1)
