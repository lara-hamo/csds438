#!/usr/bin/env python3
"""
organize_hdfs.py
Author: Maximilian Malz
Task: Organization of data in HDFS

Sets up a clean, consistent HDFS directory structure and uploads
the prepared novel corpus so downstream MapReduce jobs (TF-IDF,
n-gram extraction) can find their inputs reliably.

HDFS Layout:
  /project/
  ├── corpus/
  │   ├── high/          ← HIGH popularity novels
  │   ├── medium/        ← MEDIUM popularity novels
  │   └── low/           ← LOW popularity novels
  ├── metadata/
  │   └── dataset_metadata.json
  └── output/            ← Reserved for MapReduce job outputs
      ├── tfidf/
      ├── ngrams/
      └── preprocessing/

Usage:
  python3 organize_hdfs.py [--dry-run]

  --dry-run   Print all HDFS commands without executing (for review/testing
              when Hadoop is not yet configured).
"""

import os
import sys
import json
import subprocess
import logging
import argparse
from pathlib import Path

META_FILE  = "dataset_metadata.json"
CLEAN_DIR  = "cleaned_novels"
LOG_DIR    = "logs"
HDFS_ROOT  = "/project"

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "hdfs_upload.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── HDFS directory structure ───────────────────────────────────────────────────
HDFS_DIRS = [
    f"{HDFS_ROOT}/corpus/high",
    f"{HDFS_ROOT}/corpus/medium",
    f"{HDFS_ROOT}/corpus/low",
    f"{HDFS_ROOT}/metadata",
    f"{HDFS_ROOT}/output/tfidf",
    f"{HDFS_ROOT}/output/ngrams",
    f"{HDFS_ROOT}/output/preprocessing",
]

TIER_TO_HDFS = {
    "HIGH":   f"{HDFS_ROOT}/corpus/high",
    "MEDIUM": f"{HDFS_ROOT}/corpus/medium",
    "LOW":    f"{HDFS_ROOT}/corpus/low",
}


def run(cmd: list[str], dry_run: bool) -> bool:
    """Execute or print an HDFS command."""
    cmd_str = " ".join(cmd)
    if dry_run:
        print(f"  [DRY-RUN] {cmd_str}")
        return True
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            log.error(f"Command failed: {cmd_str}\n{result.stderr}")
            print(f"  FAILED: {result.stderr.strip()}")
            return False
        log.info(f"OK: {cmd_str}")
        return True
    except subprocess.TimeoutExpired:
        log.error(f"Timeout: {cmd_str}")
        print(f"  TIMEOUT: {cmd_str}")
        return False
    except FileNotFoundError:
        print("  ERROR: 'hdfs' command not found — is Hadoop installed and on PATH?")
        print("         Run with --dry-run to preview commands without Hadoop.")
        sys.exit(1)


def create_directories(dry_run: bool):
    """Create the full HDFS directory tree."""
    print("\n── Creating HDFS directory structure ──")
    for d in HDFS_DIRS:
        print(f"  mkdir -p {d} ...", end=" ", flush=True)
        ok = run(["hdfs", "dfs", "-mkdir", "-p", d], dry_run)
        if ok and not dry_run:
            print("OK")


def set_permissions(dry_run: bool):
    """Make output directories group-writable so all pipeline jobs can write."""
    print("\n── Setting permissions ──")
    for subdir in ["tfidf", "ngrams", "preprocessing"]:
        path = f"{HDFS_ROOT}/output/{subdir}"
        run(["hdfs", "dfs", "-chmod", "775", path], dry_run)


def upload_corpus(metadata: list[dict], dry_run: bool):
    """Upload each cleaned novel to its tier-appropriate HDFS directory."""
    print("\n── Uploading corpus ──")
    success, failed = 0, 0

    for entry in metadata:
        tier       = entry.get("popularity_tier", "LOW")
        clean_path = entry.get("clean_filepath")
        filename   = entry.get("clean_filename")

        if not clean_path or not os.path.exists(clean_path):
            print(f"  SKIP (missing): {filename}")
            log.warning(f"Missing cleaned file: {clean_path}")
            failed += 1
            continue

        hdfs_dest = f"{TIER_TO_HDFS[tier]}/{filename}"
        print(f"  [{tier}] {entry['title']:<45} → {hdfs_dest} ...", end=" ", flush=True)

        ok = run(["hdfs", "dfs", "-put", "-f", clean_path, hdfs_dest], dry_run)
        if ok:
            success += 1
            if not dry_run:
                print("OK")
        else:
            failed += 1

    return success, failed


def upload_metadata(dry_run: bool):
    """Upload the metadata JSON manifest to HDFS."""
    print("\n── Uploading metadata ──")
    hdfs_dest = f"{HDFS_ROOT}/metadata/dataset_metadata.json"
    print(f"  {META_FILE} → {hdfs_dest} ...", end=" ", flush=True)
    ok = run(["hdfs", "dfs", "-put", "-f", META_FILE, hdfs_dest], dry_run)
    if ok and not dry_run:
        print("OK")


def verify_upload(metadata: list[dict], dry_run: bool):
    """Run hdfs dfs -ls on each tier directory to confirm uploads."""
    if dry_run:
        print("\n── Verification skipped in dry-run mode ──")
        return
    print("\n── Verifying uploads ──")
    for tier_dir in TIER_TO_HDFS.values():
        print(f"\n  {tier_dir}:")
        run(["hdfs", "dfs", "-ls", tier_dir], dry_run=False)


def print_structure():
    """Pretty-print the intended HDFS layout."""
    print("""
HDFS Layout:
  /project/
  ├── corpus/
  │   ├── high/          ← HIGH popularity novels
  │   ├── medium/        ← MEDIUM popularity novels
  │   └── low/           ← LOW popularity novels
  ├── metadata/
  │   └── dataset_metadata.json
  └── output/
      ├── tfidf/         ← Lara: TF-IDF MapReduce output
      ├── ngrams/        ← n-gram extraction output
      └── preprocessing/ ← tokenization output
""")


def main():
    parser = argparse.ArgumentParser(description="Organize corpus in HDFS")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print HDFS commands without executing them")
    args = parser.parse_args()

    os.makedirs(LOG_DIR, exist_ok=True)

    if not os.path.exists(META_FILE):
        print(f"ERROR: {META_FILE} not found — run collect_novels.py and prepare_novels.py first.")
        sys.exit(1)

    with open(META_FILE) as f:
        metadata = json.load(f)

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    print(f"organize_hdfs.py — {mode} mode")
    print(f"Novels to upload: {len(metadata)}")
    print_structure()

    create_directories(args.dry_run)
    set_permissions(args.dry_run)
    success, failed = upload_corpus(metadata, args.dry_run)
    upload_metadata(args.dry_run)
    verify_upload(metadata, args.dry_run)

    print(f"\n{'='*50}")
    print(f"Upload complete: {success} succeeded, {failed} failed")
    print(f"HDFS root: {HDFS_ROOT}")
    log.info(f"HDFS upload done: {success} OK, {failed} failed")


if __name__ == "__main__":
    main()
