# LLM Annotation Experiment

Automated annotation of legal documents using OpenAI API with speech acts categories.

## Structure

```
experiment_01/
├── input_data/              # Input documents (document_01.md, document_02.md)
├── prompts/                 # Generated prompts for each document
├── responses/               # API responses with annotations
├── speech_acts.md           # Speech acts category definitions
├── payload_template.md      # Prompt template with instructions and speech acts
├── prompt_template.json     # API configuration (model, temperature, etc.)
├── pyproject.toml           # uv project configuration
├── generate_prompts.py      # Script to generate prompts from template
└── run_annotations.py       # Script to call OpenAI API
```

## Setup

Install dependencies using `uv`:

```bash
cd experiment_01
uv sync
```

This will install all required dependencies (OpenAI SDK, etc.) in a virtual environment.

## Workflow

### 1. Generate Prompts

```bash
uv run python generate_prompts.py
```

This reads each document from `input_data/`, combines it with the prompt template from `payload_template.md`, and creates structured JSON files in `prompts/`.

Each generated prompt includes:
- Complete speech acts definitions (9 categories)
- Annotation instructions
- Expected JSON output format
- Full document text

### 2. Run Annotations

Make sure your API key is set:
```bash
export OPENAI_UFAL_API_KEY="your-api-key-here"
```

Then run:
```bash
uv run python run_annotations.py
```

This sends each prompt to OpenAI API and saves responses in `responses/`.

## Output Format

Each response file contains:
- `source_document`: Original document filename
- `model`: Model used
- `usage`: Token usage statistics (prompt, completion, total)
- `annotations`: Parsed JSON array of annotations with `start`, `end`, and `label`
- `content`: Raw response from API
- `finish_reason`: Completion status

## Configuration

Edit `prompt_template.json` to adjust:
- `model`: GPT model to use (default: gpt-4-turbo-preview)
- `temperature`: 0-1 (default: 0.2 for consistency)
- `max_tokens`: Maximum response length (default: 4096)
- `response_format`: Force JSON output (default: enabled)
- `prompt_template_file`: Template file to use (default: payload_template.md)
