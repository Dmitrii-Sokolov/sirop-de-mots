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
NOM_WITHOUT_GENRE_PATH = DATA_DIR / "nom_without_genre.csv"
GENDER_HOMOGRAPHS_PATH = DATA_DIR / "gender_homographs.csv"
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

# Content and Audio
CONTENT_DIR = PROJECT_ROOT / "content"
AUDIO_BASE_DIR = CONTENT_DIR / "audio"


def get_audio_dir(source_file: Path) -> Path:
    """
    Get audio directory for a source CSV file.

    Examples:
        content/expressions/all.csv -> content/audio/expressions/
        content/vocabulary/a1_a2.csv -> content/audio/vocabulary_a1a2/
        content/quebecismes/all.csv -> content/audio/quebecismes/
    """
    rel_path = source_file.relative_to(CONTENT_DIR)
    parent = rel_path.parent.name

    if parent == "vocabulary":
        # vocabulary/a1_a2.csv -> vocabulary_a1a2
        level = rel_path.stem.replace("_", "")
        audio_subdir = f"vocabulary_{level}"
    else:
        audio_subdir = parent

    return AUDIO_BASE_DIR / audio_subdir

# =============================================================================
# Frequency Settings
# =============================================================================

# Weighted frequency formula for TEF/TCF (oral comprehension priority)
# freq_combined = FREQ_FILMS_WEIGHT * freqlemfilms2 + FREQ_BOOKS_WEIGHT * freqlemlivres
FREQ_FILMS_WEIGHT = 0.6
FREQ_BOOKS_WEIGHT = 0.4

# Target ~20000 words in final selection
# Threshold determined: top 20000 lemmas have freqlem >= 0.67
FREQ_MIN_THRESHOLD = 0.67

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
CATEGORY_COLUMNS = ['lemme', 'cgram', 'genre', 'freqlem', 'forms']

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

# =============================================================================
# Conjugation Data (for restructured conjugation cards)
# =============================================================================

# Sample verbs for 1er groupe (-er, regular)
SAMPLE_1ER_GROUPE = ['parler', 'manger', 'commencer']

# Sample verbs for 2e groupe (-ir with -issant)
SAMPLE_2E_GROUPE = ['finir', 'choisir']

# DR MRS VANDERTRAMP - verbs using être as auxiliary
ETRE_VERBS = [
    'devenir', 'revenir', 'monter', 'rester', 'sortir',
    'venir', 'aller', 'naître', 'descendre', 'entrer',
    'rentrer', 'tomber', 'retourner', 'arriver', 'mourir', 'partir',
    'passer',  # with être when intransitive
]

# Irregular subjonctif présent verbs (stem changes)
SUBJONCTIF_IRREGULIERS = [
    'être', 'avoir', 'aller', 'faire', 'pouvoir',
    'savoir', 'vouloir', 'valoir', 'falloir', 'pleuvoir',
]

# Irregular futur/conditionnel stems (verb → stem)
FUTUR_STEMS = {
    'être': 'ser-',
    'avoir': 'aur-',
    'aller': 'ir-',
    'faire': 'fer-',
    'savoir': 'saur-',
    'pouvoir': 'pourr-',
    'vouloir': 'voudr-',
    'devoir': 'devr-',
    'voir': 'verr-',
    'envoyer': 'enverr-',
    'venir': 'viendr-',
    'tenir': 'tiendr-',
    'courir': 'courr-',
    'mourir': 'mourr-',
    'acquérir': 'acquerr-',
    'valoir': 'vaudr-',
    'falloir': 'faudr-',
    'pleuvoir': 'pleuvr-',
    'recevoir': 'recevr-',
    'apercevoir': 'apercevr-',
    'asseoir': 'assiér-',
    'cueillir': 'cueiller-',
}

