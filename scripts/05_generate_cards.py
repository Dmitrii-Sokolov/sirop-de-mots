"""
Generate card skeletons from Lexique383 categories + additions.

Inputs:
    - categories/*.csv (NOM, VER, ADJ, ADV, etc.)
    - additions/professions_f.csv
    - additions/quebecismes.csv
    - data/all_expressions.csv (already in final Anki format)
    - data/blacklist.csv, whitelist_numerals.csv
    - data/irregular_adjectives.csv, irregular_verbs.csv

Outputs:
    - output/vocabulary_skeleton.csv (French, WordType, Notes, Source, freqlem)
    - output/conjugation_skeleton.csv (Verb, Notes, freqlem)
    - output/expressions.csv (copy of all_expressions, already complete)
"""

import csv
import re
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from config import (
    PROJECT_ROOT, DATA_DIR, CATEGORIES_DIR, ADDITIONS_DIR, OUTPUT_DIR,
    BLACKLIST_PATH, WHITELIST_NUMERALS_PATH,
    IRREGULAR_ADJ_PATH, IRREGULAR_VERBS_PATH,
    get_wordtype,
)


# =============================================================================
# Constants
# =============================================================================

FRENCH_VOWELS = "aeiouhéèêëàâäùûüîïôœæ"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class VocabEntry:
    """Vocabulary card entry."""
    french: str
    wordtype: str
    notes: str = ""
    source: str = "lexique"
    freqlem: float = 0.0
    cgram: str = ""
    priority: str = ""  # for quebecismes: high/medium

    def to_row(self) -> dict:
        return {
            "French": self.french,
            "WordType": self.wordtype,
            "Notes": self.notes,
            "Source": self.source,
            "freqlem": f"{self.freqlem:.2f}",
            "Priority": self.priority,
        }


@dataclass
class ConjugationEntry:
    """Conjugation card entry (verb for later tense expansion)."""
    verb: str
    notes: str = ""
    freqlem: float = 0.0
    group: str = ""  # 1er, 2e, 3e groupe

    def to_row(self) -> dict:
        return {
            "Verb": self.verb,
            "Notes": self.notes,
            "freqlem": f"{self.freqlem:.2f}",
            "Group": self.group,
        }


# =============================================================================
# Loaders
# =============================================================================

def load_blacklist(path: Path) -> set[str]:
    """Load blacklisted lemmas."""
    blacklist = set()
    if not path.exists():
        return blacklist

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            blacklist.add(row["lemme"].lower())

    return blacklist


def load_whitelist_numerals(path: Path) -> dict[str, str]:
    """Load whitelisted numerals with notes."""
    whitelist = {}
    if not path.exists():
        return whitelist

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lemme = row["lemme"].lower()
            notes = row.get("notes", "")
            whitelist[lemme] = notes

    return whitelist


def load_irregular_adjectives(path: Path) -> dict[str, tuple[str, str, str]]:
    """Load irregular adjectives: lemme -> (form_m, form_f, notes)."""
    irregulars = {}
    if not path.exists():
        return irregulars

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lemme = row["lemme"].lower()
            form_m = row.get("form_m", "")
            form_f = row.get("form_f", "")
            notes = row.get("notes", "")
            irregulars[lemme] = (form_m, form_f, notes)

    return irregulars


def load_irregular_verbs(path: Path) -> dict[str, tuple[str, str]]:
    """Load irregular verbs: lemme -> (ending_type, notes)."""
    irregulars = {}
    if not path.exists():
        return irregulars

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lemme = row["lemme"].lower()
            ending = row.get("ending_type", "")
            notes = row.get("notes", "")
            irregulars[lemme] = (ending, notes)

    return irregulars


def load_category(path: Path) -> list[dict]:
    """Load a category CSV file."""
    if not path.exists():
        print(f"  Warning: {path.name} not found")
        return []

    entries = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)

    return entries


def load_quebecismes(path: Path) -> list[dict]:
    """Load quebecismes from additions."""
    if not path.exists():
        print(f"  Warning: quebecismes.csv not found")
        return []

    entries = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)

    return entries


def load_professions_f(path: Path) -> list[dict]:
    """Load feminine profession forms."""
    if not path.exists():
        print(f"  Warning: professions_f.csv not found")
        return []

    entries = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)

    return entries


# =============================================================================
# Formatters
# =============================================================================

def starts_with_vowel(word: str) -> bool:
    """Check if word starts with a vowel or h (requires elision in French)."""
    if not word:
        return False
    return word[0].lower() in FRENCH_VOWELS


