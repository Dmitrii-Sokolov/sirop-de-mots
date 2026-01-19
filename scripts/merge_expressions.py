#!/usr/bin/env python3
"""Merge all expression CSV files into one with source column."""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Files to merge with their source labels
FILES = {
    "expressions_idiomatiques.csv": "idiomes",
    "expressions_quebecoises.csv": "québec_expr",
    "vocabulaire_quebecois.csv": "québec_vocab",
    "sacres_quebecois.csv": "québec_sacres",
    "proverbes_francais.csv": "proverbes",
    "connecteurs_logiques.csv": "connecteurs",
    "constructions_verbales.csv": "constructions",
    "expressions_opinion.csv": "opinion",
    "expressions_temps.csv": "temps",
    "fillers_formules.csv": "fillers_formules",
}

def main():
    all_dfs = []

    for filename, source in FILES.items():
        filepath = DATA_DIR / filename
        if filepath.exists():
            df = pd.read_csv(filepath, encoding="utf-8", on_bad_lines="warn")
            df["Source"] = source
            all_dfs.append(df)
            print(f"✓ {filename}: {len(df)} entries")
        else:
            print(f"✗ {filename}: NOT FOUND")

    # Combine all dataframes
    combined = pd.concat(all_dfs, ignore_index=True)

    # Reorder columns to put Source at the end
    cols = [c for c in combined.columns if c != "Source"] + ["Source"]
    combined = combined[cols]

    # Save
    output_path = DATA_DIR / "all_expressions.csv"
    combined.to_csv(output_path, index=False, encoding="utf-8")

    print(f"\n{'='*50}")
    print(f"Total: {len(combined)} expressions")
    print(f"Saved to: {output_path}")

    # Stats by source
    print(f"\nBy source:")
    for source, count in combined["Source"].value_counts().items():
        print(f"  {source}: {count}")

if __name__ == "__main__":
    main()
