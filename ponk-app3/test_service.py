#!/usr/bin/env python3
"""
Test script for ponk-app3 service
"""
import requests
import json

# Sample CoNLL-U input
SAMPLE_CONLLU = """# sent_id = 1
# text = Nejvyšší správní soud rozhodl v senátě.
1	Nejvyšší	vysoký	ADJ	AAIS1----3A----	Animacy=Inan|Case=Nom|Degree=Sup|Gender=Masc|Number=Sing|Polarity=Pos	3	amod	_	_
2	správní	správní	ADJ	AAIS1----1A----	Animacy=Inan|Case=Nom|Degree=Pos|Gender=Masc|Number=Sing|Polarity=Pos	3	amod	_	_
3	soud	soud	NOUN	NNIS1-----A----	Animacy=Inan|Case=Nom|Gender=Masc|Number=Sing|Polarity=Pos	4	nsubj	_	_
4	rozhodl	rozhodnout	VERB	VpYS----R-AAP-1	Aspect=Perf|Gender=Masc|Number=Sing|Polarity=Pos|Tense=Past|VerbForm=Part|Voice=Act	0	root	_	_
5	v	v	ADP	RR--6----------	AdpType=Prep|Case=Loc	6	case	_	_
6	senátě	senát	NOUN	NNIS6-----A----	Animacy=Inan|Case=Loc|Gender=Masc|Number=Sing|Polarity=Pos	4	obl	_	SpaceAfter=No
7	.	.	PUNCT	Z:-------------	_	4	punct	_	_

# sent_id = 2
# text = Certifikát není rozhodnutím.
1	Certifikát	certifikát	NOUN	NNIS1-----A----	Animacy=Inan|Case=Nom|Gender=Masc|Number=Sing|Polarity=Pos	3	nsubj	_	_
2	není	být	AUX	VB-S---3P-NAI--	Mood=Ind|Number=Sing|Person=3|Polarity=Neg|Tense=Pres|VerbForm=Fin|Voice=Act	3	cop	_	_
3	rozhodnutím	rozhodnutí	NOUN	NNNS7-----A----	Case=Ins|Gender=Neut|Number=Sing|Polarity=Pos|VerbForm=Vnoun	0	root	_	SpaceAfter=No
4	.	.	PUNCT	Z:-------------	_	3	punct	_	_
"""

def test_health():
    """Test health endpoint"""
    print("Testing /api/health...")
    response = requests.get('http://localhost:8000/api/health')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_annotate():
    """Test annotation endpoint"""
    print("Testing /api/annotate...")
    
    payload = {
        "result": SAMPLE_CONLLU
    }
    
    response = requests.post(
        'http://localhost:8000/api/annotate',
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n=== Annotated CoNLL-U ===")
        print(data['result'])
        print("\n=== Color Palette ===")
        print(json.dumps(data['colours'], indent=2))
    else:
        print(f"Error: {response.text}")
    print()

if __name__ == '__main__':
    print("=" * 60)
    print("PONK-APP3 Service Test")
    print("=" * 60)
    print()
    
    try:
        test_health()
        test_annotate()
        print("✅ All tests completed")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to service. Is it running on port 8000?")
    except Exception as e:
        print(f"❌ Error: {e}")
