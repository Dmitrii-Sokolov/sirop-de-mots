#!/usr/bin/env python3
"""
04c_find_irregular_adj.py

Finds irregular adjectives in Lexique383 and classifies them by pattern.

Adjective types:
- regular: f = m + 'e' (petit → petite, grand → grande)
- invariable: m = f (rouge, possible, facile)
- doubled: f = m + last_char + 'e' (bon → bonne, gros → grosse)
- patterned: follows a known pattern (-if → -ive, -er → -ère, etc.)
- unique: truly irregular, must be memorized

Output: data/irregular_adjectives.csv with pattern in notes column
"""

import sys
import pandas as pd

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from config import (
    LEXIQUE_PATH,
    DATA_DIR,
    IRREGULAR_ADJ_PATH,
    FREQ_FILMS_WEIGHT,
    FREQ_BOOKS_WEIGHT,
    FREQ_MIN_THRESHOLD,
)


# Pattern definitions: (suffix_m, suffix_f, pattern_name)
# Order matters: more specific patterns first
PATTERNS = [
    # -eux → -euse (most common irregular)
    ('eux', 'euse', '-eux → -euse'),
    # -if → -ive
    ('if', 'ive', '-if → -ive'),
    # -er → -ère (with accent)
    ('er', 'ère', '-er → -ère'),
    # -eur → -euse (not -teur)
    ('eur', 'euse', '-eur → -euse'),
    # -teur → -trice
    ('teur', 'trice', '-teur → -trice'),
    # -et → -ète
    ('et', 'ète', '-et → -ète'),
    # -f → -ve (not -if, checked after -if)
    ('f', 've', '-f → -ve'),
    # -eau → -elle
    ('eau', 'elle', '-eau → -elle'),
    # -c → -che
    ('c', 'che', '-c → -che'),
    # -c → -que (checked after -che)
    ('c', 'que', '-c → -que'),
    # -gu → -guë
    ('gu', 'guë', '-gu → -guë'),
    # -gu → -gue (without diaeresis)
    ('gu', 'gue', '-gu → -guë'),
    # -ou → -olle
    ('ou', 'olle', '-ou → -olle'),
    # -in → -igne
    ('in', 'igne', '-in → -igne'),
    # -x → -se (jaloux → jalouse, not -eux)
    ('x', 'se', '-x → -se'),
    # -ong → -ongue (long → longue)
    ('ong', 'ongue', '-ong → -ongue'),
]


def detect_pattern(m: str, f: str) -> str | None:
    """
    Detect which pattern applies to m → f transformation.
    Returns pattern name or None if no pattern matches.
    """
    if pd.isna(m) or pd.isna(f):
        return None

    for suffix_m, suffix_f, pattern_name in PATTERNS:
        if m.endswith(suffix_m):
            expected_f = m[:-len(suffix_m)] + suffix_f
            if f == expected_f:
                return pattern_name

    return None


# Liaison forms to skip (they're separate lemmas but variants of other adjectives)
LIAISON_FORMS = {'bel', 'vieil', 'nouvel', 'fol', 'mol'}

# Compound lemma mappings (Lexique383 stores some forms with compound lemmas)
COMPOUND_LEMMA_MAP = {
    'mou,mol': 'mou',  # molle, molles → mou
}


