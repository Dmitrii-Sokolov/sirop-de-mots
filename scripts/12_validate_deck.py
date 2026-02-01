"""
Validate deck content before building.

Checks:
  1. Duplicates across CSV files (same French word in multiple sources)
  2. Invalid WordType values
  3. Expected vs actual row counts (deck_config.py)
  4. Missing audio files with detailed report
  5. Slugify stability (re-slugify produces same result)
  6. Card count calculation accuracy

Usage:
    PYTHONIOENCODING=utf-8 python scripts/12_validate_deck.py
"""

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Add scripts/ to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import PROJECT_ROOT, CONTENT_DIR, AUDIO_BASE_DIR, get_audio_dir
from deck_config import VOCABULARY_DECKS, AUTRES_DECK, CONTENT_DECKS, CONJUGATION_DECKS
from utils import slugify, get_audio_prefix

# =============================================================================
# Constants
# =============================================================================

# Valid WordType values recognized by Anki card templates
VALID_WORD_TYPES = {
    'm', 'f', 'm/f', 'v', 'adj', 'adv', 'conj', 'prep',
    'pron', 'num', 'interj', 'expr', 'loc', 'art',
}

# All vocab/content deck configs (not conjugation)
VOCAB_DECK_CONFIGS = {**VOCABULARY_DECKS, **AUTRES_DECK, **CONTENT_DECKS}
ALL_DECK_CONFIGS = {**VOCAB_DECK_CONFIGS, **CONJUGATION_DECKS}


# =============================================================================
# Helpers
# =============================================================================

def read_csv(path: Path) -> list[dict]:
    """Read CSV, return list of dicts. Empty list if file missing."""
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def deck_short_name(deck_name: str) -> str:
    """Extract short name from deck hierarchy."""
    return deck_name.split("::")[-1]