# Irregular participes passés (verb → (participe, pattern, related verbs))
PARTICIPES_IRREGULIERS = {
    # -endre → -is
    'prendre': ('pris', '-endre→-is', 'comprendre, apprendre, reprendre, surprendre'),
    'comprendre': ('compris', '-endre→-is', ''),
    'apprendre': ('appris', '-endre→-is', ''),
    'reprendre': ('repris', '-endre→-is', ''),
    'surprendre': ('surpris', '-endre→-is', ''),
    # -ettre → -is
    'mettre': ('mis', '-ettre→-is', 'permettre, promettre, admettre, remettre, soumettre'),
    'permettre': ('permis', '-ettre→-is', ''),
    'promettre': ('promis', '-ettre→-is', ''),
    'admettre': ('admis', '-ettre→-is', ''),
    'remettre': ('remis', '-ettre→-is', ''),
    'soumettre': ('soumis', '-ettre→-is', ''),
    # -aire/-ire → -it/-ait
    'faire': ('fait', '-aire→-ait', 'défaire, refaire, satisfaire'),
    'défaire': ('défait', '-aire→-ait', ''),
    'refaire': ('refait', '-aire→-ait', ''),
    'satisfaire': ('satisfait', '-aire→-ait', ''),
    'dire': ('dit', '-ire→-it', 'redire, contredire, interdire, prédire'),
    'redire': ('redit', '-ire→-it', ''),
    'contredire': ('contredit', '-ire→-it', ''),
    'interdire': ('interdit', '-ire→-it', ''),
    'prédire': ('prédit', '-ire→-it', ''),
    'écrire': ('écrit', '-ire→-it', 'décrire, inscrire, prescrire, transcrire'),
    'décrire': ('décrit', '-ire→-it', ''),
    'inscrire': ('inscrit', '-ire→-it', ''),
    'prescrire': ('prescrit', '-ire→-it', ''),
    'transcrire': ('transcrit', '-ire→-it', ''),
    # -uire → -uit
    'conduire': ('conduit', '-uire→-uit', 'produire, construire, détruire, traduire, réduire'),
    'produire': ('produit', '-uire→-uit', ''),
    'construire': ('construit', '-uire→-uit', ''),
    'détruire': ('détruit', '-uire→-uit', ''),
    'traduire': ('traduit', '-uire→-uit', ''),
    'réduire': ('réduit', '-uire→-uit', ''),
    'cuire': ('cuit', '-uire→-uit', ''),
    # -vrir/-ffrir → -vert/-ffert
    'ouvrir': ('ouvert', '-vrir→-vert', 'couvrir, découvrir, offrir, souffrir'),
    'couvrir': ('couvert', '-vrir→-vert', ''),
    'découvrir': ('découvert', '-vrir→-vert', ''),
    'offrir': ('offert', '-ffrir→-ffert', ''),
    'souffrir': ('souffert', '-ffrir→-ffert', ''),
    # Unique forms
    'mourir': ('mort', 'unique', ''),
    'naître': ('né', 'unique', 'renaître'),
    'renaître': ('rené', 'unique', ''),
    'vivre': ('vécu', '-ivre→-écu', 'survivre, revivre'),
    'survivre': ('survécu', '-ivre→-écu', ''),
    'revivre': ('revécu', '-ivre→-écu', ''),
    'boire': ('bu', '-oire→-u', ''),
    'lire': ('lu', '-ire→-u', 'relire, élire'),
    'relire': ('relu', '-ire→-u', ''),
    'élire': ('élu', '-ire→-u', ''),
    'voir': ('vu', '-oir→-u', 'revoir, prévoir'),
    'revoir': ('revu', '-oir→-u', ''),
    'prévoir': ('prévu', '-oir→-u', ''),
    'croire': ('cru', '-oire→-u', ''),
    'connaître': ('connu', '-aître→-u', 'reconnaître, paraître, apparaître, disparaître'),
    'reconnaître': ('reconnu', '-aître→-u', ''),
    'paraître': ('paru', '-aître→-u', ''),
    'apparaître': ('apparu', '-aître→-u', ''),
    'disparaître': ('disparu', '-aître→-u', ''),
    'pouvoir': ('pu', '-ouvoir→-u', ''),
    'vouloir': ('voulu', '-ouloir→-oulu', ''),
    'devoir': ('dû', '-evoir→-û', ''),
    'savoir': ('su', '-avoir→-u', ''),
    'recevoir': ('reçu', '-cevoir→-çu', 'apercevoir, concevoir, décevoir, percevoir'),
    'apercevoir': ('aperçu', '-cevoir→-çu', ''),
    'concevoir': ('conçu', '-cevoir→-çu', ''),
    'décevoir': ('déçu', '-cevoir→-çu', ''),
    'percevoir': ('perçu', '-cevoir→-çu', ''),
    'tenir': ('tenu', '-enir→-enu', 'obtenir, retenir, maintenir, soutenir, contenir'),
    'obtenir': ('obtenu', '-enir→-enu', ''),
    'retenir': ('retenu', '-enir→-enu', ''),
    'maintenir': ('maintenu', '-enir→-enu', ''),
    'soutenir': ('soutenu', '-enir→-enu', ''),
    'contenir': ('contenu', '-enir→-enu', ''),
    'venir': ('venu', '-enir→-enu', 'devenir, revenir, parvenir, intervenir, prévenir'),
    'devenir': ('devenu', '-enir→-enu', ''),
    'revenir': ('revenu', '-enir→-enu', ''),
    'parvenir': ('parvenu', '-enir→-enu', ''),
    'intervenir': ('intervenu', '-enir→-enu', ''),
    'prévenir': ('prévenu', '-enir→-enu', ''),
    'courir': ('couru', '-ourir→-ouru', 'parcourir, secourir, accourir'),
    'parcourir': ('parcouru', '-ourir→-ouru', ''),
    'secourir': ('secouru', '-ourir→-ouru', ''),
    'accourir': ('accouru', '-ourir→-ouru', ''),
    # Auxiliaries and common
    'être': ('été', 'unique', ''),
    'avoir': ('eu', 'unique', ''),
    'plaire': ('plu', '-aire→-u', 'déplaire'),
    'déplaire': ('déplu', '-aire→-u', ''),
    'pleuvoir': ('plu', 'impersonnel', ''),
    'falloir': ('fallu', 'impersonnel', ''),
    'valoir': ('valu', '-aloir→-alu', ''),
    'asseoir': ('assis', 'unique', ''),
    'suivre': ('suivi', '-ivre→-ivi', 'poursuivre'),
    'poursuivre': ('poursuivi', '-ivre→-ivi', ''),
    'rire': ('ri', '-ire→-i', 'sourire'),
    'sourire': ('souri', '-ire→-i', ''),
    'suffire': ('suffi', '-ire→-i', ''),
    # -eindre/-aindre/-oindre → -eint/-aint/-oint
    'peindre': ('peint', '-eindre→-eint', 'repeindre'),
    'repeindre': ('repeint', '-eindre→-eint', ''),
    'craindre': ('craint', '-aindre→-aint', ''),
    'plaindre': ('plaint', '-aindre→-aint', ''),
    'joindre': ('joint', '-oindre→-oint', 'rejoindre, adjoindre'),
    'rejoindre': ('rejoint', '-oindre→-oint', ''),
    'adjoindre': ('adjoint', '-oindre→-oint', ''),
    'atteindre': ('atteint', '-eindre→-eint', ''),
    'éteindre': ('éteint', '-eindre→-eint', ''),
    # Others
    'résoudre': ('résolu', '-oudre→-olu', ''),
    'coudre': ('cousu', '-oudre→-ousu', ''),
    'moudre': ('moulu', '-oudre→-oulu', ''),
    'vaincre': ('vaincu', '-aincre→-aincu', 'convaincre'),
    'convaincre': ('convaincu', '-aincre→-aincu', ''),
    'acquérir': ('acquis', '-érir→-is', 'conquérir'),
    'conquérir': ('conquis', '-érir→-is', ''),
}
