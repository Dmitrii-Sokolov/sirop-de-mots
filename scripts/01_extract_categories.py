#!/usr/bin/env python3
"""
01_extract_categories.py

Extracts lemmas from Lexique383 database:
- VER, NOM, ADJ, ADV: top N by weighted frequency
- Other categories: all lemmas
- Splits into separate files: categories >= MIN_CATEGORY_SIZE get own file, rest go to other.csv
"""

import pandas as pd
from config import (
    LEXIQUE_PATH,
    CATEGORIES_DIR,
    FREQ_FILTERED_CATEGORIES,
    TOP_N_PER_CATEGORY,
    MIN_CATEGORY_SIZE,
    CATEGORY_COLUMNS,
    FREQ_FILMS_WEIGHT,
    FREQ_BOOKS_WEIGHT,
    REQUIRED_LEXIQUE_COLUMNS,
)


def get_word_forms(df: pd.DataFrame) -> dict[tuple[str, str], str]:
    """
    Collects word forms by gender and number for each lemma+cgram.

    Returns:
        dict[(lemme, cgram)] -> "form1/form2 form3/form4"
    """
    forms_dict = {}

    for (lemme, cgram), group in df.groupby(['lemme', 'cgram']):
        forms_by_gn = {}  # (genre, nombre) -> set(ortho)

        for _, row in group.iterrows():
            genre = row['genre'] if pd.notna(row['genre']) else ''
            nombre = row['nombre'] if pd.notna(row['nombre']) else ''
            ortho = row['ortho']

            key = (genre, nombre)
            if key not in forms_by_gn:
                forms_by_gn[key] = set()
            forms_by_gn[key].add(ortho)

        forms_str = _format_forms(lemme, forms_by_gn)
        forms_dict[(lemme, cgram)] = forms_str

    return forms_dict


def _format_forms(lemme: str, forms_by_gn: dict) -> str:
    """
    Formats word forms into a string.

    Formats:
    - Single form: lemme
    - Two forms (sg/pl): sg, pl
    - Four forms (m/f x sg/pl): m.sg/f.sg m.pl/f.pl
    """
    ms = forms_by_gn.get(('m', 's'), forms_by_gn.get(('', 's'), set()))
    fs = forms_by_gn.get(('f', 's'), set())
    mp = forms_by_gn.get(('m', 'p'), forms_by_gn.get(('', 'p'), set()))
    fp = forms_by_gn.get(('f', 'p'), set())

    if not ms and not mp:
        ms = forms_by_gn.get(('m', ''), forms_by_gn.get(('', ''), set()))
    if not fs and not fp:
        fs = forms_by_gn.get(('f', ''), set())

    def first(s):
        return next(iter(s)) if s else ''

    ms_form = first(ms)
    fs_form = first(fs)
    mp_form = first(mp)
    fp_form = first(fp)

    all_forms = {f for f in [ms_form, fs_form, mp_form, fp_form] if f}

    if len(all_forms) == 0:
        return lemme

    if len(all_forms) == 1:
        return first(all_forms)

    has_gender_diff = fs_form and ms_form and fs_form != ms_form
    has_number_diff = (mp_form and ms_form and mp_form != ms_form) or \
                      (fp_form and fs_form and fp_form != fs_form)

    if has_gender_diff and has_number_diff:
        sg = f"{ms_form}/{fs_form}" if ms_form and fs_form else (ms_form or fs_form)
        pl = f"{mp_form}/{fp_form}" if mp_form and fp_form else (mp_form or fp_form)
        if pl:
            return f"{sg} {pl}"
        return sg
    elif has_gender_diff:
        return f"{ms_form}/{fs_form}"
    elif has_number_diff:
        sg = ms_form or fs_form
        pl = mp_form or fp_form
        return f"{sg}, {pl}"
    else:
        return first(all_forms)


def calculate_weighted_frequency(df: pd.DataFrame) -> pd.Series:
    """
    Calculates weighted frequency for TEF/TCF preparation.
    Films weighted higher for oral comprehension.
    """
    films = df['freqlemfilms2'].fillna(0)
    books = df['freqlemlivres'].fillna(0)
    return FREQ_FILMS_WEIGHT * films + FREQ_BOOKS_WEIGHT * books