def format_noun(lemme: str, genre: str) -> str:
    """Format noun with article.

    Args:
        lemme: The noun lemma.
        genre: Gender - 'm', 'f', or 'm/f' for common gender.

    Returns:
        Formatted noun with appropriate article.
    """
    lemme = lemme.strip()

    if genre == "m":
        if starts_with_vowel(lemme):
            return f"l'{lemme} (m)"
        return f"le {lemme}"
    elif genre == "f":
        if starts_with_vowel(lemme):
            return f"l'{lemme} (f)"
        return f"la {lemme}"
    elif genre == "m/f":
        if starts_with_vowel(lemme):
            return f"l'{lemme} (m/f)"
        return f"le/la {lemme}"
    else:
        # Unknown gender
        return lemme


def format_adjective(lemme: str, forms: str, irregular_info: Optional[tuple[str, str, str]]) -> tuple[str, str]:
    """Format adjective with m/f forms. Returns (french, notes)."""
    lemme = lemme.strip()

    if irregular_info:
        form_m, form_f, pattern = irregular_info
        if form_m and form_f and form_m != form_f:
            return f"{form_m}, {form_f}", f"irrégulier ({pattern})"
        return lemme, "invariable"

    # Parse forms field: "petit/petite petits/petites" or "autre, autres"
    if "/" in forms:
        # Has m/f distinction
        parts = forms.split()
        if parts:
            first = parts[0]  # e.g., "petit/petite"
            if "/" in first:
                m, f = first.split("/", 1)
                if m != f:
                    return f"{m}, {f}", "+e au féminin" if f == m + "e" else ""
                return m, "invariable"

    # No m/f distinction or simple forms
    if "," in forms:
        base = forms.split(",")[0].strip()
        return base, "invariable"

    return lemme, ""


def classify_verb_group(lemme: str, irregular_info: Optional[tuple[str, str]]) -> tuple[str, str]:
    """Classify verb group. Returns (group, notes)."""
    lemme_lower = lemme.lower()

    if irregular_info:
        ending_type, notes = irregular_info
        return "3e groupe", notes

    # 1st group: -er (except aller)
    if lemme_lower == "aller":
        return "3e groupe", "irrégulier"

    if lemme_lower.endswith("er"):
        return "1er groupe", ""

    # 2nd group: -ir with -issant (need to check participe)
    # For now, assume regular -ir without info is 2nd group
    if lemme_lower.endswith("ir"):
        return "2e groupe", "vérifier participe (-issant)"

    # 3rd group: everything else
    return "3e groupe", ""


def pos_to_wordtype(pos: str) -> str:
    """Convert quebecisme POS to Anki WordType."""
    pos_lower = pos.lower().strip()

    # Masculine nouns (various formats)
    if re.search(r'\bn\.?\s*m\.?(?!\s*[/ou])', pos_lower):
        return "m"

    # Feminine nouns
    if re.search(r'\bn\.?\s*f\.?', pos_lower):
        return "f"

    # Common gender (m/f, m ou f)
    if re.search(r'\bn\.?\s*m\.?\s*[/ou]\s*f\.?', pos_lower):
        return "m/f"
    if re.search(r'\bnom\b', pos_lower) and not re.search(r'[mf]', pos_lower):
        return "m/f"

    # Verbs
    if re.search(r'\bv[ti]?\.?(?:\s|$)', pos_lower) or pos_lower.startswith("v"):
        return "v"

    # Adjectives
    if re.search(r'\badj\.?', pos_lower):
        return "adj"

    # Adverbs
    if re.search(r'\badv\.?', pos_lower):
        return "adv"

    # Locutions
    if re.search(r'\bloc\.?', pos_lower):
        return "loc"

    # Interjections
    if re.search(r'\binterj\.?', pos_lower):
        return "interj"

    # Expressions
    if re.search(r'\bexpr\.?', pos_lower):
        return "expr"

    return pos_lower if pos_lower else "?"


# =============================================================================
# Processors
# =============================================================================

