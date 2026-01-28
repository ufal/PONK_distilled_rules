# LLM Annotation Evaluation Report

**Experiment:** experiment_01  
**Date:** 2026-01-26  
**Model:** gpt-4-0125-preview  

---

## 1. Methodology

### 1.1 Evaluation Approach

We evaluated LLM-generated speech act annotations against gold standard human annotations using **character-level comparison**. This approach treats each character position in the document as a classification instance, allowing precise measurement of span boundary accuracy.

### 1.2 Data Sources

| Source | Description |
|--------|-------------|
| **Gold Standard** | Human annotations from `data/normative.json`, filtered to speech act labels only |
| **LLM Predictions** | GPT-4 annotations from `responses/response_document_*.json` |

### 1.3 Document Mapping

| Input File | Document ID | Document Name |
|------------|-------------|---------------|
| document_01.md | 671918e2c6537d54ff0626db | Certifikáty autorizovaných inspektorů |
| document_02.md | 671918e2c6537d54ff0626dc | Co je to územní plánování |

### 1.4 Speech Act Labels

Nine speech act categories were used for annotation:

| Label | Czech Name | Description |
|-------|------------|-------------|
| 01_Situace | Situation | What situation/goal the advice applies to |
| 02_Kontext | Context | Broader picture, precedent cases, typical procedures |
| 03_Postup | Procedure | What the recipient is advised to do |
| 04_Proces | Process | Expected responses of authorities/other parties |
| 05_Podmínky | Conditions | Circumstances for action possibility |
| 06_Doporučení | Recommendations | Additional actions, option comparison |
| 07_Odkazy | Links | Internal links to Frank Bold knowledge base |
| 08_Prameny | References | External references (laws, regulations) |
| 09_Nezařaditelné | Unclassified | Any other text |

### 1.5 Metrics

For each label and overall:

- **Precision** = TP / (TP + FP) — How many predicted characters are correct
- **Recall** = TP / (TP + FN) — How many gold characters were found
- **F1 Score** = 2 × (P × R) / (P + R) — Harmonic mean of precision and recall
- **IoU** (Intersection over Union) = TP / (TP + FP + FN) — Overlap ratio

Aggregation methods:
- **Micro-average**: Aggregates TP/FP/FN across all labels before computing metrics
- **Macro-average**: Averages per-label metrics (gives equal weight to each label)

---

## 2. Results

### 2.1 Overall Performance

| Document | Micro F1 | Macro F1 | Micro IoU | Macro IoU |
|----------|----------|----------|-----------|-----------|
| document_01.md | 0.0918 | 0.0739 | 0.0481 | 0.0438 |
| document_02.md | 0.1881 | 0.1238 | 0.1038 | 0.0759 |
| **Average** | **0.1400** | **0.0989** | **0.0760** | **0.0599** |

### 2.2 Annotation Volume Comparison

| Document | Gold Annotations | LLM Annotations | Ratio |
|----------|------------------|-----------------|-------|
| document_01.md | 122 | 24 | 5.1x fewer |
| document_02.md | 99 | 30 | 3.3x fewer |

**Key finding:** LLM produces significantly fewer, larger spans compared to fine-grained gold annotations.

### 2.3 Per-Label Performance (Document 01)

| Label | Precision | Recall | F1 | Gold chars | Pred chars |
|-------|-----------|--------|-----|------------|------------|
| 09_Nezařaditelné | **0.8916** | 0.2320 | **0.3682** | 1,099 | 286 |
| 04_Proces | 0.5050 | 0.1760 | 0.2611 | 2,278 | 794 |
| 02_Kontext | 0.2096 | 0.0198 | 0.0361 | 5,772 | 544 |
| 01_Situace | 0.0 | 0.0 | 0.0 | 160 | 256 |
| 03_Postup | 0.0 | 0.0 | 0.0 | 334 | 1,154 |
| 05_Podmínky | 0.0 | 0.0 | 0.0 | 127 | 653 |
| 08_Prameny | 0.0 | 0.0 | 0.0 | 1,665 | 1,559 |
| 06_Doporučení | 0.0 | 0.0 | 0.0 | 77 | 0 |
| 07_Odkazy | 0.0 | 0.0 | 0.0 | 10 | 0 |

### 2.4 Per-Label Performance (Document 02)

| Label | Precision | Recall | F1 | Gold chars | Pred chars |
|-------|-----------|--------|-----|------------|------------|
| 01_Situace | 0.4938 | **0.4476** | **0.4696** | 802 | 727 |
| 02_Kontext | **0.5838** | 0.2305 | 0.3305 | 4,729 | 1,867 |
| 03_Postup | 0.1086 | 0.2923 | 0.1583 | 390 | 1,050 |
| 07_Odkazy | 0.0473 | 0.0244 | 0.0322 | 1,642 | 845 |
| 04_Proces | 0.0 | 0.0 | 0.0 | 2,638 | 0 |
| 05_Podmínky | 0.0 | 0.0 | 0.0 | 0 | 170 |
| 08_Prameny | 0.0 | 0.0 | 0.0 | 1,456 | 726 |
| 06_Doporučení | — | — | — | 0 | 0 |
| 09_Nezařaditelné | 0.0 | 0.0 | 0.0 | 1 | 0 |

### 2.5 Label Consistency Issues