def main():
    if not LEXIQUE_PATH.exists():
        print(f"File {LEXIQUE_PATH} not found!")
        print(f"   Download from: http://www.lexique.org/databases/Lexique383/Lexique383.tsv")
        return 1

    CATEGORIES_DIR.mkdir(exist_ok=True)

    # Load
    df = pd.read_csv(LEXIQUE_PATH, sep='\t', low_memory=False)
    print(f"Loaded {len(df):,} records from Lexique383")

    # Validate columns
    missing = set(REQUIRED_LEXIQUE_COLUMNS) - set(df.columns)
    if missing:
        print(f"Missing required columns: {missing}")
        return 1

    # Collect word forms (before filtering by islem)
    print("Collecting word forms...")
    forms_dict = get_word_forms(df)
    print(f"   Collected forms for {len(forms_dict):,} lemmas")

    # 1. Lemmas only
    lemmas = df[df['islem'] == 1].copy()
    print(f"Lemmas (islem=1): {len(lemmas):,}")

    # 2. Calculate weighted frequency
    lemmas['freqlem'] = calculate_weighted_frequency(lemmas)

    # 3. Add forms
    lemmas['forms'] = lemmas.apply(
        lambda row: forms_dict.get((row['lemme'], row['cgram']), row['lemme']),
        axis=1
    )

    # 4. Split into two groups
    freq_filtered = lemmas[lemmas['cgram'].isin(FREQ_FILTERED_CATEGORIES)].copy()
    other = lemmas[~lemmas['cgram'].isin(FREQ_FILTERED_CATEGORIES)].copy()

    print(f"\nCategories with filter ({', '.join(FREQ_FILTERED_CATEGORIES)}):")
    print(f"   Total: {len(freq_filtered):,}")

    # 5. For VER/NOM/ADJ/ADV: top N by freqlem
    freq_filtered = freq_filtered.nlargest(TOP_N_PER_CATEGORY, 'freqlem')
    print(f"After top-{TOP_N_PER_CATEGORY:,} filter: {len(freq_filtered):,}")

    # Category distribution in top N
    print(f"\nDistribution in top-{TOP_N_PER_CATEGORY:,}:")
    for cat in FREQ_FILTERED_CATEGORIES:
        count = len(freq_filtered[freq_filtered['cgram'] == cat])
        print(f"   {cat:<6} {count:>6}")

    # 6. Merge (exclude records without category)
    other = other[other['cgram'].notna()]
    result = pd.concat([freq_filtered, other], ignore_index=True)

    # 7. Keep only needed columns
    result = result[CATEGORY_COLUMNS].copy()

    # 8. Split by categories
    category_counts = result['cgram'].value_counts()

    large_categories = category_counts[category_counts >= MIN_CATEGORY_SIZE].index.tolist()
    small_categories = category_counts[category_counts < MIN_CATEGORY_SIZE].index.tolist()

    print(f"\nCategories for separate files (>={MIN_CATEGORY_SIZE}):")
    for cat in sorted(large_categories):
        print(f"   {cat:<12} {category_counts[cat]:>6}")

    print(f"\nCategories for other.csv (<{MIN_CATEGORY_SIZE}):")
    for cat in sorted(small_categories):
        print(f"   {cat:<12} {category_counts[cat]:>6}")

    # 9. Save files
    total_saved = 0

    for cat in large_categories:
        cat_data = result[result['cgram'] == cat].copy()
        cat_data = cat_data.sort_values('freqlem', ascending=False)

        filename = cat.replace(':', '_') + '.csv'
        filepath = CATEGORIES_DIR / filename
        cat_data.to_csv(filepath, index=False)

        print(f"   {filename}: {len(cat_data):,} lemmas")
        total_saved += len(cat_data)

    # Save other.csv
    other_data = result[result['cgram'].isin(small_categories)].copy()
    other_data = other_data.sort_values(['cgram', 'freqlem'], ascending=[True, False])
    other_path = CATEGORIES_DIR / 'other.csv'
    other_data.to_csv(other_path, index=False)

    print(f"   other.csv: {len(other_data):,} lemmas")
    total_saved += len(other_data)

    print(f"\n" + "=" * 60)
    print(f"TOTAL: {total_saved:,} lemmas")
    print(f"Saved to: {CATEGORIES_DIR}/")
    print(f"Frequency formula: {FREQ_FILMS_WEIGHT}*films + {FREQ_BOOKS_WEIGHT}*books")
    print("=" * 60)

    # Preview
    print(f"\nPreview ADJ (top 5):")
    adj_preview = result[result['cgram'] == 'ADJ'].nlargest(5, 'freqlem')
    print(adj_preview.to_string(index=False))

    return 0


if __name__ == "__main__":
    exit(main())