def process_nouns(
    entries: list[dict],
    blacklist: set[str],
    professions_f: list[dict],
) -> list[VocabEntry]:
    """Process NOM category."""
    vocab = []
    seen = set()

    # Add regular nouns
    for row in entries:
        lemme = row["lemme"].strip()
        if lemme.lower() in blacklist:
            continue
        if lemme.lower() in seen:
            continue
        seen.add(lemme.lower())

        genre = row.get("genre", "").strip()
        freqlem = float(row.get("freqlem", 0) or 0)

        french = format_noun(lemme, genre)
        wordtype = "m" if genre == "m" else "f" if genre == "f" else "m/f"

        vocab.append(VocabEntry(
            french=french,
            wordtype=wordtype,
            freqlem=freqlem,
            source="lexique",
            cgram="NOM",
        ))

    # Add feminine profession forms
    for row in professions_f:
        lemme = row["lemme"].strip()
        if lemme.lower() in blacklist:
            continue
        if lemme.lower() in seen:
            continue
        seen.add(lemme.lower())

        freqlem = float(row.get("freqlem", 0) or 0)
        lemme_m = row.get("lemme_m", "")
        notes = row.get("notes", "")

        french = format_noun(lemme, "f")
        note_text = f"fém. de {lemme_m}" if lemme_m else notes

        vocab.append(VocabEntry(
            french=french,
            wordtype="f",
            notes=note_text,
            freqlem=freqlem,
            source="additions",
            cgram="NOM",
        ))

    return vocab


def process_adjectives(
    entries: list[dict],
    blacklist: set[str],
    irregular_adj: dict,
) -> list[VocabEntry]:
    """Process ADJ category."""
    vocab = []
    seen = set()

    for row in entries:
        lemme = row["lemme"].strip()
        if lemme.lower() in blacklist:
            continue
        if lemme.lower() in seen:
            continue
        seen.add(lemme.lower())

        forms = row.get("forms", "")
        freqlem = float(row.get("freqlem", 0) or 0)

        irregular_info = irregular_adj.get(lemme.lower())
        french, notes = format_adjective(lemme, forms, irregular_info)

        vocab.append(VocabEntry(
            french=french,
            wordtype="adj",
            notes=notes,
            freqlem=freqlem,
            source="lexique",
            cgram="ADJ",
        ))

    return vocab


def process_adverbs(entries: list[dict], blacklist: set[str]) -> list[VocabEntry]:
    """Process ADV category."""
    vocab = []
    seen = set()

    for row in entries:
        lemme = row["lemme"].strip()
        if lemme.lower() in blacklist:
            continue
        if lemme.lower() in seen:
            continue
        seen.add(lemme.lower())

        freqlem = float(row.get("freqlem", 0) or 0)

        vocab.append(VocabEntry(
            french=lemme,
            wordtype="adv",
            freqlem=freqlem,
            source="lexique",
            cgram="ADV",
        ))

    return vocab


def process_numerals(
    entries: list[dict],
    blacklist: set[str],
    whitelist: dict[str, str],
) -> list[VocabEntry]:
    """Process ADJ:num category with whitelist filtering."""
    vocab = []
    seen = set()

    for row in entries:
        lemme = row["lemme"].strip()
        lemme_lower = lemme.lower()

        # Only include whitelisted numerals
        if lemme_lower not in whitelist:
            continue
        if lemme_lower in blacklist:
            continue
        if lemme_lower in seen:
            continue
        seen.add(lemme_lower)

        freqlem = float(row.get("freqlem", 0) or 0)
        notes = whitelist.get(lemme_lower, "")

        vocab.append(VocabEntry(
            french=lemme,
            wordtype="num",
            notes=notes,
            freqlem=freqlem,
            source="lexique",
            cgram="ADJ:num",
        ))

    # Add whitelisted numerals not in Lexique (like dix-sept, etc.)
    for lemme, notes in whitelist.items():
        if lemme in seen:
            continue
        if lemme in blacklist:
            continue
        seen.add(lemme)

        vocab.append(VocabEntry(
            french=lemme,
            wordtype="num",
            notes=notes,
            freqlem=0,
            source="whitelist",
            cgram="ADJ:num",
        ))

    return vocab


def process_other(entries: list[dict], blacklist: set[str]) -> list[VocabEntry]:
    """Process 'other' category from Lexique383.

    Includes: ART (articles), PRO (pronouns), CON (conjunctions),
    PRE (prepositions), ART:def/ind, PRO:per/dem/rel/int, etc.
    """
    vocab = []
    seen = set()

    for row in entries:
        lemme = row["lemme"].strip()
        if lemme.lower() in blacklist:
            continue
        if lemme.lower() in seen:
            continue
        seen.add(lemme.lower())

        cgram = row.get("cgram", "")
        genre = row.get("genre", "")
        freqlem = float(row.get("freqlem", 0) or 0)

        wordtype = get_wordtype(cgram, genre)

        vocab.append(VocabEntry(
            french=lemme,
            wordtype=wordtype,
            freqlem=freqlem,
            source="lexique",
            cgram=cgram,
        ))

    return vocab


