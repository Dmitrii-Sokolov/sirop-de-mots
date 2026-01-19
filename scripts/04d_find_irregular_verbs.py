#!/usr/bin/env python3
"""
04d_find_irregular_verbs.py

Finds irregular verbs (3rd group) in Lexique383.

French verb groups:
- 1st group (-er): regular, except "aller"
- 2nd group (-ir with -issant participle): regular (finir → finissant)
- 3rd group (all others): irregular
  - -ir without -issant (venir → venant, dormir → dormant)
  - -re (prendre, mettre, être)
  - -oir (pouvoir, vouloir, savoir, voir)
  - "aller" (exception from 1st group)

Output: data/irregular_verbs.csv
"""

import sys
import pandas as pd

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from config import (
    LEXIQUE_PATH,
    DATA_DIR,
    IRREGULAR_VERBS_PATH,
    FREQ_FILMS_WEIGHT,
    FREQ_BOOKS_WEIGHT,
    FREQ_MIN_THRESHOLD,
)


# Verbs that are irregular despite -er ending
IRREGULAR_ER_VERBS = {'aller'}

# Common irregular verb patterns for notes
IRREGULAR_PATTERNS = {
    # Être/Avoir
    'être': 'auxiliaire',
    'avoir': 'auxiliaire',
    # Aller
    'aller': '3e groupe (-er exception)',
    # -oir verbs
    'pouvoir': '-oir (je peux, je pourrai)',
    'vouloir': '-oir (je veux, je voudrai)',
    'savoir': '-oir (je sais, je saurai)',
    'devoir': '-oir (je dois, je devrai)',
    'voir': '-oir (je vois, je verrai)',
    'recevoir': '-cevoir (je reçois)',
    'apercevoir': '-cevoir (j\'aperçois)',
    'concevoir': '-cevoir (je conçois)',
    'décevoir': '-cevoir (je déçois)',
    'falloir': '-oir impersonnel (il faut)',
    'valoir': '-oir (je vaux, je vaudrai)',
    'pleuvoir': '-oir impersonnel (il pleut)',
    # -enir verbs
    'venir': '-enir (je viens, je viendrai)',
    'tenir': '-enir (je tiens, je tiendrai)',
    'devenir': '-enir (je deviens)',
    'revenir': '-enir (je reviens)',
    'appartenir': '-enir (j\'appartiens)',
    'contenir': '-enir (je contiens)',
    'obtenir': '-enir (j\'obtiens)',
    'retenir': '-enir (je retiens)',
    'maintenir': '-enir (je maintiens)',
    'soutenir': '-enir (je soutiens)',
    # -ir (3rd group)
    'partir': '-tir (je pars)',
    'sortir': '-tir (je sors)',
    'sentir': '-tir (je sens)',
    'mentir': '-tir (je mens)',
    'servir': '-vir (je sers)',
    'dormir': '-mir (je dors)',
    'mourir': '-ourir (je meurs, je mourrai)',
    'courir': '-ourir (je cours, je courrai)',
    'acquérir': '-érir (j\'acquiers, j\'acquerrai)',
    'ouvrir': '-vrir (j\'ouvre) - comme -er',
    'couvrir': '-vrir (je couvre) - comme -er',
    'offrir': '-frir (j\'offre) - comme -er',
    'souffrir': '-frir (je souffre) - comme -er',
    'cueillir': '-illir (je cueille) - comme -er',
    # -re verbs
    'prendre': '-endre (je prends)',
    'apprendre': '-endre (j\'apprends)',
    'comprendre': '-endre (je comprends)',
    'attendre': '-endre (j\'attends) - régulier',
    'entendre': '-endre (j\'entends) - régulier',
    'mettre': '-ettre (je mets)',
    'permettre': '-ettre (je permets)',
    'promettre': '-ettre (je promets)',
    'battre': '-attre (je bats)',
    'faire': 'très irrégulier (je fais, je ferai)',
    'dire': 'irrégulier (je dis, vous dites)',
    'lire': '-ire (je lis)',
    'écrire': '-ire (j\'écris)',
    'conduire': '-uire (je conduis)',
    'produire': '-uire (je produis)',
    'construire': '-uire (je construis)',
    'détruire': '-uire (je détruis)',
    'traduire': '-uire (je traduis)',
    'vivre': '-ivre (je vis)',
    'suivre': '-ivre (je suis)',
    'boire': 'irrégulier (je bois, nous buvons)',
    'croire': '-oire (je crois)',
    'connaître': '-aître (je connais)',
    'paraître': '-aître (je parais)',
    'naître': '-aître (je nais)',
    'plaire': '-aire (je plais)',
    'craindre': '-aindre (je crains)',
    'peindre': '-eindre (je peins)',
    'joindre': '-oindre (je joins)',
    'résoudre': '-oudre (je résous)',
    'coudre': '-oudre (je couds)',
    'moudre': '-oudre (je mouds)',
    'rompre': '-ompre (je romps)',
    'vaincre': '-aincre (je vaincs)',
    'conclure': '-clure (je conclus)',
    'inclure': '-clure (j\'inclus)',
}


