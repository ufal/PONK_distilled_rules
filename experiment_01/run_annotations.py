#!/usr/bin/env python3

import json
import os
import time
from pathlib import Path
from openai import OpenAI

def run_annotations(prompts_dir, output_dir):
    """
    Send prompts to OpenAI API and save responses.
    
    Args:
        prompts_dir: Directory containing prompt JSON files
        output_dir: Directory to save API responses
    """
    prompts_path = Path(prompts_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    prompt_files = sorted(prompts_path.glob('prompt_*.json'))
    
    if not prompt_files:
        print(f"No prompt files found in {prompts_dir}")
        return
    
    print(f"Found {len(prompt_files)} prompt(s) to process\n")
    
    for prompt_file in prompt_files:
        print(f"Processing {prompt_file.name}...")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
        
        api_key_env = prompt_data.get('api_key_env', 'OPENAI_UFAL_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            print(f"  ✗ Error: Environment variable {api_key_env} not set")
            continue
        
        client = OpenAI(api_key=api_key)
        
        try:
            messages = []
            
            if prompt_data.get('system_message'):
                messages.append({
                    'role': 'system',
                    'content': prompt_data['system_message']
                })
            
            messages.append({
                'role': 'user',
                'content': prompt_data['user_message']
            })
            
            api_params = {
                'model': prompt_data['model'],
                'messages': messages,
                'temperature': prompt_data['temperature'],
                'max_tokens': prompt_data['max_tokens']
            }
            
            if prompt_data.get('response_format'):
                api_params['response_format'] = prompt_data['response_format']
            
            print(f"  → Calling OpenAI API ({prompt_data['model']})...")
            
            response = client.chat.completions.create(**api_params)
            
            response_data = {
                'source_document': prompt_data.get('source_document'),
                'model': response.model,
                'created': response.created,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'content': response.choices[0].message.content,
                'finish_reason': response.choices[0].finish_reason
            }
            
            try:
                response_data['annotations'] = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                print(f"  ⚠ Warning: Response is not valid JSON")
            
            output_file = output_path / f"response_{prompt_file.stem.replace('prompt_', '')}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ Saved to {output_file.name}")
            print(f"  ✓ Tokens used: {response.usage.total_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            
            error_data = {
                'source_document': prompt_data.get('source_document'),
                'error': str(e),
                'prompt_file': prompt_file.name
            }
            
            error_file = output_path / f"error_{prompt_file.stem.replace('prompt_', '')}.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Completed processing {len(prompt_files)} prompt(s)")
    print(f"✓ Responses saved in {output_dir}")

if __name__ == '__main__':
    script_dir = Path(__file__).parent
    
    run_annotations(
        prompts_dir=script_dir / 'prompts',
        output_dir=script_dir / 'responses'
    )
