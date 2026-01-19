#!/usr/bin/env python3
"""
04b_check_professions.py

Checks for m/f pairs in profession/person nouns.

In Lexique383, feminine forms are stored as `ortho` with the same `lemme`:
- lemme="acteur" has ortho: acteur (m.s), actrice (f.s), acteurs (m.p), actrices (f.p)

This script:
1. Finds NOM lemmas that have BOTH m.s. and f.s. forms (profession pairs)
2. Detects the morphological pattern (e.g., -teur → -trice)
3. Reports nouns that SHOULD have pairs but don't

Patterns for m → f transformation:
- -teur → -trice (acteur/actrice, directeur/directrice)
- -eur → -euse (chanteur/chanteuse, vendeur/vendeuse)
- -ier → -ière (boulanger/boulangère, infirmier/infirmière)
- -ien → -ienne (musicien/musicienne, pharmacien/pharmacienne)
- -er → -ère (étranger/étrangère)
- -ant → -ante (assistant/assistante)
- invariable: -iste (artiste, journaliste)

Output: data/professions_check.csv
"""

import sys
import pandas as pd

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from config import (
    LEXIQUE_PATH,
    DATA_DIR,
    PROFESSIONS_CHECK_PATH,
    FREQ_FILMS_WEIGHT,
    FREQ_BOOKS_WEIGHT,
    FREQ_MIN_THRESHOLD,
)


# Patterns: (m_suffix, f_suffix, pattern_name)
# Order matters: more specific patterns first
PROFESSION_PATTERNS = [
    ('teur', 'trice', '-teur → -trice'),
    ('eur', 'euse', '-eur → -euse'),
    ('ier', 'ière', '-ier → -ière'),
    ('ien', 'ienne', '-ien → -ienne'),
    ('er', 'ère', '-er → -ère'),
    ('ant', 'ante', '-ant → -ante'),
]

# Suffixes that indicate potential profession nouns (for filtering)
PROFESSION_SUFFIXES_M = ['teur', 'eur', 'ier', 'ien', 'er', 'ant', 'iste']


def detect_pattern(form_m: str, form_f: str) -> str:
    """Detect which pattern applies to m → f transformation."""
    if pd.isna(form_m) or pd.isna(form_f):
        return ''

    for m_suf, f_suf, pattern_name in PROFESSION_PATTERNS:
        if form_m.endswith(m_suf):
            expected_f = form_m[:-len(m_suf)] + f_suf
            if form_f == expected_f:
                return pattern_name

    # Check invariable (same form)
    if form_m == form_f:
        return 'invariable'

    return 'irregular'


