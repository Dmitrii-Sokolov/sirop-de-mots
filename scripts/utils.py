"""
Shared utilities for French vocabulary scripts.
"""

import re
from pathlib import Path

# Maximum slug length to avoid filesystem issues (255 char limit minus prefix/suffix room)
MAX_SLUG_LENGTH = 200

# Accent map for French characters (lowercase only - input is lowercased first)
ACCENT_MAP = {
    'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
    'à': 'a', 'â': 'a', 'ä': 'a',
    'ù': 'u', 'û': 'u', 'ü': 'u',
    'î': 'i', 'ï': 'i',
    'ô': 'o', 'ö': 'o',
    'ç': 'c',
    'œ': 'oe', 'æ': 'ae',
    'ÿ': 'y',
}


def slugify(text: str, max_length: int = MAX_SLUG_LENGTH) -> str:
    """
    Convert French text to filename-safe slug.

    Args:
        text: French text to convert
        max_length: Maximum slug length (default 200)

    Examples:
        "une maison" -> "une_maison"
        "l'homme" -> "l_homme"
        "aujourd'hui" -> "aujourd_hui"
        "être" -> "etre"
        "L'Haÿ-les-Roses" -> "l_hay_les_roses"
    """
    # Normalize apostrophes
    text = text.replace("'", "_").replace("'", "_")

    # Lowercase first, then remove accents (handles uppercase accents too)
    slug = text.lower()
    for accented, plain in ACCENT_MAP.items():
        slug = slug.replace(accented, plain)

    # Replace spaces and special chars with underscore
    slug = re.sub(r'[^a-z0-9]+', '_', slug)

    # Remove leading/trailing underscores
    slug = slug.strip('_')

    # Collapse multiple underscores
    slug = re.sub(r'_+', '_', slug)

    # Truncate if too long (unlikely but safe)
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('_')

    return slug


def strip_html(text: str) -> str:
    """Remove HTML tags like <b>...</b> from text."""
    return re.sub(r'<[^>]+>', '', text)


def get_audio_prefix(source_file: Path, content_dir: Path) -> str:
    """
    Get unique prefix for audio files based on source category.

    This ensures unique filenames in Anki's flat media storage.

    Args:
        source_file: Path to source CSV file
        content_dir: Path to content directory

    Examples:
        vocabulary/a1_a2.csv -> "v_a1a2_"
        vocabulary/b1.csv -> "v_b1_"
        expressions/all.csv -> "expr_"
        quebecismes/all.csv -> "qc_"
    """
    rel_path = source_file.relative_to(content_dir)
    parent = rel_path.parent.name

    if parent == "vocabulary":
        level = rel_path.stem.replace("_", "")
        return f"v_{level}_"
    elif parent == "expressions":
        return "expr_"
    elif parent == "quebecismes":
        return "qc_"
    else:
        return f"{parent[:4]}_"
