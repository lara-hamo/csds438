"""
collect_novels.py
Author: Maximilian Malz
Task: Collection and preparation of novel dataset from Project Gutenberg

Downloads a curated set of novels spanning different popularity tiers
(measured by download count on Gutenberg) for use in the distributed
text mining pipeline.
"""

import requests
import os
import time
import json
import logging
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
RAW_DIR    = "raw_novels"
LOG_DIR    = "logs"
META_FILE  = "dataset_metadata.json"
DELAY      = 1.5   # seconds between requests (be polite to Gutenberg)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "collection.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Novel catalog ──────────────────────────────────────────────────────────────
# Each entry: (gutenberg_id, title, author, popularity_tier)
# Popularity tiers: HIGH (top downloads), MEDIUM, LOW
# Source for rankings: https://www.gutenberg.org/browse/scores/top
NOVELS = [
    # HIGH popularity
    (1342,  "Pride and Prejudice",               "Jane Austen",           "HIGH"),
    (11,    "Alice's Adventures in Wonderland",  "Lewis Carroll",         "HIGH"),
    (84,    "Frankenstein",                      "Mary Shelley",          "HIGH"),
    (1661,  "The Adventures of Sherlock Holmes", "Arthur Conan Doyle",    "HIGH"),
    (98,    "A Tale of Two Cities",              "Charles Dickens",       "HIGH"),
    (2701,  "Moby Dick",                         "Herman Melville",       "HIGH"),
    (74,    "The Adventures of Tom Sawyer",      "Mark Twain",            "HIGH"),
    (1080,  "A Modest Proposal",                 "Jonathan Swift",        "HIGH"),

    # MEDIUM popularity
    (345,   "Dracula",                           "Bram Stoker",           "MEDIUM"),
    (1260,  "Jane Eyre",                         "Charlotte Bronte",      "MEDIUM"),
    (2542,  "A Doll's House",                    "Henrik Ibsen",          "MEDIUM"),
    (768,   "Wuthering Heights",                 "Emily Bronte",          "MEDIUM"),
    (5200,  "Metamorphosis",                     "Franz Kafka",           "MEDIUM"),
    (2554,  "Crime and Punishment",              "Fyodor Dostoevsky",     "MEDIUM"),
    (161,   "Sense and Sensibility",             "Jane Austen",           "MEDIUM"),
    (174,   "The Picture of Dorian Gray",        "Oscar Wilde",           "MEDIUM"),

    # LOW popularity
    (1400,  "Great Expectations",                "Charles Dickens",       "LOW"),
    (786,   "The Mayor of Casterbridge",         "Thomas Hardy",          "LOW"),
    (158,   "Emma",                              "Jane Austen",           "LOW"),
    (1184,  "The Count of Monte Cristo",         "Alexandre Dumas",       "LOW"),
    (2097,  "Leviathan",                         "Thomas Hobbes",         "LOW"),
    (209,   "The Turn of the Screw",             "Henry James",           "LOW"),
    (244,   "A Study in Scarlet",                "Arthur Conan Doyle",    "LOW"),
    (996,   "Don Quixote",                       "Miguel de Cervantes",   "LOW"),
]

GUTENBERG_URL = "https://www.gutenberg.org/files/{id}/{id}-0.txt"
GUTENBERG_ALT = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"


def fetch_novel(gutenberg_id: int) -> str | None:
    """Try primary then fallback Gutenberg URL."""
    for url_template in [GUTENBERG_URL, GUTENBERG_ALT]:
        url = url_template.format(id=gutenberg_id)
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and len(r.text) > 1000:
                log.info(f"  Fetched {gutenberg_id} from {url}")
                return r.text
        except requests.RequestException as e:
            log.warning(f"  Failed {url}: {e}")
    return None


def strip_gutenberg_header_footer(text: str) -> str:
    """
    Remove Project Gutenberg boilerplate that appears before and after
    the actual novel content.
    """
    start_markers = [
        "*** START OF THE PROJECT GUTENBERG",
        "*** START OF THIS PROJECT GUTENBERG",
        "*END*THE SMALL PRINT",
    ]
    end_markers = [
        "*** END OF THE PROJECT GUTENBERG",
        "*** END OF THIS PROJECT GUTENBERG",
        "End of the Project Gutenberg",
        "End of Project Gutenberg",
    ]

    start_idx = 0
    for marker in start_markers:
        idx = text.find(marker)
        if idx != -1:
            # Skip to end of that line
            start_idx = text.find("\n", idx) + 1
            break

    end_idx = len(text)
    for marker in end_markers:
        idx = text.find(marker)
        if idx != -1:
            end_idx = idx
            break

    return text[start_idx:end_idx].strip()


def save_novel(gutenberg_id: int, title: str, text: str) -> str:
    """Save raw text to disk, return filepath."""
    safe_title = title.replace(" ", "_").replace("'", "").replace("/", "-")
    filename = f"{gutenberg_id}_{safe_title}.txt"
    filepath = os.path.join(RAW_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    return filepath


def collect():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    metadata = []
    success, failed = 0, 0

    print(f"Starting dataset collection — {len(NOVELS)} novels targeted\n")
    log.info(f"Collection started — {len(NOVELS)} novels")

    for gid, title, author, tier in NOVELS:
        print(f"  [{tier}] {title} ({author}) ...", end=" ", flush=True)
        text = fetch_novel(gid)

        if text is None:
            print("FAILED")
            log.error(f"Could not fetch {gid} ({title})")
            failed += 1
            continue

        clean_text = strip_gutenberg_header_footer(text)
        filepath   = save_novel(gid, title, clean_text)
        word_count = len(clean_text.split())

        metadata.append({
            "gutenberg_id":    gid,
            "title":           title,
            "author":          author,
            "popularity_tier": tier,
            "word_count":      word_count,
            "char_count":      len(clean_text),
            "filename":        os.path.basename(filepath),
            "filepath":        filepath,
            "collected_at":    datetime.utcnow().isoformat(),
        })

        print(f"OK  ({word_count:,} words)")
        log.info(f"Saved {filepath} — {word_count} words")
        success += 1
        time.sleep(DELAY)

    # Write metadata manifest
    with open(META_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nDone. {success} collected, {failed} failed.")
    print(f"Metadata written to {META_FILE}")
    log.info(f"Collection complete: {success} success, {failed} failed")
    return metadata


if __name__ == "__main__":
    collect()
