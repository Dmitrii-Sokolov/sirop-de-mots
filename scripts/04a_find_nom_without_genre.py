#!/usr/bin/env python3
"""
04a_find_nom_without_genre.py

Extracts nouns (NOM) without specified gender from Lexique383.
These require manual review to classify as:
- homograph: different genders = different meanings (livre m=book, f=pound)
- common_gender: same meaning for m/f (enfant, chef)
- f_only: feminine only, data error in Lexique
- m_only: masculine only, data error in Lexique

Output: data/nom_without_genre.csv (only words above FREQ_MIN_THRESHOLD)
"""

import pandas as pd
from config import (
    LEXIQUE_PATH,
    DATA_DIR,
    NOM_WITHOUT_GENRE_PATH,
    GENDER_HOMOGRAPHS_PATH,
    FREQ_FILMS_WEIGHT,
    FREQ_BOOKS_WEIGHT,
    FREQ_MIN_THRESHOLD,
)


def main():
    if not LEXIQUE_PATH.exists():
        print(f"File {LEXIQUE_PATH} not found!")
        return 1

    DATA_DIR.mkdir(exist_ok=True)

    # Load Lexique
    df = pd.read_csv(LEXIQUE_PATH, sep='\t', low_memory=False, encoding='utf-8')
    lemmas = df[df['islem'] == 1].copy()

    # Filter NOM with genre=NaN
    nom = lemmas[(lemmas['cgram'] == 'NOM') & (lemmas['genre'].isna())].copy()

    # Calculate weighted frequency
    nom['freqlem'] = (
        FREQ_FILMS_WEIGHT * nom['freqlemfilms2'].fillna(0) +
        FREQ_BOOKS_WEIGHT * nom['freqlemlivres'].fillna(0)
    )

    # Filter by threshold
    nom = nom[nom['freqlem'] >= FREQ_MIN_THRESHOLD].copy()
    nom = nom.sort_values('freqlem', ascending=False)

    print(f"NOM without genre above threshold ({FREQ_MIN_THRESHOLD}): {len(nom)}")

    # Load known gender homographs for pre-classification
    known_homographs = set()
    if GENDER_HOMOGRAPHS_PATH.exists():
        gh = pd.read_csv(GENDER_HOMOGRAPHS_PATH, encoding='utf-8')
        known_homographs = set(gh['lemme'].unique())
        print(f"Loaded {len(known_homographs)} known gender homographs")

    # Pre-classify known types
    def classify(lemme):
        if lemme in known_homographs:
            return 'homograph'
        return ''

    # Build output
    output = nom[['lemme', 'freqlem', 'nbhomogr']].copy()
    output['freqlem'] = output['freqlem'].round(2)
    output['type'] = output['lemme'].apply(classify)
    output['review_notes'] = ''

    # Save
    output.to_csv(NOM_WITHOUT_GENRE_PATH, index=False, encoding='utf-8')

    # Stats
    classified = len(output[output['type'] != ''])
    unclassified = len(output[output['type'] == ''])

    print(f"\nSaved to: {NOM_WITHOUT_GENRE_PATH}")
    print(f"Total: {len(output)}")
    print(f"  Pre-classified (homograph): {classified}")
    print(f"  Needs review: {unclassified}")

    # Show top unclassified
    print(f"\nTop 20 unclassified:")
    unclass = output[output['type'] == ''].head(20)
    print(unclass.to_string(index=False))

    return 0


if __name__ == "__main__":
    exit(main())
