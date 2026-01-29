# Local Testing Pipeline

This directory contains tools for testing the ponk-app3 speech acts annotation service locally.

## Prerequisites

1. **ponk-app3 service running locally:**
   ```bash
   cd ../ponk-app3
   source .venv/bin/activate
   python app.py
   ```
   The service should be running on `http://localhost:8000`

2. **Python 3 with requests library:**
   ```bash
   pip install requests
   ```

## Usage

### Run the pipeline

```bash
python annotate_pipeline.py <input_file.txt>
```

This will:
1. Read raw Czech text from the input file
2. Convert to CoNLL-U format using UDPipe REST API
3. Send to local ponk-app3 for annotation
4. Save human-readable results to `<input_file>_out.txt`

### Example

```bash
python annotate_pipeline.py sample_input.txt
```

Output will be saved to `sample_input_out.txt` with:
- Sentence-by-sentence breakdown
- Inline speech act annotations
- Summary of all detected speech acts

### Input Format

Input files should contain raw Czech text in UTF-8 encoding. The text will be automatically:
- Tokenized by UDPipe
- Parsed into CoNLL-U format
- Annotated with speech acts by the LLM

### Output Format

The output file contains:
- Each sentence with its text
- Annotations showing which tokens belong to which speech acts
- Position markers (start/end) for annotation spans
- Summary table of all speech act categories found

### Speech Act Categories

- **01_Situace** - Situation descriptions
- **02_Kontext** - Contextual information
- **03_Postup** - Procedures and steps
- **04_Proces** - Process descriptions
- **05_Podmínky** - Conditions and options
- **06_Doporučení** - Recommendations
- **07_Odkazy** - Links to other documents
- **08_Prameny** - Legal references
- **09_Nezařaditelné** - Unclassified text

## Troubleshooting

**Connection refused:**
- Make sure ponk-app3 is running on port 8000
- Check: `curl http://localhost:8000/api/health`

**UDPipe timeout:**
- The UDPipe API may be slow for very long texts
- Try breaking long documents into smaller chunks

**No annotations returned:**
- Check ponk-app3 logs for errors
- Verify API key is set in `../ponk-app3/.env`
- Look for `WARNING: AIUFAL_API_KEY not set` in logs
