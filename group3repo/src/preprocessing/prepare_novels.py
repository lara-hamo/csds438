"""
prepare_novels.py
Author: Maximilian Malz
Task: Pre-processing and preparation of raw novel text for MapReduce pipeline

Reads raw novels from raw_novels/, applies cleaning steps, and writes
cleaned output to cleaned_novels/. Also produces a summary report.

Cleaning steps applied:
  1. Unicode normalization (NFKD → ASCII)
  2. Lowercase conversion
  3. Removal of non-alphabetic characters (keep spaces + newlines)
  4. Collapse of excess whitespace
  5. Line-length normalization (wrap to ~80 chars for HDFS chunking)

Output format: one sentence/line where possible (aids MapReduce splitting).
"""

import os
import re
import json
import unicodedata
import textwrap
import logging
from pathlib import Path

RAW_DIR     = "raw_novels"
CLEAN_DIR   = "cleaned_novels"
META_FILE   = "dataset_metadata.json"
LOG_DIR     = "logs"
REPORT_FILE = "preparation_report.txt"

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "preparation.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


# ── Cleaning functions ─────────────────────────────────────────────────────────

def normalize_unicode(text: str) -> str:
    """Normalize unicode to closest ASCII equivalent."""
    nfkd = unicodedata.normalize("NFKD", text)
    return nfkd.encode("ascii", errors="ignore").decode("ascii")


def remove_special_chars(text: str) -> str:
    """Keep only alphabetic characters, spaces, and newlines."""
    return re.sub(r"[^a-zA-Z \n]", " ", text)


def collapse_whitespace(text: str) -> str:
    """
    Collapse multiple spaces to one.
    Collapse 3+ consecutive newlines to 2 (preserve paragraph breaks).
    """
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_sentences(text: str) -> list[str]:
    """
    Rough sentence splitter — good enough for TF-IDF/n-gram work.
    Splits on period/exclamation/question followed by whitespace + capital.
    """
    # Simple regex-based split; keeps the delimiter with the preceding sentence
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def clean_text(raw: str) -> tuple[str, dict]:
    """Full cleaning pipeline. Returns (cleaned_text, stats)."""
    original_chars = len(raw)

    text = normalize_unicode(raw)
    # Split sentences BEFORE lowercasing so capital-letter heuristic works
    sentences = split_into_sentences(text)
    # Now apply remaining cleaning per sentence
    cleaned_sentences = []
    for s in sentences:
        s = s.lower()
        s = remove_special_chars(s)
        s = collapse_whitespace(s)
        if s.strip():
            cleaned_sentences.append(s.strip())

    # Write one sentence per line for MapReduce InputFormat splitting
    output = "\n".join(cleaned_sentences)

    stats = {
        "original_chars":  original_chars,
        "cleaned_chars":   len(output),
        "sentence_count":  len(cleaned_sentences),
        "word_count":      len(output.split()),
        "reduction_pct":   round((1 - len(output) / max(original_chars, 1)) * 100, 1),
    }
    return output, stats


# ── Main ───────────────────────────────────────────────────────────────────────

def prepare():
    os.makedirs(CLEAN_DIR, exist_ok=True)
    os.makedirs(LOG_DIR,   exist_ok=True)

    # Load metadata written by collect_novels.py
    if not os.path.exists(META_FILE):
        print(f"ERROR: {META_FILE} not found — run collect_novels.py first.")
        return

    with open(META_FILE) as f:
        metadata = json.load(f)

    report_lines = [
        "Novel Preparation Report",
        "=" * 60,
        f"Total novels: {len(metadata)}",
        "",
        f"{'Title':<45} {'Tier':<8} {'Words':>8} {'Sents':>7} {'Reduc':>7}",
        "-" * 60,
    ]

    updated_metadata = []

    for entry in metadata:
        raw_path = entry["filepath"]
        if not os.path.exists(raw_path):
            log.warning(f"Missing raw file: {raw_path}")
            continue

        print(f"  Cleaning: {entry['title']} ...", end=" ", flush=True)

        with open(raw_path, encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        cleaned, stats = clean_text(raw)

        # Write cleaned file
        clean_filename = "clean_" + entry["filename"]
        clean_path     = os.path.join(CLEAN_DIR, clean_filename)
        with open(clean_path, "w", encoding="utf-8") as f:
            f.write(cleaned)

        entry.update({
            "clean_filepath":  clean_path,
            "clean_filename":  clean_filename,
            "prep_stats":      stats,
        })
        updated_metadata.append(entry)

        log.info(f"Cleaned {entry['title']}: {stats}")
        print(f"OK  ({stats['word_count']:,} words, {stats['reduction_pct']}% reduction)")

        report_lines.append(
            f"{entry['title']:<45} {entry['popularity_tier']:<8} "
            f"{stats['word_count']:>8,} {stats['sentence_count']:>7,} "
            f"{stats['reduction_pct']:>6.1f}%"
        )

    # Tier summary
    tiers = {}
    for e in updated_metadata:
        t = e["popularity_tier"]
        s = e.get("prep_stats", {})
        if t not in tiers:
            tiers[t] = {"count": 0, "words": 0}
        tiers[t]["count"] += 1
        tiers[t]["words"] += s.get("word_count", 0)

    report_lines += [
        "",
        "Tier Summary",
        "-" * 30,
    ]
    for tier, d in sorted(tiers.items()):
        report_lines.append(
            f"  {tier:<8}: {d['count']} novels, {d['words']:,} total words"
        )

    report_text = "\n".join(report_lines)
    with open(REPORT_FILE, "w") as f:
        f.write(report_text)

    # Update metadata with clean paths
    with open(META_FILE, "w") as f:
        json.dump(updated_metadata, f, indent=2)

    print(f"\nPreparation complete. Report: {REPORT_FILE}")
    print(report_text)


if __name__ == "__main__":
    prepare()
