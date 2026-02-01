#!/usr/bin/env python3
"""Fix missing WordType in autres.csv by looking up from skeleton."""

import pandas as pd
from pathlib import Path
import re

CONTENT_DIR = Path(__file__).parent.parent / "content" / "vocabulary"
SKELETON_PATH = Path(__file__).parent.parent / "output" / "vocabulary_skeleton.csv"

# Manual fixes for words not in skeleton
MANUAL_WORDTYPE = {
    "non": "adv",
    "ou": "conj",
    "précis": "adj",
    "principal": "adj",
    "supérieur": "adj",
    "matière": "f",
    "autrefois": "adv",
    "complet": "adj",
    "futur": "adj",
    "tranquillité": "f",
    "con, conne": "adj",
    "nouveau": "adj",
    "las, lasse": "adj",
    "tendu, tendue": "adj",
    "complémentaire": "adj",
    "exécrable": "adj",
    "râper": "v",
    "hardi, hardie": "adj",
    "navrant, navrante": "adj",
    "tripler": "v",
    "bramer": "v",
    "pardi": "interj",
    "ici-bas": "adv",
    "parbleu": "interj",
    "sapristi": "interj",
    "dame": "interj",
    "fichtre": "interj",
    "Mme": "f",
    "Mlle": "f",
    "monseigneur": "m",
    "quant": "adv",
    "un boche": "m",
    "les cieux": "m",
    "Virginie": "f",
    "go": "interj",
    "Noël": "m",
    "Notre-Dame": "f",
    "mesdemoiselles": "f",
    "des chips": "f",
}

def normalize_french(text: str) -> str:
    """Normalize French text for matching."""
    if pd.isna(text):
        return ""
    text = str(text).strip().lower()
    # Remove quotes
    text = text.strip('"\'')
    return text

def infer_wordtype(french: str) -> str | None:
    """Infer WordType from French field patterns."""
    french = str(french).strip()

    # Reflexive verbs
    if french.startswith("s'") or french.startswith("se "):
        return "v"

    # Nouns with articles
    if french.startswith("un ") or french.startswith("l'") and "(m)" in french:
        return "m"
    if french.startswith("une ") or french.startswith("l'") and "(f)" in french:
        return "f"

    # Days of week (masculine)
    days = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    if french.lower() in days:
        return "m"

    # Months (masculine)
    months = ["janvier", "février", "mars", "avril", "mai", "juin",
              "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    if french.lower() in months:
        return "m"

    # Common adjective patterns
    adj_endings = ["eux", "eux, euse", "ant", "ant, ante", "ent", "ent, ente",
                   "ieux", "ieux, ieuse", "if", "if, ive"]
    for ending in adj_endings:
        if french.endswith(ending):
            return "adj"

    return None

def main():
    # Load skeleton
    skeleton = pd.read_csv(SKELETON_PATH)
    skeleton_lookup = {}
    for _, row in skeleton.iterrows():
        key = normalize_french(row['French'])
        if key and pd.notna(row.get('WordType')):
            skeleton_lookup[key] = row['WordType']

    print(f"Loaded {len(skeleton_lookup)} entries from skeleton")

    # Load autres.csv
    autres_path = CONTENT_DIR / "autres.csv"
    autres = pd.read_csv(autres_path)

    # Find empty WordType
    empty_mask = autres['WordType'].isna() | (autres['WordType'] == '')
    empty_count = empty_mask.sum()
    print(f"Found {empty_count} entries with empty WordType")

    # Fix each empty entry
    fixed = 0
    not_found = []

    for idx in autres[empty_mask].index:
        french = autres.loc[idx, 'French']
        key = normalize_french(french)

        # Try manual lookup first (exact match)
        if french in MANUAL_WORDTYPE:
            autres.loc[idx, 'WordType'] = MANUAL_WORDTYPE[french]
            fixed += 1
            continue

        # Try skeleton lookup
        if key in skeleton_lookup:
            autres.loc[idx, 'WordType'] = skeleton_lookup[key]
            fixed += 1
            continue

        # Try inference
        inferred = infer_wordtype(french)
        if inferred:
            autres.loc[idx, 'WordType'] = inferred
            fixed += 1
            continue

        not_found.append(french)

    print(f"Fixed {fixed} entries")
    print(f"Could not fix {len(not_found)} entries:")
    for word in not_found[:30]:
        print(f"  - {word}")
    if len(not_found) > 30:
        print(f"  ... and {len(not_found) - 30} more")

    # Save
    autres.to_csv(autres_path, index=False)
    print(f"\nSaved to {autres_path}")

    # Verify
    autres_check = pd.read_csv(autres_path)
    remaining = (autres_check['WordType'].isna() | (autres_check['WordType'] == '')).sum()
    print(f"Remaining empty WordType: {remaining}")

if __name__ == "__main__":
    main()
