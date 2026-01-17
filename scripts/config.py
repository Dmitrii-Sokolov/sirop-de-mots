"""
Configuration for French Anki card generation pipeline.

All paths are relative to project root (sirop-de-mots/).
"""

from pathlib import Path

# =============================================================================
# Paths
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent

# Input
LEXIQUE_PATH = PROJECT_ROOT / "Lexique383.tsv"

# Data files (manual + generated)
DATA_DIR = PROJECT_ROOT / "data"
BLACKLIST_PATH = DATA_DIR / "blacklist.csv"
WHITELIST_NUMERALS_PATH = DATA_DIR / "whitelist_numerals.csv"
HOMOGRAPHS_REPORT_PATH = DATA_DIR / "homographs_report.csv"
PROFESSIONS_CHECK_PATH = DATA_DIR / "professions_check.csv"
IRREGULAR_ADJ_PATH = DATA_DIR / "irregular_adjectives.csv"
IRREGULAR_VERBS_PATH = DATA_DIR / "irregular_verbs.csv"

# Categories (generated)
CATEGORIES_DIR = PROJECT_ROOT / "categories"

# Additions (manual)
ADDITIONS_DIR = PROJECT_ROOT / "additions"
CANADIAN_FRENCH_PATH = ADDITIONS_DIR / "canadian_french.csv"
EXPRESSIONS_PATH = ADDITIONS_DIR / "expressions.csv"

# Output
OUTPUT_DIR = PROJECT_ROOT / "output"
CARDS_SKELETON_PATH = OUTPUT_DIR / "cards_skeleton.csv"
CARDS_FOR_AI_PATH = OUTPUT_DIR / "cards_for_ai.csv"
CARDS_COMPLETE_PATH = OUTPUT_DIR / "cards_complete.csv"
VOCABULARY_IMPORT_PATH = OUTPUT_DIR / "French_Vocabulary_Import.csv"
CONJUGATION_IMPORT_PATH = OUTPUT_DIR / "French_Conjugation_Import.csv"
AUDIO_WORDS_DIR = OUTPUT_DIR / "audio" / "words"
AUDIO_EXAMPLES_DIR = OUTPUT_DIR / "audio" / "examples"

# =============================================================================
# Frequency Settings
# =============================================================================

# Weighted frequency formula for TEF/TCF (oral comprehension priority)
# freq_combined = FREQ_FILMS_WEIGHT * freqlemfilms2 + FREQ_BOOKS_WEIGHT * freqlemlivres
FREQ_FILMS_WEIGHT = 0.6
FREQ_BOOKS_WEIGHT = 0.4

# Target ~20000 words in final selection
# This threshold will be determined experimentally
FREQ_MIN_THRESHOLD = None  # To be determined

# =============================================================================
# Category Settings
# =============================================================================

# Categories with frequency filtering (top N by frequency)
FREQ_FILTERED_CATEGORIES = ['VER', 'NOM', 'ADJ', 'ADV']

# Top N for main categories (before threshold filtering)
TOP_N_PER_CATEGORY = 10000

# Minimum category size for separate file
MIN_CATEGORY_SIZE = 100

# =============================================================================
# Blacklist Reasons
# =============================================================================

class BlacklistReason:
    ARCHAIC = "archaic"
    PARSE_ERROR = "parse_error"
    COMPOSITE_NUMERAL = "composite_numeral"
    DUPLICATE = "duplicate"
    OFFENSIVE = "offensive"

# =============================================================================
# Output Columns
# =============================================================================

# Columns for category CSV files
CATEGORY_COLUMNS = ['lemme', 'cgram', 'genre', 'freqlem', 'forms', 'nbhomogr']

# Columns for skeleton CSV
SKELETON_COLUMNS = ['French', 'WordType', 'cgram', 'freqlem', 'related_forms']

# Columns for AI filling
AI_COLUMNS = ['French', 'WordType', 'Russian', 'ExampleFrench', 'ExampleRussian', 'Notes', 'Emoji']

# Final Anki import columns
ANKI_VOCABULARY_COLUMNS = ['French', 'Russian', 'WordType', 'ExampleFrench', 'ExampleRussian', 'Notes', 'Emoji', 'Audio', 'AudioExample']

# =============================================================================
# WordType Mapping (cgram -> Anki WordType)
# =============================================================================

WORDTYPE_MAP = {
    'NOM': lambda genre: 'm' if genre == 'm' else 'f' if genre == 'f' else 'm/f',
    'VER': lambda _: 'v',
    'ADJ': lambda _: 'adj',
    'ADV': lambda _: 'adv',
    'PRE': lambda _: 'prep',
    'CON': lambda _: 'conj',
    'ONO': lambda _: 'interj',
    'PRO:per': lambda _: 'pron',
    'PRO:ind': lambda _: 'pron',
    'PRO:pos': lambda _: 'pron',
    'PRO:rel': lambda _: 'pron',
    'PRO:int': lambda _: 'pron',
    'PRO:dem': lambda _: 'pron',
    'ART:def': lambda _: 'art',
    'ART:ind': lambda _: 'art',
    'ADJ:num': lambda _: 'num',
    'ADJ:ind': lambda _: 'adj',
    'ADJ:pos': lambda _: 'adj',
    'ADJ:int': lambda _: 'adj',
    'ADJ:dem': lambda _: 'adj',
    'AUX': lambda _: 'v',
}

def get_wordtype(cgram: str, genre: str | None) -> str:
    """Convert Lexique cgram to Anki WordType."""
    mapper = WORDTYPE_MAP.get(cgram)
    if mapper:
        return mapper(genre)
    return cgram.lower()

# =============================================================================
# Azure TTS Settings
# =============================================================================

# Canadian French voices (all 4 in equal proportion)
AZURE_TTS_VOICES = [
    "fr-CA-SylvieNeural",   # Female
    "fr-CA-JeanNeural",     # Male
    "fr-CA-AntoineNeural",  # Male
    "fr-CA-ThierryNeural",  # Male
]

AZURE_TTS_FORMAT = "audio-16khz-128kbitrate-mono-mp3"

# Rate limiting for batch processing
AZURE_TTS_REQUESTS_PER_SECOND = 10
AZURE_TTS_RETRY_ATTEMPTS = 3

# =============================================================================
# Target Volumes
# =============================================================================

# Phase 1: realistic set for 1 year of study
TARGET_LEMMAS_PHASE1 = 3000

# Phase 2: B2-C1 level
TARGET_LEMMAS_PHASE2 = 5000

# Total pool for selection
TARGET_LEMMAS_POOL = 20000

# =============================================================================
# Validation
# =============================================================================

# Required Lexique columns
REQUIRED_LEXIQUE_COLUMNS = [
    'ortho', 'lemme', 'cgram', 'genre', 'nombre',
    'freqlemfilms2', 'freqlemlivres', 'islem', 'nbhomogr'
]
