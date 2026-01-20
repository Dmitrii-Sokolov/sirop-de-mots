"""
Generate restructured conjugation card skeletons.

Based on pattern analysis: instead of 8 tenses × 2088 verbs = 16700 cards,
we generate ~370 focused cards covering what actually needs memorization.

Outputs (in output/):
    - conj_present_skeleton.csv — Présent for 3e groupe + samples (255)
    - conj_subjonctif_skeleton.csv — Irregular subjonctif (10)
    - conj_participes_skeleton.csv — Irregular participes passés (60)
    - conj_futur_stems_skeleton.csv — Irregular futur stems (25)
    - conj_etre_verbs_skeleton.csv — DR MRS VANDERTRAMP verbs (17)
"""

import csv
from pathlib import Path
from dataclasses import dataclass

from config import (
    PROJECT_ROOT, CATEGORIES_DIR, OUTPUT_DIR, IRREGULAR_VERBS_PATH,
    SAMPLE_1ER_GROUPE, SAMPLE_2E_GROUPE, ETRE_VERBS,
    SUBJONCTIF_IRREGULIERS, FUTUR_STEMS, PARTICIPES_IRREGULIERS,
)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PresentEntry:
    """Présent conjugation card."""
    verb: str
    group: str
    pattern: str = ""
    freqlem: float = 0.0

    def to_row(self) -> dict:
        return {
            "Verb": self.verb,
            "Group": self.group,
            "Pattern": self.pattern,
            "freqlem": f"{self.freqlem:.2f}",
        }


@dataclass
class SubjonctifEntry:
    """Subjonctif présent card (irregular only)."""
    verb: str
    freqlem: float = 0.0

    def to_row(self) -> dict:
        return {
            "Verb": self.verb,
            "freqlem": f"{self.freqlem:.2f}",
        }


@dataclass
class ParticipeEntry:
    """Participe passé card (irregular only)."""
    verb: str
    participe: str
    auxiliaire: str
    pattern: str
    related: str = ""
    freqlem: float = 0.0

    def to_row(self) -> dict:
        return {
            "Verb": self.verb,
            "Participe": self.participe,
            "Auxiliaire": self.auxiliaire,
            "Pattern": self.pattern,
            "Related": self.related,
            "freqlem": f"{self.freqlem:.2f}",
        }


@dataclass
class FuturStemEntry:
    """Futur/Conditionnel stem card (irregular only)."""
    verb: str
    stem: str
    freqlem: float = 0.0

    def to_row(self) -> dict:
        return {
            "Verb": self.verb,
            "FuturStem": self.stem,
            "freqlem": f"{self.freqlem:.2f}",
        }


@dataclass
class EtreVerbEntry:
    """Être auxiliary verb card."""
    verb: str
    participe: str = ""
    freqlem: float = 0.0

    def to_row(self) -> dict:
        return {
            "Verb": self.verb,
            "Participe": self.participe,
            "freqlem": f"{self.freqlem:.2f}",
        }


# =============================================================================
# Loaders
# =============================================================================

def load_verbs_from_category() -> dict[str, tuple[float, str]]:
    """Load verbs from VER.csv. Returns verb -> (freqlem, notes)."""
    path = CATEGORIES_DIR / "VER.csv"
    verbs = {}

    if not path.exists():
        print(f"  Warning: {path} not found")
        return verbs

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lemme = row["lemme"].strip().lower()
            freqlem = float(row.get("freqlem", 0) or 0)
            verbs[lemme] = (freqlem, "")

    return verbs


def load_irregular_verbs() -> dict[str, str]:
    """Load irregular verbs with their patterns. Returns verb -> pattern."""
    path = IRREGULAR_VERBS_PATH
    irregulars = {}

    if not path.exists():
        print(f"  Warning: {path} not found")
        return irregulars

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lemme = row["lemme"].strip().lower()
            ending = row.get("ending_type", "")
            notes = row.get("notes", "")
            pattern = f"{ending} ({notes})" if notes else ending
            irregulars[lemme] = pattern

    return irregulars


# =============================================================================
# Generators
# =============================================================================

def generate_present_entries(
    verbs: dict[str, tuple[float, str]],
    irregular_patterns: dict[str, str],
) -> list[PresentEntry]:
    """Generate Présent entries for 3e groupe + samples."""
    entries = []
    seen = set()

    # 1. Add 3e groupe verbs (irregular)
    for verb, pattern in irregular_patterns.items():
        if verb in seen:
            continue
        seen.add(verb)

        freqlem = verbs.get(verb, (0.0, ""))[0]
        entries.append(PresentEntry(
            verb=verb,
            group="3e groupe",
            pattern=pattern,
            freqlem=freqlem,
        ))

    # 2. Add sample 1er groupe
    for verb in SAMPLE_1ER_GROUPE:
        if verb in seen:
            continue
        seen.add(verb)

        freqlem = verbs.get(verb, (0.0, ""))[0]
        pattern = "-er régulier"
        if verb == "manger":
            pattern = "-ger (nous mangeons)"
        elif verb == "commencer":
            pattern = "-cer (nous commençons)"

        entries.append(PresentEntry(
            verb=verb,
            group="1er groupe",
            pattern=pattern,
            freqlem=freqlem,
        ))

    # 3. Add sample 2e groupe
    for verb in SAMPLE_2E_GROUPE:
        if verb in seen:
            continue
        seen.add(verb)

        freqlem = verbs.get(verb, (0.0, ""))[0]
        entries.append(PresentEntry(
            verb=verb,
            group="2e groupe",
            pattern="-ir/-issant régulier",
            freqlem=freqlem,
        ))

    # Sort by frequency
    entries.sort(key=lambda x: (-x.freqlem, x.verb))
    return entries


