#!/usr/bin/env python3
"""
04c_find_irregular_adj.py

Finds irregular adjectives in Lexique383.

Adjective types:
- regular: f = m + 'e' (petit → petite, grand → grande)
- invariable: m = f (rouge, possible, facile)
- irregular: f ≠ m + 'e' (beau → belle, vieux → vieille)

Output: data/irregular_adjectives.csv
"""

import pandas as pd
from config import (
    LEXIQUE_PATH,
    DATA_DIR,
    IRREGULAR_ADJ_PATH,
    FREQ_FILMS_WEIGHT,
    FREQ_BOOKS_WEIGHT,
    FREQ_MIN_THRESHOLD,
)


def get_adj_forms(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract m.sg and f.sg forms for each ADJ lemma.
    """
    adj = df[df['cgram'] == 'ADJ'].copy()

    # Get singular forms (nombre='s')
    m_sg = adj[(adj['genre'] == 'm') & (adj['nombre'] == 's')][['lemme', 'ortho']].copy()
    m_sg = m_sg.rename(columns={'ortho': 'form_m'})

    f_sg = adj[(adj['genre'] == 'f') & (adj['nombre'] == 's')][['lemme', 'ortho']].copy()
    f_sg = f_sg.rename(columns={'ortho': 'form_f'})

    # Invariable adjectives (genre=NaN, nombre='s')
    invariable = adj[adj['genre'].isna() & (adj['nombre'] == 's')][['lemme', 'ortho']].copy()
    invariable = invariable.rename(columns={'ortho': 'form_inv'})

    # Invariable adjectives with nombre=NaN (borrowed words like ok, super, cool)
    invariable_nan = adj[adj['genre'].isna() & adj['nombre'].isna()][['lemme', 'ortho']].copy()
    invariable_nan = invariable_nan.rename(columns={'ortho': 'form_inv_nan'})

    # Merge all
    forms = m_sg.merge(f_sg, on='lemme', how='outer')
    forms = forms.merge(invariable, on='lemme', how='outer')
    forms = forms.merge(invariable_nan, on='lemme', how='outer')

    # Fill missing: prefer form_inv, then form_inv_nan
    forms['form_inv'] = forms['form_inv'].fillna(forms['form_inv_nan'])
    forms['form_m'] = forms['form_m'].fillna(forms['form_inv'])
    forms['form_f'] = forms['form_f'].fillna(forms['form_inv'])

    return forms[['lemme', 'form_m', 'form_f']].drop_duplicates()


def classify_adjective(row: pd.Series) -> str:
    """
    Classify adjective as regular, invariable, or irregular.
    """
    m = row['form_m']
    f = row['form_f']

    if pd.isna(m) or pd.isna(f):
        return 'unknown'

    # Invariable: same form
    if m == f:
        return 'invariable'

    # Regular: f = m + 'e'
    if f == m + 'e':
        return 'regular'

    # Regular with doubled consonant: bon → bonne, gros → grosse
    if len(m) >= 1 and f == m + m[-1] + 'e':
        return 'regular_doubled'

    # Everything else is irregular
    return 'irregular'


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

    # Classify
    result['adj_type'] = result.apply(classify_adjective, axis=1)
    result['freqlem'] = result['freqlem'].round(2)
    result = result.sort_values('freqlem', ascending=False)

    # Stats
    print("\n=== Classification stats ===")
    print(result['adj_type'].value_counts().to_string())

    # Filter to irregular only
    irregular = result[result['adj_type'] == 'irregular'].copy()
    irregular = irregular[['lemme', 'form_m', 'form_f', 'freqlem']]
    irregular['notes'] = ''

    print(f"\n=== Irregular adjectives: {len(irregular)} ===")
    print(irregular.head(30).to_string(index=False))

    # Save
    irregular.to_csv(IRREGULAR_ADJ_PATH, index=False, encoding='utf-8')
    print(f"\nSaved to: {IRREGULAR_ADJ_PATH}")

    # Also show regular_doubled for reference
    doubled = result[result['adj_type'] == 'regular_doubled']
    print(f"\n=== Regular with doubled consonant: {len(doubled)} ===")
    print(doubled[['lemme', 'form_m', 'form_f', 'freqlem']].head(20).to_string(index=False))

    return 0


if __name__ == "__main__":
    exit(main())
