"""
Shared utilities for French vocabulary scripts.
"""

import re


def slugify(text: str) -> str:
    """
    Convert French text to filename-safe slug.

    Examples:
        "une maison" -> "une_maison"
        "l'homme" -> "l_homme"
        "aujourd'hui" -> "aujourd_hui"
        "être" -> "etre"
    """
    # Normalize apostrophes
    text = text.replace("'", "_").replace("'", "_")

    # Remove accents for filename (keep original for TTS)
    accent_map = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ç': 'c',
        'œ': 'oe', 'æ': 'ae',
    }
    slug = text.lower()
    for accented, plain in accent_map.items():
        slug = slug.replace(accented, plain)

    # Replace spaces and special chars with underscore
    slug = re.sub(r'[^a-z0-9]+', '_', slug)

    # Remove leading/trailing underscores
    slug = slug.strip('_')

    # Collapse multiple underscores
    slug = re.sub(r'_+', '_', slug)

    return slug


def strip_html(text: str) -> str:
    """Remove HTML tags like <b>...</b> from text."""
    return re.sub(r'<[^>]+>', '', text)