def generate_subjonctif_entries(
    verbs: dict[str, tuple[float, str]],
) -> list[SubjonctifEntry]:
    """Generate Subjonctif entries for irregular verbs only."""
    entries = []

    for verb in SUBJONCTIF_IRREGULIERS:
        freqlem = verbs.get(verb, (0.0, ""))[0]
        entries.append(SubjonctifEntry(verb=verb, freqlem=freqlem))

    entries.sort(key=lambda x: (-x.freqlem, x.verb))
    return entries


def generate_participe_entries(
    verbs: dict[str, tuple[float, str]],
) -> list[ParticipeEntry]:
    """Generate Participe passé entries for irregular verbs."""
    entries = []
    etre_set = set(ETRE_VERBS)

    for verb, (participe, pattern, related) in PARTICIPES_IRREGULIERS.items():
        freqlem = verbs.get(verb, (0.0, ""))[0]
        auxiliaire = "être" if verb in etre_set else "avoir"

        entries.append(ParticipeEntry(
            verb=verb,
            participe=participe,
            auxiliaire=auxiliaire,
            pattern=pattern,
            related=related,
            freqlem=freqlem,
        ))

    entries.sort(key=lambda x: (-x.freqlem, x.verb))
    return entries


def generate_futur_stem_entries(
    verbs: dict[str, tuple[float, str]],
) -> list[FuturStemEntry]:
    """Generate Futur stem entries for irregular verbs."""
    entries = []

    for verb, stem in FUTUR_STEMS.items():
        freqlem = verbs.get(verb, (0.0, ""))[0]
        entries.append(FuturStemEntry(verb=verb, stem=stem, freqlem=freqlem))

    entries.sort(key=lambda x: (-x.freqlem, x.verb))
    return entries


def generate_etre_verb_entries(
    verbs: dict[str, tuple[float, str]],
) -> list[EtreVerbEntry]:
    """Generate être auxiliary verb entries."""
    entries = []

    for verb in ETRE_VERBS:
        freqlem = verbs.get(verb, (0.0, ""))[0]

        # Get participe from PARTICIPES_IRREGULIERS if available
        participe = ""
        if verb in PARTICIPES_IRREGULIERS:
            participe = PARTICIPES_IRREGULIERS[verb][0]
        elif verb.endswith("er"):
            participe = verb[:-2] + "é"
        elif verb.endswith("ir"):
            participe = verb[:-2] + "i"

        entries.append(EtreVerbEntry(
            verb=verb,
            participe=participe,
            freqlem=freqlem,
        ))

    entries.sort(key=lambda x: (-x.freqlem, x.verb))
    return entries


# =============================================================================
# Writers
# =============================================================================

def write_csv(path: Path, entries: list, fieldnames: list[str]) -> int:
    """Write entries to CSV file."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry.to_row())
    return len(entries)


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("GENERATE CONJUGATION SKELETONS (restructured)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    print("\nLoading data...")
    verbs = load_verbs_from_category()
    print(f"  Verbs from VER.csv: {len(verbs)}")

    irregular_patterns = load_irregular_verbs()
    print(f"  Irregular verbs (3e groupe): {len(irregular_patterns)}")

    # Generate entries
    print("\nGenerating entries...")

    present = generate_present_entries(verbs, irregular_patterns)
    print(f"  Présent: {len(present)} entries")

    subjonctif = generate_subjonctif_entries(verbs)
    print(f"  Subjonctif: {len(subjonctif)} entries")

    participes = generate_participe_entries(verbs)
    print(f"  Participes: {len(participes)} entries")

    futur_stems = generate_futur_stem_entries(verbs)
    print(f"  Futur stems: {len(futur_stems)} entries")

    etre_verbs = generate_etre_verb_entries(verbs)
    print(f"  Être verbs: {len(etre_verbs)} entries")

    # Write skeletons
    print("\nWriting skeletons to output/...")

    path = OUTPUT_DIR / "conj_present_skeleton.csv"
    count = write_csv(path, present, ["Verb", "Group", "Pattern", "freqlem"])
    print(f"  {path.name}: {count} entries")

    path = OUTPUT_DIR / "conj_subjonctif_skeleton.csv"
    count = write_csv(path, subjonctif, ["Verb", "freqlem"])
    print(f"  {path.name}: {count} entries")

    path = OUTPUT_DIR / "conj_participes_skeleton.csv"
    count = write_csv(path, participes, ["Verb", "Participe", "Auxiliaire", "Pattern", "Related", "freqlem"])
    print(f"  {path.name}: {count} entries")

    path = OUTPUT_DIR / "conj_futur_stems_skeleton.csv"
    count = write_csv(path, futur_stems, ["Verb", "FuturStem", "freqlem"])
    print(f"  {path.name}: {count} entries")

    path = OUTPUT_DIR / "conj_etre_verbs_skeleton.csv"
    count = write_csv(path, etre_verbs, ["Verb", "Participe", "freqlem"])
    print(f"  {path.name}: {count} entries")

    # Summary
    total = len(present) + len(subjonctif) + len(participes) + len(futur_stems) + len(etre_verbs)
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"""
New conjugation skeletons in output/:
  - conj_present_skeleton.csv: {len(present)} entries
  - conj_subjonctif_skeleton.csv: {len(subjonctif)} entries
  - conj_participes_skeleton.csv: {len(participes)} entries
  - conj_futur_stems_skeleton.csv: {len(futur_stems)} entries
  - conj_etre_verbs_skeleton.csv: {len(etre_verbs)} entries

TOTAL: {total} cards (vs ~16700 in old structure = 95% reduction)

Next steps:
  1. AI fill translations + cloze forms in content/conjugation/
  2. Delete old output/conjugation_skeleton.csv
""")


if __name__ == "__main__":
    main()
