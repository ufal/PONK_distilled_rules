# Task: Annotate Legal Document with Speech Acts

You are an expert annotator tasked with identifying and labeling text spans in a legal advice document according to a predefined set of speech act categories. Your goal is to segment the document into meaningful spans and assign each span the most appropriate speech act label.

## Speech Acts Definitions

### 01_Situace (Situation)
Snippets of text indicating what situation (and goal) the advice applies to.

### 02_Kontext (Context)
Snippets of text giving the broader picture, for instance precedent cases or typical procedures and their outcomes.

### 03_Postup (Procedure)
Snippets of text describing what the recipient is advised to do.

### 04_Proces (Process)
Snippets of text describing the expected responses of authorities or other parties to steps taken by the recipient.

### 05_Podmínky (Conditions, options)
Snippets of text specifying circumstances under which an action can or cannot be taken.

### 06_Doporučení (Recommendations)
Snippets of text that recommend additional actions or compare the individual options with respect to their desired impact.

### 07_Odkazy (Links)
Explicit textual links to other documents in Frank Bold's knowledge base of legal advice.

### 08_Prameny (References)
References to external documents, particularly laws and regulations.

### 09_Nezařaditelné (Not classified)
Any other text.

## Instructions

1. Read through the entire document carefully
2. Identify meaningful text spans that correspond to one of the speech act categories above
3. Spans can be of any length (words, sentences, paragraphs) - prefer smaller, more granular spans over large sections
4. **Each category can and should be used multiple times throughout the document** - do not try to use each category only once
5. Spans may overlap if a text segment serves multiple functions
6. Every part of the document should be covered by at least one annotation
7. For each span, determine the character positions (start and end indices)
8. Assign the most appropriate label from the categories above
9. Create as many annotations as needed to accurately represent the document structure - typically dozens of annotations per document

## Output Format

Return your annotations as a JSON array. Each annotation should be an object with:
- `start`: Integer (character position where the span begins, 0-indexed)
- `end`: Integer (character position where the span ends, exclusive)
- `label`: String (one of the 9 categories: "01_Situace", "02_Kontext", "03_Postup", "04_Proces", "05_Podmínky", "06_Doporučení", "07_Odkazy", "08_Prameny", "09_Nezařaditelné")

Example output format:
```json
[
  {
    "start": 0,
    "end": 45,
    "label": "01_Situace"
  },
  {
    "start": 46,
    "end": 120,
    "label": "03_Postup"
  }
]
```

## Document to Annotate

{DOCUMENT_TEXT}
