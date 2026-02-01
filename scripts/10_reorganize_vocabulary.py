"""
Reorganize vocabulary batches into level-based files.

Splits vocabulary into:
- autres.csv: non-major categories (adv, pron, prep, conj, interj, num, art)
- a1_a2.csv: Top 1000 major words (NOM, VER, ADJ)
- b1.csv: Top 1001-3000 major words
- b2.csv: Top 3001-5000 major words
- c1.csv: Top 5001+ major words

Major categories: m, f, m/f (nouns), v (verbs), adj (adjectives)
"""

import re
import pandas as pd
from pathlib import Path
from config import PROJECT_ROOT

# Paths
CONTENT_DIR = PROJECT_ROOT / "content" / "vocabulary"
OUTPUT_DIR = CONTENT_DIR  # Same directory, new files
SKELETON_PATH = PROJECT_ROOT / "output" / "vocabulary_skeleton.csv"

# Prefixes to strip for normalization (order matters - longer first)
PREFIXES_TO_STRIP = [
    # Articles
    "un/une ", "de la ", "de l'",
    "un ", "une ", "l'", "le ", "la ", "les ", "des ", "du ",
    # Reflexive pronouns
    "s'", "se ",
]


def normalize_french(text: str) -> str:
    """Normalize French text for matching.

    - Strips articles (un, une, l', le, la, les, des, du)
    - Strips reflexive pronouns (s', se)
    - Takes first form before comma (for adjectives: "intelligent, intelligente" → "intelligent")
    - Lowercases and strips whitespace
    """
    if pd.isna(text):
        return ""

    text = str(text).strip()

    # Take first form before comma (handles "intelligent, intelligente")
    if ", " in text:
        text = text.split(", ")[0]

    # Lowercase for comparison
    text_lower = text.lower()

    # Strip prefixes (articles, reflexive pronouns)
    for prefix in PREFIXES_TO_STRIP:
        if text_lower.startswith(prefix):
            text = text[len(prefix):]
            text_lower = text.lower()
            # Don't break - might have multiple (e.g., "se l'approprier")

    return text.strip().lower()

# Major word types (NOM, VER, ADJ)
MAJOR_TYPES = {'m', 'f', 'm/f', 'v', 'adj'}

# Level boundaries (by rank in skeleton, 0-indexed)
LEVELS = {
    'a1_a2': (0, 1000),      # Top 1000
    'b1': (1000, 3000),      # 1001-3000
    'b2': (3000, 5000),      # 3001-5000
    'c1': (5000, None),      # 5001+
}


def load_all_batches() -> pd.DataFrame:
    """Load and concatenate all batch files."""
    batch_files = sorted(CONTENT_DIR.glob("batch_*.csv"))
    print(f"Loading {len(batch_files)} batch files...")

    dfs = []
    for f in batch_files:
        df = pd.read_csv(f)
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    print(f"Total entries from batches: {len(combined)}")
    return combined


def load_skeleton() -> pd.DataFrame:
    """Load skeleton with metadata."""
    df = pd.read_csv(SKELETON_PATH)
    # Add rank column (0-indexed position = frequency rank)
    df['rank'] = range(len(df))
    print(f"Skeleton entries: {len(df)}")
    return df


