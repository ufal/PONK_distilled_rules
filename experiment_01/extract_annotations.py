#!/usr/bin/env python3

import json
from pathlib import Path

def extract_annotations(responses_dir, output_dir):
    """
    Extract annotations from API responses and save as clean JSON files.
    
    Args:
        responses_dir: Directory containing response JSON files
        output_dir: Directory to save extracted annotations
    """
    responses_path = Path(responses_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    response_files = sorted(responses_path.glob('response_*.json'))
    
    if not response_files:
        print(f"No response files found in {responses_dir}")
        return
    
    print(f"Found {len(response_files)} response file(s) to process\n")
    
    for response_file in response_files:
        print(f"Processing {response_file.name}...")
        
        with open(response_file, 'r', encoding='utf-8') as f:
            response_data = json.load(f)
        
        annotations = None
        
        if 'annotations' in response_data and response_data['annotations']:
            annotations = response_data['annotations']
            print(f"  → Found parsed annotations: {len(annotations)} annotation(s)")
        elif 'content' in response_data:
            try:
                annotations = json.loads(response_data['content'])
                print(f"  → Extracted from content field: {len(annotations) if isinstance(annotations, list) else 'object'}")
            except json.JSONDecodeError as e:
                print(f"  ✗ Error: Content is not valid JSON - {e}")
                
                output_file = output_path / f"error_{response_file.stem.replace('response_', '')}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response_data['content'])
                print(f"  → Saved raw content to {output_file.name}")
                continue
        else:
            print(f"  ✗ Error: No annotations or content field found")
            continue
        
        if annotations:
            if isinstance(annotations, dict) and 'annotations' in annotations:
                annotations = annotations['annotations']
            elif not isinstance(annotations, list):
                annotations = [annotations]
            
            output_file = output_path / f"{response_file.stem.replace('response_', '')}.json"
            
            output_data = {
                'source_document': response_data.get('source_document'),
                'model': response_data.get('model'),
                'total_tokens': response_data.get('usage', {}).get('total_tokens'),
                'finish_reason': response_data.get('finish_reason'),
                'annotations': annotations
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            annotation_count = len(output_data['annotations'])
            print(f"  ✓ Saved {annotation_count} annotation(s) to {output_file.name}")
        else:
            print(f"  ⚠ Warning: No annotations extracted")
    
    print(f"\n✓ Completed processing {len(response_files)} response file(s)")
    print(f"✓ Annotations saved in {output_dir}")

if __name__ == '__main__':
    script_dir = Path(__file__).parent
    
    extract_annotations(
        responses_dir=script_dir / 'responses',
        output_dir=script_dir / 'annotations'
    )