def get_adj_forms(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract m.sg and f.sg forms for each ADJ lemma.

    Handles special cases:
    - nombre=NaN for masculine (vieux, frais, héros)
    - Feminine forms only in NOM category (nouveau/nouvelle)
    - Compound lemmas (mou,mol → mou)
    - Skips liaison forms (bel, vieil, nouvel, fol, mol)
    """
    adj = df[df['cgram'] == 'ADJ'].copy()

    # Skip liaison forms (they're variants, not separate adjectives)
    adj = adj[~adj['lemme'].isin(LIAISON_FORMS)]

    # Normalize compound lemmas
    adj['lemme_norm'] = adj['lemme'].map(COMPOUND_LEMMA_MAP).fillna(adj['lemme'])

    # Get masculine singular forms
    # Include nombre='s' AND nombre=NaN (for vieux, frais, héros, etc.)
    m_sg_s = adj[(adj['genre'] == 'm') & (adj['nombre'] == 's')][['lemme_norm', 'ortho']].copy()
    m_sg_nan = adj[(adj['genre'] == 'm') & adj['nombre'].isna()][['lemme_norm', 'ortho']].copy()
    m_sg = pd.concat([m_sg_s, m_sg_nan]).drop_duplicates(subset='lemme_norm', keep='first')
    m_sg = m_sg.rename(columns={'lemme_norm': 'lemme', 'ortho': 'form_m'})

    # Get feminine singular forms from ADJ
    f_sg_adj = adj[(adj['genre'] == 'f') & (adj['nombre'] == 's')][['lemme_norm', 'ortho']].copy()
    f_sg_adj = f_sg_adj.rename(columns={'lemme_norm': 'lemme', 'ortho': 'form_f'})

    # Fallback: get feminine forms from NOM for adjectives missing in ADJ
    # (nouveau/nouvelle, etc.)
    nom = df[df['cgram'] == 'NOM'].copy()
    f_sg_nom = nom[(nom['genre'] == 'f') & (nom['nombre'] == 's')][['lemme', 'ortho']].copy()
    f_sg_nom = f_sg_nom.rename(columns={'ortho': 'form_f_nom'})

    # Invariable adjectives (genre=NaN, nombre='s')
    invariable = adj[adj['genre'].isna() & (adj['nombre'] == 's')][['lemme_norm', 'ortho']].copy()
    invariable = invariable.rename(columns={'lemme_norm': 'lemme', 'ortho': 'form_inv'})

    # Invariable adjectives with nombre=NaN (borrowed words like ok, super, cool)
    invariable_nan = adj[adj['genre'].isna() & adj['nombre'].isna()][['lemme_norm', 'ortho']].copy()
    invariable_nan = invariable_nan.rename(columns={'lemme_norm': 'lemme', 'ortho': 'form_inv_nan'})

    # Merge all
    forms = m_sg.merge(f_sg_adj, on='lemme', how='outer')
    forms = forms.merge(f_sg_nom, on='lemme', how='outer')
    forms = forms.merge(invariable, on='lemme', how='outer')
    forms = forms.merge(invariable_nan, on='lemme', how='outer')

    # Fill missing:
    # 1. form_inv_nan → form_inv
    forms['form_inv'] = forms['form_inv'].fillna(forms['form_inv_nan'])
    # 2. form_inv → form_m
    forms['form_m'] = forms['form_m'].fillna(forms['form_inv'])
    # 3. form_f_nom → form_f (fallback to NOM for feminine)
    forms['form_f'] = forms['form_f'].fillna(forms['form_f_nom'])
    forms['form_f'] = forms['form_f'].fillna(forms['form_inv'])

    return forms[['lemme', 'form_m', 'form_f']].drop_duplicates()


def classify_adjective(row: pd.Series) -> tuple[str, str]:
    """
    Classify adjective and detect pattern.
    Returns (adj_type, pattern_or_empty).
    """
    m = row['form_m']
    f = row['form_f']

    if pd.isna(m) or pd.isna(f):
        return 'unknown', ''

    # Invariable: same form
    if m == f:
        return 'invariable', ''

    # Regular: f = m + 'e'
    if f == m + 'e':
        return 'regular', ''

    # Regular with doubled consonant: bon → bonne, gros → grosse
    if len(m) >= 1 and f == m + m[-1] + 'e':
        return 'doubled', ''

    # Check for known patterns
    pattern = detect_pattern(m, f)
    if pattern:
        return 'patterned', pattern

    # Truly irregular
    return 'unique', 'unique'


def main():
    if not LEXIQUE_PATH.exists():
        print(f"File {LEXIQUE_PATH} not found!")
        return 1

    DATA_DIR.mkdir(exist_ok=True)

    # Load Lexique
    df = pd.read_csv(LEXIQUE_PATH, sep='\t', low_memory=False, encoding='utf-8')

    # Get lemmas with frequency
    lemmas = df[df['islem'] == 1].copy()
    lemmas['freqlem'] = (
        FREQ_FILMS_WEIGHT * lemmas['freqlemfilms2'].fillna(0) +
        FREQ_BOOKS_WEIGHT * lemmas['freqlemlivres'].fillna(0)
    )

    adj_lemmas = lemmas[lemmas['cgram'] == 'ADJ'][['lemme', 'freqlem']].copy()

    # Filter by threshold
    adj_lemmas = adj_lemmas[adj_lemmas['freqlem'] >= FREQ_MIN_THRESHOLD]
    print(f"ADJ lemmas above threshold ({FREQ_MIN_THRESHOLD}): {len(adj_lemmas)}")

    # Get forms
    forms = get_adj_forms(df)

    # Merge with frequency
    result = adj_lemmas.merge(forms, on='lemme', how='left')

    # Classify with pattern detection
    classifications = result.apply(classify_adjective, axis=1)
    result['adj_type'] = classifications.apply(lambda x: x[0])
    result['pattern'] = classifications.apply(lambda x: x[1])
    result['freqlem'] = result['freqlem'].round(2)
    result = result.sort_values('freqlem', ascending=False)

    # Stats
    print("\n=== Classification stats ===")
    print(result['adj_type'].value_counts().to_string())

    # Pattern stats for patterned adjectives
    patterned = result[result['adj_type'] == 'patterned']
    print(f"\n=== Pattern distribution ({len(patterned)} patterned) ===")
    print(patterned['pattern'].value_counts().to_string())

    # Unique (truly irregular)
    unique = result[result['adj_type'] == 'unique']
    print(f"\n=== Unique (truly irregular): {len(unique)} ===")
    print(unique[['lemme', 'form_m', 'form_f', 'freqlem']].to_string(index=False))

    # Combine patterned + unique for output
    irregular = result[result['adj_type'].isin(['patterned', 'unique'])].copy()
    irregular = irregular[['lemme', 'form_m', 'form_f', 'freqlem', 'pattern']]
    irregular = irregular.rename(columns={'pattern': 'notes'})

    print(f"\n=== All irregular adjectives: {len(irregular)} ===")
    print(irregular.head(30).to_string(index=False))

    # Save
    irregular.to_csv(IRREGULAR_ADJ_PATH, index=False, encoding='utf-8')
    print(f"\nSaved to: {IRREGULAR_ADJ_PATH}")

    # Summary by pattern
    print("\n=== Summary for Anki ===")
    print("Patterns to teach as rules:")
    for pattern_name in patterned['pattern'].value_counts().index:
        count = len(patterned[patterned['pattern'] == pattern_name])
        examples = patterned[patterned['pattern'] == pattern_name]['lemme'].head(3).tolist()
        print(f"  {pattern_name}: {count} words ({', '.join(examples)}...)")
    print(f"\nUnique (memorize individually): {len(unique)} words")

    return 0


if __name__ == "__main__":
    exit(main())
