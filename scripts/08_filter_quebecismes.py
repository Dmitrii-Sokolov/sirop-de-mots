"""
Filter québécismes: keep only with definitions, add frequency from Lexique383.

Input: data/quebecismes_merged.csv
Output: data/quebecismes_filtered.csv
"""

import csv
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MERGED_PATH = PROJECT_ROOT / "data" / "quebecismes_merged.csv"
LEXIQUE_PATH = PROJECT_ROOT / "Lexique383.tsv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "quebecismes_filtered.csv"


def normalize_for_lookup(word: str) -> str:
    """Normalize word for Lexique lookup."""
    word = word.strip().lower()
    word = unicodedata.normalize("NFC", word)
    # Remove articles
    word = re.sub(r"^(le |la |l'|les |un |une |des )", "", word)
    # Remove trailing punctuation
    word = word.rstrip(".,;:!?")
    return word


def load_lexique_frequencies(filepath: Path) -> dict[str, float]:
    """Load frequency data from Lexique383."""
    print(f"Loading Lexique383 from {filepath}...")

    freq_map = {}

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            lemme = row.get("lemme", "").strip().lower()
            ortho = row.get("ortho", "").strip().lower()

            # Combined frequency (films weighted higher for oral)
            try:
                freq_films = float(row.get("freqlemfilms2", 0) or 0)
                freq_books = float(row.get("freqlemlivres", 0) or 0)
                freq = 0.6 * freq_films + 0.4 * freq_books
            except (ValueError, TypeError):
                freq = 0

            # Store both lemme and ortho
            if lemme and freq > freq_map.get(lemme, 0):
                freq_map[lemme] = freq
            if ortho and freq > freq_map.get(ortho, 0):
                freq_map[ortho] = freq

    print(f"  Loaded {len(freq_map):,} entries")
    return freq_map


def main():
    print("=" * 60)
    print("FILTER QUÉBÉCISMES")
    print("=" * 60)

    # Load Lexique frequencies
    lexique_freq = load_lexique_frequencies(LEXIQUE_PATH)

    # Load merged québécismes
    print(f"\nLoading {MERGED_PATH}...")

    entries = []
    with open(MERGED_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)

    print(f"  Total: {len(entries)}")

    # Filter: only with definitions
    with_def = [e for e in entries if e.get("definition", "").strip()]
    print(f"  With definitions: {len(with_def)}")

    # Add frequency from Lexique383
    print("\nMatching with Lexique383...")

    matched = 0
    for entry in with_def:
        word = entry["word"]
        lookup_key = normalize_for_lookup(word)

        # Try exact match
        freq = lexique_freq.get(lookup_key, 0)

        # Try without accents if no match
        if freq == 0:
            # Try first word only (for multi-word entries)
            first_word = lookup_key.split()[0] if " " in lookup_key else lookup_key
            freq = lexique_freq.get(first_word, 0)

        entry["frequency"] = freq
        if freq > 0:
            matched += 1

        # Count sources
        sources = entry.get("sources", "").split(",")
        entry["source_count"] = len(sources)

    print(f"  Matched in Lexique: {matched} ({matched*100//len(with_def)}%)")

    # Sort by: frequency (desc), then source_count (desc), then alphabetically
    with_def.sort(key=lambda x: (-x["frequency"], -x["source_count"], x["word"].lower()))

    # Statistics
    print("\n" + "=" * 60)
    print("FREQUENCY DISTRIBUTION")
    print("=" * 60)

    freq_brackets = [
        (100, "Very high (≥100)"),
        (10, "High (10-99)"),
        (1, "Medium (1-9.99)"),
        (0.1, "Low (0.1-0.99)"),
        (0, "Very low/Not in Lexique (<0.1)")
    ]

    for threshold, label in freq_brackets:
        if threshold > 0:
            count = sum(1 for e in with_def if e["frequency"] >= threshold)
        else:
            count = sum(1 for e in with_def if e["frequency"] < 0.1)
        print(f"  {label}: {count}")

    # Save all with definitions
    print(f"\nSaving to {OUTPUT_PATH}...")

    fieldnames = ["word", "pos", "definition", "sources", "source_count", "frequency"]

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(with_def)

    print(f"  Saved {len(with_def)} entries")

    # Show top entries by frequency
    print("\n" + "=" * 60)
    print("TOP 30 BY FREQUENCY")
    print("=" * 60)

    for i, entry in enumerate(with_def[:30], 1):
        word = entry["word"]
        freq = entry["frequency"]
        sources = entry["source_count"]
        defn = entry["definition"][:50] + "..." if len(entry["definition"]) > 50 else entry["definition"]

        print(f"{i:2}. {word:<20} freq={freq:>7.2f} src={sources} | {defn}")

    # Show entries from multiple sources (most validated)
    print("\n" + "=" * 60)
    print("TOP 20 FROM MULTIPLE SOURCES (≥3)")
    print("=" * 60)

    multi_source = [e for e in with_def if e["source_count"] >= 3]
    multi_source.sort(key=lambda x: (-x["source_count"], -x["frequency"]))

    for i, entry in enumerate(multi_source[:20], 1):
        word = entry["word"]
        freq = entry["frequency"]
        sources = entry["sources"]
        defn = entry["definition"][:40] + "..." if len(entry["definition"]) > 40 else entry["definition"]

        print(f"{i:2}. {word:<20} [{sources}] | {defn}")


if __name__ == "__main__":
    main()
