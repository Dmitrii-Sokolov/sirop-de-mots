#!/usr/bin/env python3
"""
Count lemmas by grammatical category in Lexique383
with gender and number distribution.

Usage:
    python count_lemma_types.py
"""

import pandas as pd
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError

LEXIQUE_URL = "http://www.lexique.org/databases/Lexique383/Lexique383.tsv"
LEXIQUE_PATH = Path("Lexique383.tsv")
OUTPUT_PATH = Path("lemma_type_stats.csv")


def download_lexique():
    """Download Lexique383.tsv if not present."""
    print(f"Downloading {LEXIQUE_PATH}...")
    try:
        urlretrieve(LEXIQUE_URL, LEXIQUE_PATH)
        print(f"Downloaded: {LEXIQUE_PATH} ({LEXIQUE_PATH.stat().st_size / 1024 / 1024:.1f} MB)\n")
        return True
    except URLError as e:
        print(f"Download failed: {e}")
        return False


CGRAM_NAMES = {
    'NOM': 'Noun',
    'VER': 'Verb',
    'ADJ': 'Adjective',
    'ADV': 'Adverb',
    'PRE': 'Preposition',
    'CON': 'Conjunction',
    'PRO': 'Pronoun',
    'ART': 'Article',
    'AUX': 'Auxiliary verb',
    'ONO': 'Interjection',
    'LIA': 'Liaison',
    'ADJ:num': 'Numeral adjective',
    'ADJ:ind': 'Indefinite adjective',
    'ADJ:pos': 'Possessive adjective',
    'ADJ:dem': 'Demonstrative adjective',
    'ADJ:int': 'Interrogative adjective',
    'PRO:per': 'Personal pronoun',
    'PRO:ind': 'Indefinite pronoun',
    'PRO:pos': 'Possessive pronoun',
    'PRO:dem': 'Demonstrative pronoun',
    'PRO:rel': 'Relative pronoun',
    'PRO:int': 'Interrogative pronoun',
    'ART:def': 'Definite article',
    'ART:ind': 'Indefinite article',
}


def count_distribution(series, valid_values):
    """Count occurrences of valid values and 'unspecified'."""
    counts = {}
    for val in valid_values:
        counts[val] = (series == val).sum()
    counts['na'] = series.isna().sum() + (~series.isin(valid_values)).sum()
    return counts


def main():
    if not LEXIQUE_PATH.exists():
        if not download_lexique():
            return

    # 1. Load
    df = pd.read_csv(
        LEXIQUE_PATH,
        sep='\t',
        usecols=['lemme', 'cgram', 'islem', 'genre', 'nombre'],
        low_memory=False
    )
    print(f"Loaded {len(df):,} records\n")

    # 2. Filter islem == 1
    lemmas = df[df['islem'] == 1].copy()
    print(f"Lemmas (islem=1): {len(lemmas):,}\n")

    # 3. Count by cgram with gender/number distribution
    results = []
    for cgram in lemmas['cgram'].value_counts().index:
        subset = lemmas[lemmas['cgram'] == cgram]
        count = len(subset)

        # Gender distribution
        gender = count_distribution(subset['genre'], ['m', 'f'])

        # Number distribution
        number = count_distribution(subset['nombre'], ['s', 'p'])

        results.append({
            'cgram': cgram,
            'name': CGRAM_NAMES.get(cgram, cgram),
            'count': count,
            'genre_m': gender['m'],
            'genre_f': gender['f'],
            'genre_na': gender['na'],
            'nombre_s': number['s'],
            'nombre_p': number['p'],
            'nombre_na': number['na'],
        })

    stats = pd.DataFrame(results)

    # 4. Print to console
    print("=" * 120)
    print(f"{'Code':<12} {'Name':<25} {'Count':>8}  |  {'m':>6} {'f':>6} {'n/a':>6}  |  {'s':>6} {'p':>6} {'n/a':>6}")
    print("=" * 120)

    for _, row in stats.iterrows():
        print(
            f"{row['cgram']:<12} {row['name']:<25} {row['count']:>8,}  |  "
            f"{row['genre_m']:>6,} {row['genre_f']:>6,} {row['genre_na']:>6,}  |  "
            f"{row['nombre_s']:>6,} {row['nombre_p']:>6,} {row['nombre_na']:>6,}"
        )

    print("=" * 120)
    print(
        f"{'TOTAL':<38} {stats['count'].sum():>8,}  |  "
        f"{stats['genre_m'].sum():>6,} {stats['genre_f'].sum():>6,} {stats['genre_na'].sum():>6,}  |  "
        f"{stats['nombre_s'].sum():>6,} {stats['nombre_p'].sum():>6,} {stats['nombre_na'].sum():>6,}"
    )

    # 5. Export CSV
    stats.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved: {OUTPUT_PATH}")

    # 6. Legend
    print("\nLegend:")
    print("  genre: m = masculine, f = feminine, n/a = unspecified")
    print("  nombre: s = singular, p = plural, n/a = unspecified")


if __name__ == "__main__":
    main()