def get_verb_group(lemme: str, participe_present) -> tuple[int, str]:
    """
    Determine verb group and return (group_number, reason).

    Returns:
        (1, 'regular -er') for 1st group
        (2, 'regular -ir (-issant)') for 2nd group
        (3, reason) for 3rd group (irregular)
    """
    # Special case: aller
    if lemme in IRREGULAR_ER_VERBS:
        return 3, '-er exception'

    # 1st group: -er verbs (regular)
    if lemme.endswith('er'):
        return 1, 'regular -er'

    # -ir verbs: check participe présent
    if lemme.endswith('ir'):
        if pd.notna(participe_present) and str(participe_present).endswith('issant'):
            return 2, 'regular -ir (-issant)'
        else:
            return 3, '-ir sans -issant'

    # -re verbs: all 3rd group
    if lemme.endswith('re'):
        return 3, '-re'

    # -oir verbs: all 3rd group
    if lemme.endswith('oir'):
        return 3, '-oir'

    # Unknown ending
    return 3, 'unknown'


def main():
    if not LEXIQUE_PATH.exists():
        print(f"❌ File {LEXIQUE_PATH} not found!")
        return 1

    DATA_DIR.mkdir(exist_ok=True)

    # Load Lexique
    print("Loading Lexique383...")
    df = pd.read_csv(LEXIQUE_PATH, sep='\t', low_memory=False, encoding='utf-8')

    # Get VER lemmas with frequency
    lemmas = df[df['islem'] == 1].copy()
    lemmas['freqlem'] = (
        FREQ_FILMS_WEIGHT * lemmas['freqlemfilms2'].fillna(0) +
        FREQ_BOOKS_WEIGHT * lemmas['freqlemlivres'].fillna(0)
    )

    ver_lemmas = lemmas[lemmas['cgram'] == 'VER'][['lemme', 'freqlem']].copy()
    ver_lemmas = ver_lemmas.drop_duplicates(subset='lemme')

    print(f"Total VER lemmas: {len(ver_lemmas)}")

    # Get participe présent for each verb
    par_pre = df[df['infover'] == 'par:pre;'][['lemme', 'ortho']].copy()
    par_pre = par_pre.drop_duplicates(subset='lemme', keep='first')
    par_pre = par_pre.rename(columns={'ortho': 'participe_present'})

    # Merge
    result = ver_lemmas.merge(par_pre, on='lemme', how='left')

    # Classify verbs
    def classify(row):
        return get_verb_group(row['lemme'], row['participe_present'])

    classifications = result.apply(classify, axis=1)
    result['group'] = classifications.apply(lambda x: x[0])
    result['group_reason'] = classifications.apply(lambda x: x[1])
    result['freqlem'] = result['freqlem'].round(2)

    # Add pattern notes for known irregular verbs
    result['notes'] = result['lemme'].map(IRREGULAR_PATTERNS).fillna('')

    # Statistics
    print("\n" + "=" * 60)
    print("📊 VERB GROUP STATISTICS")
    print("=" * 60)

    for group in [1, 2, 3]:
        count = len(result[result['group'] == group])
        print(f"Group {group}: {count} verbs")

    # Filter by frequency threshold
    result_freq = result[result['freqlem'] >= FREQ_MIN_THRESHOLD]
    print(f"\nAbove frequency threshold ({FREQ_MIN_THRESHOLD}):")
    for group in [1, 2, 3]:
        count = len(result_freq[result_freq['group'] == group])
        print(f"  Group {group}: {count} verbs")

    # 3rd group (irregular) verbs
    irregular = result[result['group'] == 3].copy()
    irregular = irregular.sort_values('freqlem', ascending=False)

    irregular_freq = irregular[irregular['freqlem'] >= FREQ_MIN_THRESHOLD]

    print(f"\n{'=' * 60}")
    print(f"🔴 IRREGULAR VERBS (3rd group): {len(irregular_freq)} above threshold")
    print("=" * 60)

    # Group by reason
    print("\nBy ending:")
    print(irregular_freq['group_reason'].value_counts().to_string())

    print("\n--- Top 50 irregular verbs by frequency ---")
    cols = ['lemme', 'freqlem', 'participe_present', 'group_reason', 'notes']
    print(irregular_freq[cols].head(50).to_string(index=False))

    # Save irregular verbs
    output = irregular_freq[['lemme', 'freqlem', 'participe_present', 'group_reason', 'notes']]
    output = output.rename(columns={'group_reason': 'ending_type'})
    output.to_csv(IRREGULAR_VERBS_PATH, index=False, encoding='utf-8')
    print(f"\n✅ Saved to: {IRREGULAR_VERBS_PATH}")

    # Summary for Anki
    print("\n" + "=" * 60)
    print("📋 SUMMARY FOR ANKI CARDS")
    print("=" * 60)

    print(f"""
Total irregular verbs above threshold: {len(irregular_freq)}

By ending type:""")

    for reason, count in irregular_freq['group_reason'].value_counts().items():
        examples = irregular_freq[irregular_freq['group_reason'] == reason]['lemme'].head(3).tolist()
        print(f"  {reason}: {count} ({', '.join(examples)}...)")

    # Most frequent irregular verbs (top 20)
    print("\n🎯 Priority irregular verbs (top 20 by frequency):")
    top20 = irregular_freq.head(20)
    for _, row in top20.iterrows():
        note = f" — {row['notes']}" if row['notes'] else ""
        print(f"  {row['lemme']:15} {row['freqlem']:>8.2f}{note}")

    return 0


if __name__ == "__main__":
    exit(main())