| Document | Labels in Gold Only | Labels in Predictions Only |
|----------|--------------------|-----------------------------|
| document_01 | 06_Doporučení, 07_Odkazy | — |
| document_02 | 04_Proces, 06_Doporučení, 09_Nezařaditelné | 05_Podmínky |

---

## 3. Analysis

### 3.1 Main Issues Identified

#### Issue 1: Under-segmentation
The LLM produces ~4x fewer annotations than gold standard. Gold annotations are fine-grained (often sentence or clause level), while LLM creates paragraph-level spans.

#### Issue 2: Label Confusion
Several labels show systematic confusion:
- **03_Postup vs 05_Podmínky**: LLM often labels conditions as procedures
- **08_Prameny vs 07_Odkazy**: References to laws confused with internal links
- **04_Proces**: Frequently missed entirely (confused with 02_Kontext or 03_Postup)

#### Issue 3: Missing Labels
LLM fails to use certain categories:
- **06_Doporučení** (Recommendations) — never used in predictions
- **07_Odkazy** (Links) — rarely identified correctly

#### Issue 4: Boundary Misalignment
Even when correct label is assigned, span boundaries often don't match gold standard, causing low IoU scores.

---

## 4. Recommendations for Prompt Improvement

### 4.1 Increase Granularity

**Current instruction:**
> "Spans can be of any length (words, sentences, paragraphs) - prefer smaller, more granular spans over large sections"

**Suggested revision:**
```
CRITICAL: Create fine-grained annotations at the sentence or clause level, NOT paragraph level.
- Each sentence typically contains 1-3 separate speech acts
- A single paragraph often contains 5-10+ distinct annotations
- Target: 80-150 annotations per document (not 20-30)
- When in doubt, split into smaller spans rather than merge
```

### 4.2 Clarify Label Distinctions

Add explicit disambiguation guidance:

```
## Label Disambiguation Guide

### 03_Postup vs 05_Podmínky
- 03_Postup: Direct instructions ("Submit form X", "Contact the authority")
- 05_Podmínky: Prerequisites or conditions ("If you are...", "When the deadline passes...")

### 04_Proces vs 02_Kontext
- 04_Proces: Describes what happens AFTER recipient acts ("The authority will respond within 30 days")
- 02_Kontext: General background information, not tied to specific recipient action

### 07_Odkazy vs 08_Prameny
- 07_Odkazy: Links to OTHER Frank Bold advice articles (internal hyperlinks)
- 08_Prameny: Citations of laws, regulations, court decisions (external legal sources)

### 06_Doporučení Recognition
Look for comparative language: "We recommend...", "The better option is...", "Consider also..."
```

### 4.3 Add Concrete Examples

Extend the prompt with annotated examples from the gold standard:

```
## Worked Example

Consider this text segment:

"Většina staveb vyžaduje územní rozhodnutí a stavební povolení. [01_Situace]
Místo stavebního povolení si ale stavebník může opatřit tzv. certifikát. [05_Podmínky]
Certifikát zpracovává autorizovaný inspektor. [04_Proces]
Autorizovaný inspektor přezkoumává podklady ze stejných hledisek jako stavební úřad. [02_Kontext]"

Notice how a single paragraph contains 4 different speech acts at sentence level.
```

### 4.4 Add Coverage Verification Step

```
## Final Verification

Before submitting, verify:
1. Every character in the document is covered by at least one annotation
2. You have used at least 6 of the 9 categories (documents typically contain most types)
3. Total annotation count is 80+ for documents of this length
4. Check specifically for: 06_Doporučení (recommendations) and 04_Proces (authority responses)
```

### 4.5 Two-Pass Annotation Strategy

```
## Annotation Strategy

PASS 1 - Initial Segmentation:
- Read the document and identify all distinct spans (aim for 100+ segments)
- Assign preliminary labels

PASS 2 - Label Refinement:
- Review each annotation against the disambiguation guide
- Split any spans longer than 2 sentences
- Verify 04_Proces and 06_Doporučení are not missed
```

### 4.6 Fix Label Format

**Issue:** Gold standard uses `06_ Doporučení` (with space after underscore), but prompt shows `06_Doporučení`.

**Fix:** Ensure label format in prompt matches gold standard exactly, or normalize during evaluation.

---

## 5. Suggested Next Steps

1. **Update `payload_template.md`** with the improved instructions above
2. **Re-run annotation** on the same documents with improved prompts
3. **Compare results** to measure improvement
4. **Consider few-shot examples** by including 1-2 fully annotated paragraphs in the prompt
5. **Experiment with temperature** — try temperature=0.0 for more deterministic output
6. **Test chunking** — for long documents, annotate section-by-section to improve focus

---

## 6. Appendix: Evaluation Script

The evaluation was performed using `evaluate_annotations.py` which:
- Loads gold annotations from `data/normative.json` filtered by doc_id and speech act labels
- Loads LLM predictions from `responses/` directory
- Converts spans to character-level labels
- Computes per-label and aggregate metrics
- Outputs detailed JSON reports to `evaluations/` directory

**Run command:**
```bash
python3 evaluate_annotations.py
```

**Output files:**
- `evaluations/eval_response_document_01.json`
- `evaluations/eval_response_document_02.json`
- `evaluations/evaluation_summary.json`
