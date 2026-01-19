"""
Merge and deduplicate québécismes from multiple sources.

Input: data/quebecismes/*.csv
Output: data/quebecismes_merged.csv

Merges data from:
1. OQLF (official terminology)
2. Le Caméléon (with definitions)
3. Wiktionary (word list)
4. Exionnaire (word list)
"""

import csv
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
QUEBECISMES_DIR = PROJECT_ROOT / "data" / "quebecismes"
OUTPUT_PATH = PROJECT_ROOT / "data" / "quebecismes_merged.csv"


def normalize_word(word: str) -> str:
    """Normalize word for deduplication."""
    # Strip whitespace
    word = word.strip()

    # Remove quotes
    word = word.strip('"\'')

    # Normalize unicode (é vs e + combining accent)
    word = unicodedata.normalize("NFC", word)

    # Lowercase for comparison
    word = word.lower()

    # Normalize spaces and hyphens
    word = re.sub(r"[\s\-–—]+", " ", word)

    # Remove trailing punctuation
    word = word.rstrip(".,;:!?")

    return word


def extract_base_word(word: str) -> str:
    """Extract base word from complex entries like 'Achalant, E' or 'mot (n. f.)'."""
    # Remove part of speech markers in parentheses
    word = re.sub(r"\s*\([^)]*\)\s*", "", word)

    # Handle "Word, E" pattern (masculine/feminine)
    if ", " in word:
        parts = word.split(", ")
        if len(parts) == 2 and len(parts[1]) <= 4:
            # Likely a gender suffix like "E", "TRICE", etc.
            word = parts[0]

    return word.strip()


def parse_oqlf(filepath: Path) -> list[dict]:
    """Parse OQLF official terms CSV."""
    entries = []

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            term = row.get("Termes_Officialises", "").strip()
            if not term:
                continue

            # Extract word from "mot (n. f.)" format
            match = re.match(r"^(.+?)\s*\(([^)]+)\)", term)
            if match:
                word = match.group(1).strip()
                pos = match.group(2).strip()
            else:
                word = term
                pos = ""

            # Remove [Québec/Canada] markers
            word = re.sub(r"\s*\[.*?\]", "", word)

            definition = row.get("Definition", "").strip()
            english = row.get("Equivalent_anglais", "").strip()

            if english and definition:
                definition = f"{definition} (en: {english})"
            elif english:
                definition = f"(en: {english})"

            entries.append({
                "word": word,
                "pos": pos,
                "definition": definition,
                "source": "oqlf"
            })

    return entries


def parse_cameleon(filepath: Path) -> list[dict]:
    """Parse Le Caméléon CSV."""
    entries = []

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            word = row.get("word", "").strip()
            if not word:
                continue

            # Handle complex entries like "Achalant, E"
            word = extract_base_word(word)

            pos = row.get("pos", "").strip()
            definition = row.get("definition", "").strip()

            entries.append({
                "word": word,
                "pos": pos,
                "definition": definition,
                "source": "cameleon"
            })

    return entries


def parse_wiktionary(filepath: Path) -> list[dict]:
    """Parse Wiktionary word list CSV."""
    entries = []

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            word = row.get("word", "").strip()
            if not word:
                continue

            # Skip entries that look like codes/abbreviations only
            # (keep if they're actual words)
            if len(word) <= 2 and word.isupper():
                continue

            # Skip numeric-only entries
            if word.isdigit():
                continue

            entries.append({
                "word": word,
                "pos": "",
                "definition": "",
                "source": "wiktionary"
            })

    return entries


def parse_exionnaire(filepath: Path) -> list[dict]:
    """Parse Exionnaire word list CSV."""
    entries = []

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            word = row.get("word", "").strip()
            if not word:
                continue

            # Convert from uppercase
            word = word.title()

            entries.append({
                "word": word,
                "pos": "",
                "definition": "",
                "source": "exionnaire"
            })

    return entries


