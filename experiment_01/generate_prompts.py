#!/usr/bin/env python3

import json
import os
from pathlib import Path

def generate_prompts(input_dir, prompt_template_file, config_file, output_dir):
    """
    Generate prompts for each input document using the template.
    
    Args:
        input_dir: Directory containing input documents
        prompt_template_file: Path to prompt.md template
        config_file: Path to prompt_template.json config
        output_dir: Directory to save generated prompts
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(prompt_template_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    placeholder = config.get('placeholder', '{DOCUMENT_TEXT}')
    
    input_files = sorted(input_path.glob('*.md'))
    
    if not input_files:
        print(f"No .md files found in {input_dir}")
        return
    
    for doc_file in input_files:
        print(f"Processing {doc_file.name}...")
        
        with open(doc_file, 'r', encoding='utf-8') as f:
            document_text = f.read().strip().strip("'\"")
        
        prompt_content = prompt_template.replace(placeholder, document_text)
        
        prompt_data = {
            'model': config.get('model'),
            'temperature': config.get('temperature'),
            'max_tokens': config.get('max_tokens'),
            'response_format': config.get('response_format'),
            'system_message': config.get('system_message'),
            'user_message': prompt_content,
            'source_document': doc_file.name,
            'api_key_env': config.get('api_key_env')
        }
        
        output_file = output_path / f"prompt_{doc_file.stem}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, indent=2, ensure_ascii=False)
        
        print(f"  → Saved to {output_file.name}")
    
    print(f"\nGenerated {len(input_files)} prompts in {output_dir}")

if __name__ == '__main__':
    script_dir = Path(__file__).parent
    config_file = script_dir / 'prompt_template.json'
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    prompt_template_file = script_dir / config.get('prompt_template_file', 'payload_template.md')
    
    generate_prompts(
        input_dir=script_dir / 'input_data',
        prompt_template_file=prompt_template_file,
        config_file=config_file,
        output_dir=script_dir / 'prompts'
    )