class ValidationReport:
    """Collects and prints validation results."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warning(self, msg: str):
        self.warnings.append(msg)

    def print_summary(self):
        print("\n" + "=" * 60)
        if self.errors:
            print(f"❌ ERRORS: {len(self.errors)}")
            for e in self.errors:
                print(f"  ❌ {e}")
        if self.warnings:
            print(f"⚠️  WARNINGS: {len(self.warnings)}")
            for w in self.warnings:
                print(f"  ⚠️  {w}")
        if not self.errors and not self.warnings:
            print("✅ All checks passed!")
        print("=" * 60)


# =============================================================================
# Check 1: Duplicates across CSV files
# =============================================================================

def check_duplicates(report: ValidationReport):
    """Find duplicate French entries across all vocabulary/content CSVs."""
    print("\n--- Check: Duplicates ---")

    # word -> list of source files
    seen: dict[str, list[str]] = defaultdict(list)

    for deck_name, info in VOCAB_DECK_CONFIGS.items():
        source = PROJECT_ROOT / info['source']
        rows = read_csv(source)
        short = deck_short_name(deck_name)
        for row in rows:
            french = row.get('French', '').strip()
            if french:
                seen[french].append(short)

    # Find words appearing in multiple decks
    cross_deck_dupes = {
        word: sources for word, sources in seen.items()
        if len(set(sources)) > 1
    }
    # Find words duplicated within same deck
    intra_deck_dupes = {
        word: sources for word, sources in seen.items()
        if len(sources) > len(set(sources)) or (len(set(sources)) == 1 and len(sources) > 1)
    }

    if cross_deck_dupes:
        report.error(f"{len(cross_deck_dupes)} words appear in multiple decks")
        for word, sources in sorted(cross_deck_dupes.items())[:10]:
            print(f"    «{word}» → {', '.join(sources)}")
        if len(cross_deck_dupes) > 10:
            print(f"    ... and {len(cross_deck_dupes) - 10} more")
    else:
        print("  ✅ No cross-deck duplicates")

    if intra_deck_dupes:
        report.warning(f"{len(intra_deck_dupes)} words duplicated within same deck")
        for word, sources in sorted(intra_deck_dupes.items())[:10]:
            counter = Counter(sources)
            for src, count in counter.items():
                if count > 1:
                    print(f"    «{word}» × {count} in {src}")
        if len(intra_deck_dupes) > 10:
            print(f"    ... and {len(intra_deck_dupes) - 10} more")
    else:
        print("  ✅ No intra-deck duplicates")


# =============================================================================
# Check 2: WordType validation
# =============================================================================

def check_word_types(report: ValidationReport):
    """Validate WordType values against known set."""
    print("\n--- Check: WordType ---")

    invalid: list[tuple[str, str, str]] = []  # (word, type, deck)

    for deck_name, info in VOCAB_DECK_CONFIGS.items():
        source = PROJECT_ROOT / info['source']
        rows = read_csv(source)
        short = deck_short_name(deck_name)
        for row in rows:
            wt = row.get('WordType', '').strip()
            if wt and wt not in VALID_WORD_TYPES:
                french = row.get('French', '?')
                invalid.append((french, wt, short))

    if invalid:
        # Group by invalid type
        by_type: dict[str, list[str]] = defaultdict(list)
        for french, wt, deck in invalid:
            by_type[wt].append(f"{french} ({deck})")

        report.warning(f"{len(invalid)} entries with unrecognized WordType")
        for wt, entries in sorted(by_type.items()):
            print(f"    WordType «{wt}»: {len(entries)} entries")
            for entry in entries[:3]:
                print(f"      {entry}")
            if len(entries) > 3:
                print(f"      ... and {len(entries) - 3} more")
    else:
        print("  ✅ All WordType values are valid")


# =============================================================================
# Check 3: Expected vs actual counts
# =============================================================================

def check_counts(report: ValidationReport):
    """Compare deck_config expected counts with actual CSV row counts."""
    print("\n--- Check: Row counts ---")

    mismatches = []
    for deck_name, info in ALL_DECK_CONFIGS.items():
        source = PROJECT_ROOT / info['source']
        expected = info['count']
        rows = read_csv(source)
        actual = len(rows)
        short = deck_short_name(deck_name)

        if not source.exists():
            report.error(f"{short}: file missing ({info['source']})")
        elif actual != expected:
            diff = actual - expected
            sign = "+" if diff > 0 else ""
            mismatches.append((short, expected, actual, diff))
            print(f"    {short}: expected {expected}, got {actual} ({sign}{diff})")

    if mismatches:
        report.warning(f"{len(mismatches)} decks have count mismatches vs deck_config.py")
    else:
        print("  ✅ All counts match deck_config.py")


# =============================================================================
# Check 4: Missing audio
# =============================================================================

def check_audio(report: ValidationReport):
    """Check for missing audio files across all vocabulary/content decks."""
    print("\n--- Check: Audio ---")

    total_expected = 0
    total_missing_word = 0
    total_missing_example = 0
    missing_details: dict[str, list[str]] = defaultdict(list)  # deck -> missing words

    for deck_name, info in VOCAB_DECK_CONFIGS.items():
        source = PROJECT_ROOT / info['source']
        if not source.exists():
            continue

        rows = read_csv(source)
        audio_dir = get_audio_dir(source)
        short = deck_short_name(deck_name)

        if not audio_dir.exists():
            report.error(f"{short}: audio dir missing ({audio_dir.relative_to(PROJECT_ROOT)})")
            continue

        deck_missing_word = 0
        deck_missing_ex = 0

        for row in rows:
            french = row.get('French', '').strip()
            if not french:
                continue
            total_expected += 1

            slug = slugify(french)
            word_path = audio_dir / f"{slug}.mp3"
            ex_path = audio_dir / f"{slug}_ex.mp3"

            if not word_path.exists():
                deck_missing_word += 1
                if len(missing_details[short]) < 5:
                    missing_details[short].append(f"{french} → {slug}.mp3")
            if not ex_path.exists():
                deck_missing_ex += 1

        total_missing_word += deck_missing_word
        total_missing_example += deck_missing_ex

        if deck_missing_word > 0 or deck_missing_ex > 0:
            print(f"    {short}: {deck_missing_word} words + {deck_missing_ex} examples missing")

    if total_missing_word > 0:
        report.warning(
            f"{total_missing_word}/{total_expected} word audio files missing, "
            f"{total_missing_example}/{total_expected} example audio missing"
        )
        for deck, samples in missing_details.items():
            if samples:
                print(f"    Samples from {deck}:")
                for s in samples:
                    print(f"      {s}")
    else:
        print(f"  ✅ All {total_expected} word audio files present")
        if total_missing_example > 0:
            report.warning(f"{total_missing_example}/{total_expected} example audio missing")
        else:
            print(f"  ✅ All {total_expected} example audio files present")


# =============================================================================
# Check 5: Slugify stability
# =============================================================================

def check_slugify_stability(report: ValidationReport):
    """Verify slugify is idempotent and produces unique results per deck."""
    print("\n--- Check: Slugify stability ---")

    non_idempotent = []
    slug_collisions: dict[str, list[tuple[str, str]]] = defaultdict(list)  # slug -> (french, deck)

    for deck_name, info in VOCAB_DECK_CONFIGS.items():
        source = PROJECT_ROOT / info['source']
        rows = read_csv(source)
        short = deck_short_name(deck_name)
        prefix = get_audio_prefix(source, CONTENT_DIR)

        for row in rows:
            french = row.get('French', '').strip()
            if not french:
                continue

            slug = slugify(french)
            slug2 = slugify(slug)
            if slug != slug2:
                non_idempotent.append((french, slug, slug2))

            # Check collisions within same audio prefix (same flat namespace)
            full_slug = f"{prefix}{slug}"
            slug_collisions[full_slug].append((french, short))

    if non_idempotent:
        report.error(f"slugify is not idempotent for {len(non_idempotent)} entries")
        for french, s1, s2 in non_idempotent[:5]:
            print(f"    «{french}» → «{s1}» → «{s2}»")
    else:
        print("  ✅ slugify is idempotent")

    collisions = {k: v for k, v in slug_collisions.items() if len(v) > 1}
    if collisions:
        report.error(f"{len(collisions)} slug collisions (different words → same audio filename)")
        for slug, entries in sorted(collisions.items())[:10]:
            words = [f"«{w}» ({d})" for w, d in entries]
            print(f"    {slug}.mp3 ← {', '.join(words)}")
        if len(collisions) > 10:
            print(f"    ... and {len(collisions) - 10} more")
    else:
        print("  ✅ No slug collisions")


# =============================================================================
# Check 6: Card count calculation
# =============================================================================

def check_card_count(report: ValidationReport):
    """Verify card count calculation in build script."""
    print("\n--- Check: Card count ---")

    vocab_entries = 0
    conj_entries = 0

    for deck_name, info in {**VOCABULARY_DECKS, **AUTRES_DECK, **CONTENT_DECKS}.items():
        source = PROJECT_ROOT / info['source']
        rows = read_csv(source)
        vocab_entries += len(rows)

    for deck_name, info in CONJUGATION_DECKS.items():
        source = PROJECT_ROOT / info['source']
        rows = read_csv(source)
        conj_entries += len(rows)

    total_entries = vocab_entries + conj_entries

    # Build script does: sum(v * 2 for v in stats.values())
    # This is wrong: vocab generates 2 cards per note (Recognition + Production)
    # but cloze generates variable cards per note (1 card per cloze number)
    build_script_calc = total_entries * 2

    # Correct: vocab * 2 templates, cloze * 2 (c1 + c2 for present/subjonctif)
    # Actually cloze card count depends on content, but present/subjonctif have c1+c2
    correct_vocab = vocab_entries * 2
    # Cloze: each note with {{c1::}} and {{c2::}} generates 2 cards
    # Participes/futur/être may have only {{c1::}} = 1 card each
    # We can't know exactly without reading content, so flag the issue

    print(f"  Vocabulary entries: {vocab_entries} × 2 templates = {correct_vocab} cards")
    print(f"  Conjugation entries: {conj_entries} (cloze, variable cards per note)")
    print(f"  Build script calculates: {build_script_calc} (all × 2)")

    report.warning(
        f"11_build_deck.py line 542: total_cards = sum(v * 2) "
        f"treats conjugation same as vocabulary. "
        f"Conjugation cloze cards depend on {{{{c1::}}}}/{{{{c2::}}}} count, not × 2"
    )


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("Deck Validation")
    print("=" * 60)

    report = ValidationReport()

    check_duplicates(report)
    check_word_types(report)
    check_counts(report)
    check_audio(report)
    check_slugify_stability(report)
    check_card_count(report)

    report.print_summary()

    # Exit code: 1 if errors, 0 otherwise
    sys.exit(1 if report.errors else 0)


if __name__ == "__main__":
    main()
