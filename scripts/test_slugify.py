"""
Pinned tests for slugify stability.

If slugify changes, existing audio files break. These tests lock down
the exact mapping for known words. If a test fails, you must also
migrate audio files (see 11_build_deck.py migration notes).

Usage:
    python scripts/test_slugify.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import slugify

# Pinned slug mappings — DO NOT change without migrating audio files
PINNED = {
    # Basic
    "une maison": "une_maison",
    "l'homme": "l_homme",
    "aujourd'hui": "aujourd_hui",
    # Accents preserved
    "être": "être",
    "dès": "dès",
    "là": "là",
    "où": "où",
    "tâche": "tâche",
    "tâcher": "tâcher",
    "ténu, ténue": "ténu_ténue",
    "un gradé": "un_gradé",
    "un mât": "un_mât",
    # Accents don't collide with non-accented
    "une tache": "une_tache",
    "tacher": "tacher",
    "la": "la",
    "des": "des",
    "ou": "ou",
    "un grade": "un_grade",
    "un mat": "un_mat",
    # Ligatures expand
    "cœur": "coeur",
    # Apostrophes
    "l\u2019eau": "l_eau",
    "quelqu'un": "quelqu_un",
    # Reserved Windows filenames
    "aux": "w_aux",
    "nul": "w_nul",
    "con": "w_con",
    # Cedilla preserved
    "français": "français",
    "ça": "ça",
    # Complex
    "allô": "allô",
    "allo": "allo",
    "tchin-tchin": "tchin_tchin",
}


def main():
    failed = 0
    for text, expected in PINNED.items():
        actual = slugify(text)
        if actual != expected:
            print(f"FAIL: slugify({text!r}) = {actual!r}, expected {expected!r}")
            failed += 1

    if failed:
        print(f"\n{failed}/{len(PINNED)} tests FAILED")
        sys.exit(1)
    else:
        print(f"All {len(PINNED)} slugify tests passed")


if __name__ == "__main__":
    main()
