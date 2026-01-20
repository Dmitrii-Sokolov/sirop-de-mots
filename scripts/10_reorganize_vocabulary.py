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

import pandas as pd
from pathlib import Path
from config import PROJECT_ROOT

# Paths
CONTENT_DIR = PROJECT_ROOT / "content" / "vocabulary"
OUTPUT_DIR = CONTENT_DIR  # Same directory, new files
SKELETON_PATH = PROJECT_ROOT / "output" / "vocabulary_skeleton.csv"

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
    """Merge batch content with skeleton metadata."""
    # Merge on French field
    merged = batches.merge(
        skeleton[['French', 'WordType', 'Notes', 'freqlem', 'rank']],
        on='French',
        how='left'
    )

    # Check for unmatched
    unmatched = merged[merged['WordType'].isna()]
    if len(unmatched) > 0:
        print(f"Warning: {len(unmatched)} entries not in skeleton:")
        print(unmatched['French'].head(10).tolist())

    # Remove duplicates (keep first occurrence)
    before = len(merged)
    merged = merged.drop_duplicates(subset='French', keep='first')
    if before != len(merged):
        print(f"Removed {before - len(merged)} duplicates")

    return merged


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