def get_nom_forms(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract m.s and f.s forms for each NOM lemma.

    Returns DataFrame with: lemme, form_m, form_f
    """
    nom = df[df['cgram'] == 'NOM'].copy()

    # Get masculine singular forms
    m_sg = nom[(nom['genre'] == 'm') & (nom['nombre'] == 's')][['lemme', 'ortho']].copy()
    m_sg = m_sg.drop_duplicates(subset='lemme', keep='first')
    m_sg = m_sg.rename(columns={'ortho': 'form_m'})

    # Get feminine singular forms
    f_sg = nom[(nom['genre'] == 'f') & (nom['nombre'] == 's')][['lemme', 'ortho']].copy()
    f_sg = f_sg.drop_duplicates(subset='lemme', keep='first')
    f_sg = f_sg.rename(columns={'ortho': 'form_f'})

    # Merge
    forms = m_sg.merge(f_sg, on='lemme', how='outer')

    return forms


def main():
    if not LEXIQUE_PATH.exists():
        print(f"❌ File {LEXIQUE_PATH} not found!")
        return 1

    DATA_DIR.mkdir(exist_ok=True)

    # Load Lexique
    print("Loading Lexique383...")
    df = pd.read_csv(LEXIQUE_PATH, sep='\t', low_memory=False, encoding='utf-8')

    # Get lemma frequencies
    lemmas = df[df['islem'] == 1].copy()
    lemmas['freqlem'] = (
        FREQ_FILMS_WEIGHT * lemmas['freqlemfilms2'].fillna(0) +
        FREQ_BOOKS_WEIGHT * lemmas['freqlemlivres'].fillna(0)
    )

    nom_freq = lemmas[lemmas['cgram'] == 'NOM'][['lemme', 'freqlem']].copy()
    nom_freq = nom_freq[nom_freq['freqlem'] >= FREQ_MIN_THRESHOLD]

    print(f"NOM lemmas above threshold ({FREQ_MIN_THRESHOLD}): {len(nom_freq)}")

    # Get all forms (not just lemmas)
    forms = get_nom_forms(df)

    # Merge with frequency
    result = nom_freq.merge(forms, on='lemme', how='left')
    result = result[result['lemme'].notna()]

    # Classify each noun
    def classify(row):
        form_m = row['form_m']
        form_f = row['form_f']
        lemme = row['lemme']

        has_m = pd.notna(form_m)
        has_f = pd.notna(form_f)

        if has_m and has_f:
            pattern = detect_pattern(form_m, form_f)
            return 'has_both', pattern
        elif has_m and not has_f:
            # Check if it SHOULD have feminine (profession-like suffix)
            for suf in PROFESSION_SUFFIXES_M:
                if lemme.endswith(suf):
                    return 'm_only_profession', f'expected f-form (-{suf})'
            return 'm_only', ''
        elif has_f and not has_m:
            return 'f_only', ''
        else:
            return 'unknown', ''

    classifications = result.apply(classify, axis=1)
    result['status'] = classifications.apply(lambda x: x[0])
    result['pattern'] = classifications.apply(lambda x: x[1])
    result['freqlem'] = result['freqlem'].round(2)

    # Stats
    print("\n" + "=" * 60)
    print("📊 CLASSIFICATION STATISTICS")
    print("=" * 60)
    print(result['status'].value_counts().to_string())

    # Professions with both forms
    has_both = result[result['status'] == 'has_both'].copy()
    has_both = has_both.sort_values('freqlem', ascending=False)

    print(f"\n{'=' * 60}")
    print(f"👥 NOUNS WITH BOTH M/F FORMS: {len(has_both)}")
    print("=" * 60)

    print("\nPattern distribution:")
    print(has_both['pattern'].value_counts().to_string())

    print("\n--- Top 40 by frequency ---")
    cols = ['lemme', 'form_m', 'form_f', 'freqlem', 'pattern']
    print(has_both[cols].head(40).to_string(index=False))

    # Potential professions missing f-form
    m_only_prof = result[result['status'] == 'm_only_profession'].copy()
    m_only_prof = m_only_prof.sort_values('freqlem', ascending=False)

    print(f"\n{'=' * 60}")
    print(f"⚠️  M-ONLY WITH PROFESSION SUFFIX (may need review): {len(m_only_prof)}")
    print("=" * 60)

    print("\n--- Top 30 by frequency ---")
    cols = ['lemme', 'form_m', 'freqlem', 'pattern']
    print(m_only_prof[cols].head(30).to_string(index=False))

    # Save results - only profession-related
    output = pd.concat([has_both, m_only_prof])
    output = output.sort_values(['status', 'freqlem'], ascending=[True, False])
    output = output[['lemme', 'form_m', 'form_f', 'freqlem', 'status', 'pattern']]
    output.to_csv(PROFESSIONS_CHECK_PATH, index=False, encoding='utf-8')
    print(f"\n✅ Saved to: {PROFESSIONS_CHECK_PATH}")

    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY FOR ANKI CARDS")
    print("=" * 60)

    # Count by pattern for has_both
    pattern_counts = has_both['pattern'].value_counts()

    print(f"""
Nouns with both m/f forms: {len(has_both)}
  → Create 2 cards each (un acteur / une actrice)

Pattern breakdown:""")

    for pattern, count in pattern_counts.items():
        examples = has_both[has_both['pattern'] == pattern]['lemme'].head(3).tolist()
        print(f"  {pattern}: {count} ({', '.join(examples)}...)")

    print(f"""
M-only with profession suffix: {len(m_only_prof)}
  → Review: some may be objects, not people (ordinateur, ventilateur)
""")

    return 0


if __name__ == "__main__":
    exit(main())
