# PONK Module 3 - Speech Acts Annotation Service

Flask service that receives CoNLL-U formatted text, annotates it with speech act labels using LLM, and returns annotated CoNLL-U.

## Architecture

```
POST /api/annotate
  ↓
CoNLL-U Parser → Text Extractor → LLM Client → Annotation Mapper → CoNLL-U Serializer
  ↓
Response: {"result": "annotated_conllu", "colours": {...}}
```

## Files

- `app.py` - Flask application with API endpoints
- `conllu_processor.py` - CoNLL-U parsing, text extraction, annotation mapping
- `llm_client.py` - UFAL LLM API client for speech act annotations
- `pyproject.toml` - Project configuration and dependencies

## Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Create virtual environment and install dependencies
uv venv
uv pip install flask requests
```

## Configuration

Set environment variables for LLM API:

```bash
export UFAL_LLM_ENDPOINT="http://llm-server:8080/v1/chat/completions"
export UFAL_LLM_API_KEY="your_api_key"
export UFAL_LLM_MODEL="gpt-4-turbo-preview"
```

## Running

```bash
# Run with venv python
.venv/bin/python app.py

# Or activate venv first
source .venv/bin/activate
python app.py

# Server starts on http://0.0.0.0:8000
# Accessible via quest proxy: https://quest.ms.mff.cuni.cz/ponk-app3/
```

## API Endpoints

### `POST /api/annotate`

**Request:**
```json
{
  "result": "<conllu_text>"
}
```

**Response:**
```json
{
  "result": "<annotated_conllu>",
  "colours": {
    "01_Situace": "#E8F5E9",
    "02_Kontext": "#E3F2FD",
    ...
  }
}
```

### `GET /api/health`

Health check endpoint.

## Annotation Format

Annotations are added to the MISC field (10th column) of CoNLL-U tokens:

```
PonkApp3:[SpeechActLabel]:[SpanID]=start|end
```

Example:
```conllu
3	soud	soud	NOUN	...	...	4	nsubj	_	PonkApp3:01_Situace:a1b2c3=start
4	rozhodl	rozhodnout	VERB	...	...	0	root	_	PonkApp3:01_Situace:a1b2c3=end
```

## Speech Act Labels

- `01_Situace` - Situation
- `02_Kontext` - Context
- `03_Postup` - Procedure
- `04_Proces` - Process
- `05_Podmínky` - Conditions
- `06_Doporučení` - Recommendations
- `07_Odkazy` - Links
- `08_Prameny` - References
- `09_Nezařaditelné` - Not classified

## Testing

Use the provided test script:

```bash
python test_service.py
```

Or manually with curl:

```bash
curl -X POST http://localhost:8000/api/annotate \
  -H "Content-Type: application/json" \
  -d '{"result": "# sent_id = 1\n# text = Test sentence.\n1\tTest\ttest\tNOUN\t...\t...\t2\tnsubj\t_\t_\n2\tsentence\tsentence\tNOUN\t...\t...\t0\troot\t_\tSpaceAfter=No\n3\t.\t.\tPUNCT\t...\t...\t2\tpunct\t_\t_\n"}'
```

## TODO

- [ ] Implement actual UFAL LLM API integration (currently uses mock)
- [ ] Add error handling for malformed CoNLL-U
- [ ] Add request timeout handling
- [ ] Add logging to file
- [ ] Add tests
- [ ] Consider async processing for long documents