def merge_entries(all_entries: list[dict]) -> list[dict]:
    """Merge entries by normalized word, combining information."""
    # Group by normalized word
    grouped = defaultdict(list)

    for entry in all_entries:
        key = normalize_word(entry["word"])
        if key:  # Skip empty
            grouped[key].append(entry)

    # Merge each group
    merged = []

    for key, entries in grouped.items():
        # Pick the best word form (prefer title case, then as-is)
        word_forms = [e["word"] for e in entries]

        # Prefer form from Caméléon (has proper casing)
        best_word = None
        for e in entries:
            if e["source"] == "cameleon":
                best_word = e["word"]
                break

        if not best_word:
            # Pick title-cased version if available
            for w in word_forms:
                if w and w[0].isupper() and not w.isupper():
                    best_word = w
                    break

        if not best_word:
            best_word = word_forms[0]

        # Collect all POS tags
        pos_set = set()
        for e in entries:
            if e["pos"]:
                pos_set.add(e["pos"])
        pos = "; ".join(sorted(pos_set)) if pos_set else ""

        # Pick best definition (prefer Caméléon, then OQLF)
        definition = ""
        for source in ["cameleon", "oqlf"]:
            for e in entries:
                if e["source"] == source and e["definition"]:
                    definition = e["definition"]
                    break
            if definition:
                break

        # Collect sources
        sources = sorted(set(e["source"] for e in entries))

        merged.append({
            "word": best_word,
            "pos": pos,
            "definition": definition,
            "sources": ",".join(sources)
        })

    return merged


def main():
    print("=" * 60)
    print("MERGE QUÉBÉCISMES")
    print("=" * 60)

    all_entries = []

    # 1. OQLF
    oqlf_path = QUEBECISMES_DIR / "oqlf_termes_officialises.csv"
    if oqlf_path.exists():
        entries = parse_oqlf(oqlf_path)
        print(f"  OQLF: {len(entries)} entries")
        all_entries.extend(entries)
    else:
        print(f"  OQLF: not found")

    # 2. Caméléon
    cameleon_path = QUEBECISMES_DIR / "cameleon_quebecismes.csv"
    if cameleon_path.exists():
        entries = parse_cameleon(cameleon_path)
        print(f"  Caméléon: {len(entries)} entries")
        all_entries.extend(entries)
    else:
        print(f"  Caméléon: not found")

    # 3. Wiktionary
    wiktionary_path = QUEBECISMES_DIR / "wiktionary_quebecismes.csv"
    if wiktionary_path.exists():
        entries = parse_wiktionary(wiktionary_path)
        print(f"  Wiktionary: {len(entries)} entries")
        all_entries.extend(entries)
    else:
        print(f"  Wiktionary: not found")

    # 4. Exionnaire
    exionnaire_path = QUEBECISMES_DIR / "exionnaire_quebecismes.csv"
    if exionnaire_path.exists():
        entries = parse_exionnaire(exionnaire_path)
        print(f"  Exionnaire: {len(entries)} entries")
        all_entries.extend(entries)
    else:
        print(f"  Exionnaire: not found")

    print(f"\n  Total raw: {len(all_entries)} entries")

    # Merge and deduplicate
    print("\nMerging and deduplicating...")
    merged = merge_entries(all_entries)

    # Sort alphabetically
    merged.sort(key=lambda x: normalize_word(x["word"]))

    print(f"  After merge: {len(merged)} unique entries")

    # Statistics
    with_definition = sum(1 for e in merged if e["definition"])
    with_pos = sum(1 for e in merged if e["pos"])

    source_counts = defaultdict(int)
    for e in merged:
        for src in e["sources"].split(","):
            source_counts[src] += 1

    print(f"\n  With definition: {with_definition}")
    print(f"  With POS: {with_pos}")
    print(f"\n  By source:")
    for src, count in sorted(source_counts.items()):
        print(f"    {src}: {count}")

    # Multi-source entries
    multi_source = sum(1 for e in merged if "," in e["sources"])
    print(f"\n  Found in multiple sources: {multi_source}")

    # Save
    print(f"\nSaving to: {OUTPUT_PATH}")

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["word", "pos", "definition", "sources"])
        writer.writeheader()
        writer.writerows(merged)

    print(f"  Done! {OUTPUT_PATH.stat().st_size:,} bytes")

    # Show sample
    print("\n" + "=" * 60)
    print("SAMPLE (first 20 entries)")
    print("=" * 60)

    for entry in merged[:20]:
        word = entry["word"]
        pos = f" ({entry['pos']})" if entry["pos"] else ""
        sources = f" [{entry['sources']}]"
        defn = entry["definition"][:60] + "..." if len(entry["definition"]) > 60 else entry["definition"]

        print(f"  {word}{pos}{sources}")
        if defn:
            print(f"    → {defn}")


if __name__ == "__main__":
    main()