def process_onomatopoeia(entries: list[dict], blacklist: set[str]) -> list[VocabEntry]:
    """Process ONO (onomatopoeia/interjections) category."""
    vocab = []
    seen = set()

    for row in entries:
        lemme = row["lemme"].strip()
        if lemme.lower() in blacklist:
            continue
        if lemme.lower() in seen:
            continue
        seen.add(lemme.lower())

        freqlem = float(row.get("freqlem", 0) or 0)

        vocab.append(VocabEntry(
            french=lemme,
            wordtype="interj",
            freqlem=freqlem,
            source="lexique",
            cgram="ONO",
        ))

    return vocab


def process_verbs(
    entries: list[dict],
    blacklist: set[str],
    irregular_verbs: dict,
) -> list[ConjugationEntry]:
    """Process VER category for conjugation cards."""
    conj = []
    seen = set()

    for row in entries:
        lemme = row["lemme"].strip()
        if lemme.lower() in blacklist:
            continue
        if lemme.lower() in seen:
            continue
        seen.add(lemme.lower())

        freqlem = float(row.get("freqlem", 0) or 0)

        irregular_info = irregular_verbs.get(lemme.lower())
        group, notes = classify_verb_group(lemme, irregular_info)

        conj.append(ConjugationEntry(
            verb=lemme,
            notes=notes,
            freqlem=freqlem,
            group=group,
        ))

    return conj


