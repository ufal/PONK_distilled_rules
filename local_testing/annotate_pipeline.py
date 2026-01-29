#!/usr/bin/env python3
"""
Local testing pipeline for PONK Module 3 Speech Acts Annotation

Usage:
    python annotate_pipeline.py input_text.txt

This script will:
1. Read raw Czech text from the input file
2. Convert to CoNLL-U format using UDPipe REST API
3. Call the local ponk-app3 annotation service
4. Save human-readable annotated output to input_text_out.txt
"""

import sys
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple


UDPIPE_API = "https://lindat.mff.cuni.cz/services/udpipe/api/process"
UDPIPE_MODEL = "czech-pdt-ud-2.12-230717"
PONK_APP3_URL = "http://localhost:8000/api/annotate"

SPEECH_ACT_LABELS = {
    "01_Situace": "Situation",
    "02_Kontext": "Context",
    "03_Postup": "Procedure",
    "04_Proces": "Process",
    "05_Podmínky": "Conditions",
    "06_Doporučení": "Recommendations",
    "07_Odkazy": "Links",
    "08_Prameny": "References",
    "09_Nezařaditelné": "Unclassified",
}


def read_text_file(file_path: Path) -> str:
    """Read raw text from input file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def convert_to_conllu(text: str) -> str:
    """Convert raw text to CoNLL-U format using UDPipe API."""
    print(f"Converting text to CoNLL-U using UDPipe ({len(text)} chars)...")
    
    response = requests.post(
        UDPIPE_API,
        data={
            'data': text,
            'model': UDPIPE_MODEL,
            'tokenizer': '',
            'tagger': '',
            'parser': '',
        },
        timeout=60
    )
    response.raise_for_status()
    
    result = response.json()
    conllu = result.get('result', '')
    
    if not conllu:
        raise ValueError("UDPipe returned empty result")
    
    print(f"✓ Converted to CoNLL-U")
    return conllu


def annotate_conllu(conllu: str) -> Dict:
    """Call ponk-app3 API to annotate CoNLL-U."""
    print(f"Calling ponk-app3 annotation service...")
    
    response = requests.post(
        PONK_APP3_URL,
        json={'result': conllu},
        headers={'Content-Type': 'application/json'},
        timeout=180
    )
    response.raise_for_status()
    
    result = response.json()
    print(f"✓ Received annotated response")
    return result


def parse_conllu_with_annotations(conllu: str) -> List[Dict]:
    """Parse CoNLL-U and extract sentences with annotations."""
    sentences = []
    current_sentence = {
        'text': '',
        'tokens': [],
        'annotations': []
    }
    
    for line in conllu.split('\n'):
        line = line.strip()
        
        if not line:
            if current_sentence['tokens']:
                sentences.append(current_sentence)
                current_sentence = {
                    'text': '',
                    'tokens': [],
                    'annotations': []
                }
            continue
        
        if line.startswith('# text ='):
            current_sentence['text'] = line[8:].strip()
            continue
        
        if line.startswith('#'):
            continue
        
        fields = line.split('\t')
        if len(fields) == 10:
            token = {
                'id': fields[0],
                'form': fields[1],
                'misc': fields[9]
            }
            current_sentence['tokens'].append(token)
            
            # Parse PonkApp3 annotations from MISC field
            if 'PonkApp3:' in fields[9]:
                parts = fields[9].split('PonkApp3:')[1]
                # Format: Label:SpanId=start/end
                if '=' in parts:
                    label_span, position = parts.split('=')
                    label, span_id = label_span.split(':')
                    
                    current_sentence['annotations'].append({
                        'token_id': fields[0],
                        'form': fields[1],
                        'label': label,
                        'span_id': span_id,
                        'position': position
                    })
    
    if current_sentence['tokens']:
        sentences.append(current_sentence)
    
    return sentences


def format_human_readable(sentences: List[Dict]) -> str:
    """Format annotated sentences in human-readable format."""
    output = []
    output.append("=" * 80)
    output.append("PONK Module 3 - Speech Acts Annotation Results")
    output.append("=" * 80)
    output.append("")
    
    # Group annotations by span_id across all sentences
    all_spans = {}
    for sent_idx, sent in enumerate(sentences):
        for ann in sent['annotations']:
            span_id = ann['span_id']
            if span_id not in all_spans:
                all_spans[span_id] = {
                    'label': ann['label'],
                    'tokens': [],
                    'sentences': set()
                }
            all_spans[span_id]['tokens'].append((sent_idx, ann['token_id'], ann['form']))
            all_spans[span_id]['sentences'].add(sent_idx)
    
    # Output sentences with inline annotations
    for sent_idx, sent in enumerate(sentences):
        output.append(f"Sentence {sent_idx + 1}:")
        output.append(f"  {sent['text']}")
        output.append("")
        
        if sent['annotations']:
            output.append("  Annotations:")
            
            # Group by span within sentence
            spans_in_sent = {}
            for ann in sent['annotations']:
                span_id = ann['span_id']
                if span_id not in spans_in_sent:
                    spans_in_sent[span_id] = {
                        'label': ann['label'],
                        'positions': []
                    }
                spans_in_sent[span_id]['positions'].append(f"{ann['form']} ({ann['position']})")
            
            for span_id, span_info in spans_in_sent.items():
                label = span_info['label']
                label_name = SPEECH_ACT_LABELS.get(label, label)
                positions = ", ".join(span_info['positions'])
                output.append(f"    [{label_name}] {positions}")
            
            output.append("")
    
    output.append("=" * 80)
    output.append("Summary of Speech Acts")
    output.append("=" * 80)
    output.append("")
    
    # Summary by label
    label_counts = {}
    for span_id, span_info in all_spans.items():
        label = span_info['label']
        if label not in label_counts:
            label_counts[label] = 0
        label_counts[label] += 1
    
    for label in sorted(label_counts.keys()):
        label_name = SPEECH_ACT_LABELS.get(label, label)
        count = label_counts[label]
        output.append(f"  {label_name} ({label}): {count} span(s)")
    
    output.append("")
    return '\n'.join(output)


def main():
    if len(sys.argv) != 2:
        print("Usage: python annotate_pipeline.py <input_file.txt>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
    
    # Generate output filename
    output_path = input_path.parent / f"{input_path.stem}_out.txt"
    
    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print()
    
    try:
        # Step 1: Read input text
        text = read_text_file(input_path)
        print(f"✓ Read input text ({len(text)} chars)")
        
        # Step 2: Convert to CoNLL-U
        conllu = convert_to_conllu(text)
        
        # Step 3: Annotate with ponk-app3
        result = annotate_conllu(conllu)
        annotated_conllu = result.get('result', '')
        
        if not annotated_conllu:
            raise ValueError("ponk-app3 returned empty result")
        
        # Step 4: Parse and format output
        print("Formatting output...")
        sentences = parse_conllu_with_annotations(annotated_conllu)
        output = format_human_readable(sentences)
        
        # Step 5: Save output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        print(f"✓ Saved human-readable output to {output_path}")
        print()
        print("Done!")
        
    except requests.RequestException as e:
        print(f"Error: Request failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
