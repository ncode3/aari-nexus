#!/usr/bin/env python3
"""
AARI-NEXUS Google Drive Ingestion Pipeline
Watches data/google_drive and classifies + ingests documents into domain vector stores.

Pipeline:
  Google Drive sync → file watcher → domain classifier → vector store update

Usage:
  python3 scripts/ingest_drive.py              # ingest existing files once
  python3 scripts/ingest_drive.py --watch      # watch for new files continuously
  python3 scripts/ingest_drive.py --file FILE  # ingest a single file
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scripts.domain_router import route_query  # noqa: E402

# ── Config ────────────────────────────────────────────────────────────────────

WATCH_DIR = ROOT / "data" / "google_drive"
DATA_DIR = ROOT / "data"
VECTOR_STORE_DIR = ROOT / "vector_stores"
LOG_DIR = ROOT / "logs"
INGESTED_DB = LOG_DIR / "ingested.json"

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt", ".docx", ".rst", ".csv"}

OLLAMA_EMBED_MODEL = "nomic-embed-text"
OLLAMA_API_BASE = "http://localhost:11434"


# ── Ingestion tracking ────────────────────────────────────────────────────────

def load_ingested() -> dict:
    if INGESTED_DB.exists():
        with open(INGESTED_DB) as f:
            return json.load(f)
    return {}


def save_ingested(db: dict):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(INGESTED_DB, "w") as f:
        json.dump(db, f, indent=2)


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


# ── Domain classification ─────────────────────────────────────────────────────

def classify_file(path: Path) -> str:
    """
    Classify a file into a domain using:
    1. Parent folder name (if already in a domain folder)
    2. Filename keyword match
    3. Content sample keyword match (first 500 chars)
    """
    # Check if already sorted into a domain folder
    for part in path.parts:
        if part in ["quantum", "robotics", "infrastructure",
                    "world_models", "linear_algebra", "research_papers"]:
            return part

    # Use filename + content sample
    sample = path.name
    if path.suffix in {".md", ".txt", ".rst", ".csv"}:
        try:
            sample += " " + path.read_text(errors="ignore")[:500]
        except Exception:
            pass

    result = route_query(sample)
    return result.domain


# ── Core ingestion ────────────────────────────────────────────────────────────

def ingest_file(path: Path, ingested_db: dict, verbose: bool = True) -> bool:
    """Ingest a single file into the correct domain vector store."""
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        if verbose:
            print(f"  SKIP (unsupported type): {path.name}")
        return False

    fhash = file_hash(path)
    if ingested_db.get(str(path)) == fhash:
        if verbose:
            print(f"  SKIP (already ingested): {path.name}")
        return False

    domain = classify_file(path)
    domain_dir = DATA_DIR / domain
    domain_dir.mkdir(parents=True, exist_ok=True)

    # Symlink into domain folder (avoids duplication)
    link_target = domain_dir / path.name
    if not link_target.exists():
        link_target.symlink_to(path.resolve())

    ingested_db[str(path)] = fhash
    print(f"  ✓ {path.name} → {domain}/")
    return True


def ingest_directory(directory: Path, verbose: bool = True) -> int:
    """Ingest all supported files in a directory."""
    ingested_db = load_ingested()
    count = 0

    files = sorted([
        f for f in directory.rglob("*")
        if f.is_file() and not f.name.startswith(".")
    ])

    if not files:
        print(f"  No files found in {directory}")
        return 0

    print(f"\nIngesting {len(files)} file(s) from {directory}\n")
    for f in files:
        if ingest_file(f, ingested_db, verbose):
            count += 1

    save_ingested(ingested_db)
    print(f"\n✓ Ingested {count} new file(s)")
    return count


# ── File watcher ──────────────────────────────────────────────────────────────

def watch_directory(directory: Path, interval: int = 10):
    """Continuously watch directory for new files and ingest them."""
    print(f"\n── AARI-NEXUS File Watcher ──")
    print(f"Watching: {directory}")
    print(f"Interval: {interval}s\n")
    print("Press Ctrl+C to stop.\n")

    seen: set = set()

    while True:
        try:
            current = set(
                f for f in directory.rglob("*")
                if f.is_file() and not f.name.startswith(".")
            )
            new_files = current - seen
            if new_files:
                ingested_db = load_ingested()
                for f in sorted(new_files):
                    ingest_file(f, ingested_db, verbose=True)
                save_ingested(ingested_db)
            seen = current
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nWatcher stopped.")
            break


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AARI-NEXUS Drive Ingestion Pipeline")
    parser.add_argument("--watch", action="store_true", help="Watch for new files continuously")
    parser.add_argument("--file", type=str, help="Ingest a single file by path")
    parser.add_argument("--dir", type=str, default=str(WATCH_DIR), help="Directory to ingest")
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file not found: {path}")
            sys.exit(1)
        db = load_ingested()
        ingest_file(path, db, verbose=True)
        save_ingested(db)
    elif args.watch:
        watch_directory(Path(args.dir))
    else:
        ingest_directory(Path(args.dir))