def process_quebecismes(entries: list[dict], blacklist: set[str]) -> list[VocabEntry]:
    """Process quebecismes from additions."""
    vocab = []
    seen = set()

    for row in entries:
        word = row.get("word", "").strip()
        if not word:
            continue
        if word.lower() in blacklist:
            continue
        if word.lower() in seen:
            continue
        seen.add(word.lower())

        pos = row.get("pos", "")
        definition = row.get("definition", "")
        translation = row.get("translation", "")
        priority = row.get("priority", "medium")

        wordtype = pos_to_wordtype(pos)

        # For nouns, add article
        french = word
        if wordtype in ("m", "f", "m/f"):
            french = format_noun(word, wordtype)

        # Notes: combine definition preview
        notes = ""
        if definition:
            notes = definition[:80] + "..." if len(definition) > 80 else definition

        # Add translation to notes if available
        if translation:
            if notes:
                notes = f"{translation} | {notes}"
            else:
                notes = translation

        vocab.append(VocabEntry(
            french=french,
            wordtype=wordtype,
            notes=notes,
            source="quebecismes",
            freqlem=0,
            priority=priority,
        ))

    return vocab


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("GENERATE CARD SKELETONS")
    print("=" * 60)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load filters
    print("\nLoading filters...")
    blacklist = load_blacklist(BLACKLIST_PATH)
    print(f"  Blacklist: {len(blacklist)} entries")

    whitelist_num = load_whitelist_numerals(WHITELIST_NUMERALS_PATH)
    print(f"  Whitelist numerals: {len(whitelist_num)} entries")

    # Load reference data
    print("\nLoading reference data...")
    irregular_adj = load_irregular_adjectives(IRREGULAR_ADJ_PATH)
    print(f"  Irregular adjectives: {len(irregular_adj)} entries")

    irregular_verbs = load_irregular_verbs(IRREGULAR_VERBS_PATH)
    print(f"  Irregular verbs: {len(irregular_verbs)} entries")

    # Load additions
    print("\nLoading additions...")
    professions_f = load_professions_f(ADDITIONS_DIR / "professions_f.csv")
    print(f"  Professions (f): {len(professions_f)} entries")

    quebecismes = load_quebecismes(ADDITIONS_DIR / "quebecismes.csv")
    print(f"  Québécismes: {len(quebecismes)} entries")

    # ==========================================================================
    # Process Vocabulary
    # ==========================================================================
    print("\n" + "=" * 60)
    print("PROCESSING VOCABULARY")
    print("=" * 60)

    all_vocab: list[VocabEntry] = []

    # Nouns
    print("\nProcessing NOM...")
    nom_entries = load_category(CATEGORIES_DIR / "NOM.csv")
    nom_vocab = process_nouns(nom_entries, blacklist, professions_f)
    print(f"  NOM: {len(nom_vocab)} entries")
    all_vocab.extend(nom_vocab)

    # Adjectives
    print("\nProcessing ADJ...")
    adj_entries = load_category(CATEGORIES_DIR / "ADJ.csv")
    adj_vocab = process_adjectives(adj_entries, blacklist, irregular_adj)
    print(f"  ADJ: {len(adj_vocab)} entries")
    all_vocab.extend(adj_vocab)

    # Adverbs
    print("\nProcessing ADV...")
    adv_entries = load_category(CATEGORIES_DIR / "ADV.csv")
    adv_vocab = process_adverbs(adv_entries, blacklist)
    print(f"  ADV: {len(adv_vocab)} entries")
    all_vocab.extend(adv_vocab)

    # Numerals
    print("\nProcessing ADJ:num...")
    num_entries = load_category(CATEGORIES_DIR / "ADJ_num.csv")
    num_vocab = process_numerals(num_entries, blacklist, whitelist_num)
    print(f"  ADJ:num: {len(num_vocab)} entries")
    all_vocab.extend(num_vocab)

    # Other (determiners, pronouns)
    print("\nProcessing other...")
    other_entries = load_category(CATEGORIES_DIR / "other.csv")
    other_vocab = process_other(other_entries, blacklist)
    print(f"  other: {len(other_vocab)} entries")
    all_vocab.extend(other_vocab)

    # Onomatopoeia
    print("\nProcessing ONO...")
    ono_entries = load_category(CATEGORIES_DIR / "ONO.csv")
    ono_vocab = process_onomatopoeia(ono_entries, blacklist)
    print(f"  ONO: {len(ono_vocab)} entries")
    all_vocab.extend(ono_vocab)

    # Québécismes
    print("\nProcessing québécismes...")
    qc_vocab = process_quebecismes(quebecismes, blacklist)
    print(f"  québécismes: {len(qc_vocab)} entries")
    all_vocab.extend(qc_vocab)

    # Sort by frequency (descending)
    all_vocab.sort(key=lambda x: (-x.freqlem, x.french.lower()))

    print(f"\n  TOTAL vocabulary: {len(all_vocab)} entries")

    # ==========================================================================
    # Process Conjugation
    # ==========================================================================
    print("\n" + "=" * 60)
    print("PROCESSING CONJUGATION")
    print("=" * 60)

    print("\nProcessing VER...")
    ver_entries = load_category(CATEGORIES_DIR / "VER.csv")
    all_conj = process_verbs(ver_entries, blacklist, irregular_verbs)
    print(f"  VER: {len(all_conj)} entries")

    # Sort by frequency (descending)
    all_conj.sort(key=lambda x: (-x.freqlem, x.verb.lower()))

    # Group statistics
    groups = {}
    for c in all_conj:
        groups[c.group] = groups.get(c.group, 0) + 1
    print("\n  By group:")
    for g, count in sorted(groups.items()):
        print(f"    {g}: {count}")

    # ==========================================================================
    # Save Vocabulary Skeleton
    # ==========================================================================
    print("\n" + "=" * 60)
    print("SAVING OUTPUT")
    print("=" * 60)

    vocab_path = OUTPUT_DIR / "vocabulary_skeleton.csv"
    print(f"\nSaving vocabulary to {vocab_path}...")

    fieldnames = ["French", "WordType", "Notes", "Source", "freqlem", "Priority"]
    with open(vocab_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in all_vocab:
            writer.writerow(entry.to_row())

    print(f"  Saved {len(all_vocab)} entries")

    # ==========================================================================
    # Save Conjugation Skeleton
    # ==========================================================================
    conj_path = OUTPUT_DIR / "conjugation_skeleton.csv"
    print(f"\nSaving conjugation to {conj_path}...")

    fieldnames = ["Verb", "Notes", "freqlem", "Group"]
    with open(conj_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in all_conj:
            writer.writerow(entry.to_row())

    print(f"  Saved {len(all_conj)} entries")

    # ==========================================================================
    # Copy Expressions (already complete)
    # ==========================================================================
    expressions_src = DATA_DIR / "all_expressions.csv"
    expressions_dst = OUTPUT_DIR / "expressions.csv"
    expr_count = 0

    if expressions_src.exists():
        print(f"\nCopying expressions to {expressions_dst}...")
        shutil.copy(expressions_src, expressions_dst)

        # Count
        with open(expressions_dst, "r", encoding="utf-8") as f:
            expr_count = sum(1 for _ in f) - 1  # minus header
        print(f"  Copied {expr_count} expressions")
    else:
        print(f"\n  Warning: {expressions_src} not found")

    # ==========================================================================
    # Summary
    # ==========================================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"""
Output files in {OUTPUT_DIR}/:
  - vocabulary_skeleton.csv: {len(all_vocab)} entries
  - conjugation_skeleton.csv: {len(all_conj)} entries
  - expressions.csv: {expr_count if expressions_src.exists() else 0} entries (already complete)

Next steps:
  1. AI fill: add Russian, ExampleFrench, ExampleRussian, Emoji to vocabulary
  2. AI fill: generate conjugation tables for verbs
  3. Azure TTS: generate audio files
  4. Assembly: combine into final .apkg
""")


if __name__ == "__main__":
    main()