def merge_with_skeleton(batches: pd.DataFrame, skeleton: pd.DataFrame) -> pd.DataFrame:
    """Merge batch content with skeleton metadata.

    Strategy: exact match first, then normalized match for remaining.
    This prevents "un mignon" (noun) from matching "mignon, mignonne" (adj).
    """
    batches = batches.copy()
    skeleton = skeleton.copy()

    # Create lookup dictionaries
    skeleton['_norm_key'] = skeleton['French'].apply(normalize_french)

    # Exact match lookup: French -> (WordType, Notes, freqlem, rank)
    exact_lookup = {}
    for _, row in skeleton.iterrows():
        exact_lookup[row['French']] = (row['WordType'], row.get('Notes', ''), row['freqlem'], row['rank'])

    # Normalized lookup: norm_key -> (WordType, Notes, freqlem, rank)
    # Only add if not already in exact (to prefer exact matches)
    norm_lookup = {}
    for _, row in skeleton.iterrows():
        norm_key = row['_norm_key']
        if norm_key not in norm_lookup:
            norm_lookup[norm_key] = (row['WordType'], row.get('Notes', ''), row['freqlem'], row['rank'])

    # Match each batch entry
    results = []
    unmatched = []

    # Article prefixes that indicate a noun - don't fallback to normalized match
    NOUN_PREFIXES = ('un ', 'une ', 'un/', 'des ', 'les ', "l'", 'le ', 'la ')

    for _, row in batches.iterrows():
        french = row['French']
        norm_key = normalize_french(french)

        # Try exact match first
        if french in exact_lookup:
            wt, notes, freq, rank = exact_lookup[french]
        # For nouns with articles, try epicene form (un X -> un/une X)
        # before giving up. This prevents substantivized forms from matching
        # base adjectives (un malade -> malade/adj) while still matching
        # common-gender nouns (un enfant -> un/une enfant).
        elif french.startswith(('un ', 'une ')):
            epicene_key = f"un/une {french.split(' ', 1)[1]}"
            if epicene_key in exact_lookup:
                wt, notes, freq, rank = exact_lookup[epicene_key]
            else:
                unmatched.append(french)
                continue
        elif french.startswith(NOUN_PREFIXES):
            unmatched.append(french)
            continue
        # Then try normalized match (for words without articles)
        elif norm_key in norm_lookup:
            wt, notes, freq, rank = norm_lookup[norm_key]
        else:
            unmatched.append(french)
            continue

        results.append({
            'French': french,
            'Russian': row['Russian'],
            'ExampleFrench': row['ExampleFrench'],
            'ExampleRussian': row['ExampleRussian'],
            'Emoji': row['Emoji'],
            'WordType': wt,
            'Notes': notes,
            'freqlem': freq,
            'rank': rank,
        })

    if unmatched:
        print(f"\nWARNING: {len(unmatched)} entries not matched in skeleton!")
        print("Unmatched words (first 20):")
        for word in unmatched[:20]:
            norm = normalize_french(word)
            print(f"  '{word}' (normalized: '{norm}')")
        if len(unmatched) > 20:
            print(f"  ... and {len(unmatched) - 20} more")
        print("\nThese words will be EXCLUDED from output.")
        print("Fix: add them to skeleton or check French field format.\n")

    matched = pd.DataFrame(results)
    print(f"Matched: {len(matched)} / {len(batches)} entries")

    # Remove duplicates (keep first occurrence)
    before = len(matched)
    matched = matched.drop_duplicates(subset='French', keep='first')
    if before != len(matched):
        print(f"Removed {before - len(matched)} duplicates")

    return matched


def split_by_category(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into major (NOM/VER/ADJ) and other categories."""
    df['is_major'] = df['WordType'].isin(MAJOR_TYPES)

    major = df[df['is_major']].copy()
    other = df[~df['is_major']].copy()

    # Sort by rank (frequency)
    major = major.sort_values('rank')
    other = other.sort_values('rank')

    print(f"Major (NOM/VER/ADJ): {len(major)}")
    print(f"Other: {len(other)}")

    return major, other


def save_level_files(major: pd.DataFrame, other: pd.DataFrame):
    """Save reorganized files."""
    # Output columns (content + WordType for Anki)
    content_cols = ['French', 'Russian', 'ExampleFrench', 'ExampleRussian', 'Emoji', 'WordType']

    # Save autres.csv
    autres_path = OUTPUT_DIR / "autres.csv"
    other[content_cols].to_csv(autres_path, index=False)
    print(f"Saved: {autres_path.name} ({len(other)} entries)")

    # Save level files
    for level_name, (start, end) in LEVELS.items():
        if end is None:
            level_df = major[major['rank'] >= start]
        else:
            level_df = major[(major['rank'] >= start) & (major['rank'] < end)]

        level_path = OUTPUT_DIR / f"{level_name}.csv"
        level_df[content_cols].to_csv(level_path, index=False)
        print(f"Saved: {level_path.name} ({len(level_df)} entries)")


def print_summary(major: pd.DataFrame, other: pd.DataFrame):
    """Print summary statistics."""
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)

    print("\nMajor categories by level:")
    for level_name, (start, end) in LEVELS.items():
        if end is None:
            count = len(major[major['rank'] >= start])
        else:
            count = len(major[(major['rank'] >= start) & (major['rank'] < end)])
        print(f"  {level_name}: {count}")

    print(f"\nOther (autres): {len(other)}")
    print(f"  Types: {dict(other['WordType'].value_counts())}")

    print(f"\nTotal: {len(major) + len(other)}")


def main():
    print("="*50)
    print("Reorganizing vocabulary files")
    print("="*50 + "\n")

    # Load data
    batches = load_all_batches()
    skeleton = load_skeleton()

    # Merge
    print("\nMerging with skeleton...")
    merged = merge_with_skeleton(batches, skeleton)

    # Split
    print("\nSplitting by category...")
    major, other = split_by_category(merged)

    # Summary
    print_summary(major, other)

    # Save
    print("\nSaving files...")
    save_level_files(major, other)

    print("\nDone!")


if __name__ == "__main__":
    main()
