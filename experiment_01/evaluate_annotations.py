#!/usr/bin/env python3
"""
Evaluate LLM span annotations against gold standard annotations.

Computes character-level metrics: Precision, Recall, F1, IoU per label.
"""

import json
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

DOCUMENT_MAPPING = {
    "document_01.md": "671918e2c6537d54ff0626db",
    "document_02.md": "671918e2c6537d54ff0626dc",
}

SPEECH_ACT_LABELS = {
    "01_Situace",
    "02_Kontext",
    "03_Postup",
    "04_Proces",
    "05_Podmínky",
    "06_ Doporučení",
    "07_Odkazy",
    "08_Prameny",
    "09_Nezařaditelné",
}

NORMATIVE_PATH = Path(__file__).parent.parent / "data" / "normative.json"
RESPONSES_DIR = Path(__file__).parent / "responses"
OUTPUT_DIR = Path(__file__).parent / "evaluations"


@dataclass
class CharLevelMetrics:
    """Character-level metrics for a single label."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    @property
    def iou(self) -> float:
        union = self.true_positives + self.false_positives + self.false_negatives
        if union == 0:
            return 0.0
        return self.true_positives / union
    
    def to_dict(self) -> dict:
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "iou": round(self.iou, 4),
        }


def load_gold_annotations(doc_id: str, filter_speech_acts: bool = True) -> list[dict]:
    """Load gold standard annotations for a document from normative.json."""
    with open(NORMATIVE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    annotations = [
        ann for ann in data.get("annotations", [])
        if ann.get("doc_id") == doc_id
        and (not filter_speech_acts or ann.get("label") in SPEECH_ACT_LABELS)
    ]
    return annotations


def load_llm_annotations(response_file: Path) -> tuple[list[dict], str]:
    """Load LLM annotations from response file. Returns (annotations, source_document)."""
    with open(response_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    annotations = data.get("annotations", {}).get("annotations", [])
    source_doc = data.get("source_document", "")
    return annotations, source_doc


def get_document_length(doc_id: str) -> int:
    """Get the length of document text from normative.json."""
    with open(NORMATIVE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for doc in data.get("documents", []):
        if doc.get("doc_id") == doc_id:
            return len(doc.get("plainText", ""))
    return 0


def spans_to_char_labels(annotations: list[dict], doc_length: int) -> list[Optional[str]]:
    """
    Convert span annotations to character-level labels.
    Each character position gets the label of the span covering it.
    Overlapping spans: last one wins (for simplicity).
    """
    char_labels = [None] * doc_length
    
    for ann in annotations:
        start = ann.get("start", 0)
        end = ann.get("end", 0)
        label = ann.get("label", "")
        
        for i in range(start, min(end + 1, doc_length)):
            char_labels[i] = label
    
    return char_labels


def extract_labels(annotations: list[dict]) -> set[str]:
    """Extract unique labels from annotations."""
    return {ann.get("label", "") for ann in annotations if ann.get("label")}


def compute_metrics(
    gold_char_labels: list[Optional[str]],
    pred_char_labels: list[Optional[str]],
    all_labels: set[str]
) -> dict[str, CharLevelMetrics]:
    """Compute character-level metrics for each label."""
    metrics = {label: CharLevelMetrics() for label in all_labels}
    
    max_len = max(len(gold_char_labels), len(pred_char_labels))
    
    for i in range(max_len):
        gold = gold_char_labels[i] if i < len(gold_char_labels) else None
        pred = pred_char_labels[i] if i < len(pred_char_labels) else None
        
        for label in all_labels:
            gold_has = (gold == label)
            pred_has = (pred == label)
            
            if gold_has and pred_has:
                metrics[label].true_positives += 1
            elif pred_has and not gold_has:
                metrics[label].false_positives += 1
            elif gold_has and not pred_has:
                metrics[label].false_negatives += 1
    
    return metrics


def compute_overall_metrics(label_metrics: dict[str, CharLevelMetrics]) -> dict:
    """Compute macro and micro averaged metrics."""
    total_tp = sum(m.true_positives for m in label_metrics.values())
    total_fp = sum(m.false_positives for m in label_metrics.values())
    total_fn = sum(m.false_negatives for m in label_metrics.values())
    
    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0.0
    micro_iou = total_tp / (total_tp + total_fp + total_fn) if (total_tp + total_fp + total_fn) > 0 else 0.0
    
    non_empty_labels = [m for m in label_metrics.values() if m.true_positives + m.false_positives + m.false_negatives > 0]
    
    macro_precision = sum(m.precision for m in non_empty_labels) / len(non_empty_labels) if non_empty_labels else 0.0
    macro_recall = sum(m.recall for m in non_empty_labels) / len(non_empty_labels) if non_empty_labels else 0.0
    macro_f1 = sum(m.f1 for m in non_empty_labels) / len(non_empty_labels) if non_empty_labels else 0.0
    macro_iou = sum(m.iou for m in non_empty_labels) / len(non_empty_labels) if non_empty_labels else 0.0
    
    return {
        "micro": {
            "precision": round(micro_precision, 4),
            "recall": round(micro_recall, 4),
            "f1": round(micro_f1, 4),
            "iou": round(micro_iou, 4),
        },
        "macro": {
            "precision": round(macro_precision, 4),
            "recall": round(macro_recall, 4),
            "f1": round(macro_f1, 4),
            "iou": round(macro_iou, 4),
        }
    }


def verify_labels(gold_labels: set[str], pred_labels: set[str]) -> dict:
    """Verify label consistency between gold and predictions."""
    return {
        "gold_only": sorted(gold_labels - pred_labels),
        "pred_only": sorted(pred_labels - gold_labels),
        "common": sorted(gold_labels & pred_labels),
        "consistent": gold_labels == pred_labels,
    }


def evaluate_document(response_file: Path) -> dict:
    """Evaluate a single document's annotations."""
    pred_annotations, source_doc = load_llm_annotations(response_file)
    
    if source_doc not in DOCUMENT_MAPPING:
        return {"error": f"Unknown source document: {source_doc}"}
    
    doc_id = DOCUMENT_MAPPING[source_doc]
    gold_annotations = load_gold_annotations(doc_id)
    doc_length = get_document_length(doc_id)
    
    if doc_length == 0:
        return {"error": f"Could not find document with doc_id: {doc_id}"}
    
    gold_char_labels = spans_to_char_labels(gold_annotations, doc_length)
    pred_char_labels = spans_to_char_labels(pred_annotations, doc_length)
    
    gold_labels = extract_labels(gold_annotations)
    pred_labels = extract_labels(pred_annotations)
    all_labels = gold_labels | pred_labels
    
    label_verification = verify_labels(gold_labels, pred_labels)
    label_metrics = compute_metrics(gold_char_labels, pred_char_labels, all_labels)
    overall_metrics = compute_overall_metrics(label_metrics)
    
    return {
        "source_document": source_doc,
        "doc_id": doc_id,
        "document_length": doc_length,
        "gold_annotation_count": len(gold_annotations),
        "pred_annotation_count": len(pred_annotations),
        "label_verification": label_verification,
        "overall_metrics": overall_metrics,
        "per_label_metrics": {
            label: metrics.to_dict() 
            for label, metrics in sorted(label_metrics.items())
        },
    }


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    response_files = sorted(RESPONSES_DIR.glob("response_document_*.json"))
    
    if not response_files:
        print("No response files found in", RESPONSES_DIR)
        return
    
    all_results = []
    
    for response_file in response_files:
        print(f"Evaluating {response_file.name}...")
        result = evaluate_document(response_file)
        all_results.append(result)
        
        output_file = OUTPUT_DIR / f"eval_{response_file.stem}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  -> Saved to {output_file.name}")
        
        if "error" not in result:
            print(f"  -> Micro F1: {result['overall_metrics']['micro']['f1']:.4f}")
            print(f"  -> Macro F1: {result['overall_metrics']['macro']['f1']:.4f}")
            if not result['label_verification']['consistent']:
                print(f"  -> WARNING: Label mismatch!")
                print(f"     Gold only: {result['label_verification']['gold_only']}")
                print(f"     Pred only: {result['label_verification']['pred_only']}")
    
    summary = {
        "total_documents": len(all_results),
        "documents": [
            {
                "source_document": r.get("source_document", ""),
                "micro_f1": r.get("overall_metrics", {}).get("micro", {}).get("f1", 0),
                "macro_f1": r.get("overall_metrics", {}).get("macro", {}).get("f1", 0),
                "labels_consistent": r.get("label_verification", {}).get("consistent", False),
            }
            for r in all_results if "error" not in r
        ]
    }
    
    summary_file = OUTPUT_DIR / "evaluation_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSummary saved to {summary_file.name}")


if __name__ == "__main__":
    main()
