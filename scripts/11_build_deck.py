"""
Build complete Anki deck from content files.

Usage:
    python scripts/11_build_deck.py
    python scripts/11_build_deck.py --no-audio  # skip audio fields
    python scripts/11_build_deck.py --output my_deck.apkg
"""

import argparse
import csv
import hashlib
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

import genanki

from config import PROJECT_ROOT, CONTENT_DIR, AUDIO_BASE_DIR, get_audio_dir
from deck_config import (
    ROOT_DECK,
    VOCABULARY_DECKS,
    AUTRES_DECK,
    CONTENT_DECKS,
    CONJUGATION_DECKS,
)
from utils import slugify, get_audio_prefix, strip_html

# =============================================================================
# Validation
# =============================================================================

VALID_WORD_TYPES = {
    'm', 'f', 'm/f', 'v', 'adj', 'adv', 'conj', 'prep',
    'pron', 'num', 'interj', 'expr', 'loc', 'art',
    'f pl', 'm pl', 'loc adv',
}

# Regex for emoji detection (Unicode emoji ranges)
_EMOJI_RE = re.compile(
    r'[\U0001F300-\U0001F9FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F'
    r'\U0000200D\U00002600-\U000026FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]'
)

# Regex for HTML tags
_HTML_TAG_RE = re.compile(r'<(/?)(\w+)[^>]*>')

_CLOZE_RE = re.compile(r'\{\{c\d+::')
_CLOZE_BALANCED_RE = re.compile(r'\{\{c\d+::.*?\}\}')
_CLOZE_OPEN_RE = re.compile(r'\{\{c\d+::')
_BOLD_RE = re.compile(r'<b>(.*?)</b>', re.IGNORECASE)


class BuildErrors:
    """Collects build validation errors."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)
        print(f"  ❌ {msg}")

    def warning(self, msg: str):
        self.warnings.append(msg)
        print(f"  ⚠️  {msg}")

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def summary(self):
        if self.errors:
            print(f"\n❌ Build blocked: {len(self.errors)} error(s)")
            for e in self.errors:
                print(f"  {e}")
        if self.warnings:
            print(f"⚠️  {len(self.warnings)} warning(s)")


def _check_html_balance(text: str) -> str | None:
    """Return first unclosed/mismatched tag, or None if balanced."""
    stack = []
    for m in _HTML_TAG_RE.finditer(text):
        is_close, tag = m.group(1), m.group(2).lower()
        if is_close:
            if not stack or stack[-1] != tag:
                return f"</{tag}> without <{tag}>"
            stack.pop()
        else:
            stack.append(tag)
    if stack:
        return f"unclosed <{stack[-1]}>"
    return None


def validate_vocab_rows(
    rows: list[dict],
    deck_short: str,
    seen_french: Counter,
    errors: BuildErrors,
    include_audio: bool,
    audio_dir: Path | None,
):
    """Validate vocabulary rows. Mutates seen_french counter."""
    for row in rows:
        french = row.get('French', '').strip()
        if not french:
            errors.error(f"{deck_short}: empty French field")
            continue

        # [2] Duplicate check (within vocabulary group)
        seen_french[french] += 1
        if seen_french[french] == 2:
            errors.error(f"{deck_short}: duplicate «{french}»")

        # [3] WordType check
        wt = row.get('WordType', '').strip()
        if wt and wt not in VALID_WORD_TYPES:
            errors.warning(f"{deck_short}: unknown WordType «{wt}» for «{french}»")

        # [14] Empty required fields
        russian = row.get('Russian', '').strip()
        if not russian:
            errors.error(f"{deck_short}: empty Russian for «{french}»")

        # [15] Unclosed HTML in examples
        for field in ('ExampleFrench', 'ExampleRussian'):
            val = row.get(field, '')
            if '<' in val:
                issue = _check_html_balance(val)
                if issue:
                    errors.error(f"{deck_short}: {field} {issue} in «{french}»")

        # [16] Emoji in French field
        if _EMOJI_RE.search(french):
            errors.error(f"{deck_short}: emoji in French field «{french}»")

        # [6/7] Bold text in ExampleFrench should relate to French field
        example_fr = row.get('ExampleFrench', '')
        if example_fr:
            bold_matches = _BOLD_RE.findall(example_fr)
            if not bold_matches:
                errors.warning(
                    f"{deck_short}: ExampleFrench has no <b> highlight for «{french}»"
                )
            else:
                # Check that bold text relates to French field
                # Skip verbs — conjugated forms differ too much from infinitive
                wt = row.get('WordType', '').strip()
                if wt != 'v':
                    french_lower = strip_html(french).lower()
                    bold_text = ' '.join(b.lower() for b in bold_matches)
                    skip = {'un', 'une', 'le', 'la', 'les', 'l', 'des', 'du', 'de', 'd'}
                    # Split on ; , / and whitespace to get individual keywords
                    keywords = re.split(r"[;,/]\s*|\s+", french_lower)
                    keywords = [k for k in keywords if k not in skip and len(k) > 2]

                    if keywords:
                        found = any(k in bold_text for k in keywords)
                        if not found:
                            errors.warning(
                                f"{deck_short}: <b> text «{'|'.join(bold_matches[:2])}» "
                                f"doesn't match «{french}»"
                            )

    return rows


def validate_conj_rows(rows: list[dict], deck_short: str, errors: BuildErrors):
    """Validate conjugation rows — check cloze markup."""
    for row in rows:
        verb = row.get('Verb', '').strip()
        if not verb:
            errors.error(f"{deck_short}: empty Verb field")
            continue

        # [23] Cloze markup required in ConjSingular or ConjPlural
        singular = row.get('ConjSingular', '')
        plural = row.get('ConjPlural', '')
        has_cloze = _CLOZE_RE.search(singular) or _CLOZE_RE.search(plural)
        if not has_cloze:
            errors.error(
                f"{deck_short}: no {{{{c1::}}}} cloze markup for «{verb}»"
            )

        # [8] Check cloze balance — every {{cN:: must have matching }}
        for field_name, field_val in [('ConjSingular', singular), ('ConjPlural', plural)]:
            open_count = len(_CLOZE_OPEN_RE.findall(field_val))
            close_count = len(_CLOZE_BALANCED_RE.findall(field_val))
            if open_count != close_count:
                errors.error(
                    f"{deck_short}: unbalanced cloze in {field_name} for «{verb}» "
                    f"({open_count} opened, {close_count} closed)"
                )


def validate_count(actual: int, expected: int, deck_short: str, errors: BuildErrors):
    """Check actual row count against deck_config expected count."""
    if actual != expected:
        diff = actual - expected
        sign = "+" if diff > 0 else ""
        errors.error(
            f"{deck_short}: expected {expected} rows, got {actual} ({sign}{diff})"
        )

# =============================================================================
# IDs (must be stable for Anki updates)
# =============================================================================

def stable_id(name: str) -> int:
    """Generate stable ID from name."""
    return int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)

VOCAB_MODEL_ID = stable_id("French Vocabulary v4 FR-RU")
CLOZE_MODEL_ID = stable_id("French Conjugation v4 Cloze")

# =============================================================================
# CSS Styles
# =============================================================================

VOCAB_CSS = """
.card {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 22px;
    text-align: center;
    color: #333;
    background-color: #fafafa;
    padding: 20px;
    max-width: 650px;
    margin: 0 auto;
}
.main-word {
    font-size: 38px;
    font-weight: bold;
    margin-bottom: 20px;
    padding: 15px;
    border-radius: 10px;
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
    color: #333;
}
.night_mode .main-word {
    background: linear-gradient(135deg, #3a3a3a 0%, #2a2a2a 100%);
    color: #f0f0f0;
}
.main-word.gender-m { color: #1565c0; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); }
.main-word.gender-f { color: #c2185b; background: linear-gradient(135deg, #fce4ec 0%, #f8bbd9 100%); }
.main-word.gender-v { color: #2e7d32; background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); }
.main-word.gender-adj { color: #7b1fa2; background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); }
.main-word.gender-adv { color: #00838f; background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); }
.main-word.gender-conj { color: #ef6c00; background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); }
.main-word.gender-prep { color: #5d4037; background: linear-gradient(135deg, #efebe9 0%, #d7ccc8 100%); }
.main-word.gender-pron { color: #455a64; background: linear-gradient(135deg, #eceff1 0%, #cfd8dc 100%); }
.main-word.gender-num { color: #6a1b9a; background: linear-gradient(135deg, #f3e5f5 0%, #ce93d8 100%); }
.main-word.gender-interj { color: #d84315; background: linear-gradient(135deg, #fbe9e7 0%, #ffccbc 100%); }
.main-word.gender-expr { color: #00695c; background: linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 100%); }
.main-word.gender-m_f { color: #4a148c; background: linear-gradient(135deg, #e3f2fd 0%, #fce4ec 100%); }
.main-word.gender-f_pl { color: #c2185b; background: linear-gradient(135deg, #fce4ec 0%, #f8bbd9 100%); }
.main-word.gender-m_pl { color: #1565c0; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); }
.main-word.gender-loc_adv { color: #00838f; background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); }
.gender-tag {
    font-size: 14px;
    padding: 3px 10px;
    border-radius: 12px;
    margin-left: 10px;
    font-weight: normal;
    vertical-align: middle;
}
.gender-tag.gender-m { background-color: #1565c0; color: white; }
.gender-tag.gender-f { background-color: #c2185b; color: white; }
.gender-tag.gender-v { background-color: #2e7d32; color: white; }
.gender-tag.gender-adj { background-color: #7b1fa2; color: white; }
.gender-tag.gender-adv { background-color: #00838f; color: white; }
.gender-tag.gender-conj { background-color: #ef6c00; color: white; }
.gender-tag.gender-prep { background-color: #5d4037; color: white; }
.gender-tag.gender-pron { background-color: #455a64; color: white; }
.gender-tag.gender-num { background-color: #6a1b9a; color: white; }
.gender-tag.gender-interj { background-color: #d84315; color: white; }
.gender-tag.gender-expr { background-color: #00695c; color: white; }
.gender-tag.gender-m_f { background: linear-gradient(135deg, #1565c0 50%, #c2185b 50%); color: white; }
.gender-tag.gender-f_pl { background-color: #c2185b; color: white; }
.gender-tag.gender-m_pl { background-color: #1565c0; color: white; }
.gender-tag.gender-loc_adv { background-color: #00838f; color: white; }
.gender-tag.gender-other { background-color: #616161; color: white; }
.answer-word { background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); color: #2e7d32; }
.example {
    font-size: 20px;
    color: #444;
    margin: 20px 0;
    padding: 18px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: left;
    line-height: 1.5;
}
.example b { color: #d84315; background-color: #fff3e0; padding: 2px 4px; border-radius: 4px; }
.translation { font-size: 28px; color: #333; margin: 20px 0; padding: 10px; }
.night_mode .translation { color: #f5f5f5; }
.emoji { font-size: 32px; margin-right: 10px; vertical-align: middle; }
.example-translation { font-size: 16px; color: #666; margin-top: 12px; padding-top: 12px; border-top: 1px dashed #ddd; font-style: italic; }
.notes { font-size: 15px; color: #555; margin-top: 20px; padding: 12px; background-color: #fff8e1; border-radius: 8px; text-align: left; border-left: 4px solid #ffc107; }
hr { border: none; border-top: 2px solid #e0e0e0; margin: 25px 0; }
.direction { font-size: 12px; color: #999; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }
.audio-inline { margin-left: 10px; }
"""

CLOZE_CSS = """
.card {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 22px;
    text-align: center;
    color: #333;
    background-color: #f0fdf4;
    padding: 20px;
    max-width: 700px;
    margin: 0 auto;
}
.verb-header { font-size: 36px; font-weight: bold; color: #2e7d32; margin-bottom: 10px; }
.verb-translation { font-size: 20px; color: #666; margin-bottom: 20px; }
.pattern { font-size: 14px; color: #1b5e20; background-color: #c8e6c9; padding: 5px 15px; border-radius: 15px; display: inline-block; margin-bottom: 20px; }
.conjugation { font-size: 24px; line-height: 2; text-align: left; padding: 20px 30px; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: inline-block; }
.cloze { font-weight: bold; color: #d84315; background-color: #fff3e0; padding: 2px 6px; border-radius: 4px; }
.pronoun { color: #666; min-width: 50px; display: inline-block; }
.notes { font-size: 15px; color: #555; margin-top: 20px; padding: 12px; background-color: #fff8e1; border-radius: 8px; text-align: left; border-left: 4px solid #ffc107; }
.group-label { font-size: 12px; color: #888; margin: 15px 0 5px 0; }
"""

# =============================================================================
# Templates
# =============================================================================

RECOG_FRONT = r"""
<div class="direction">FR → RU</div>
<div class="main-word" id="main-word">{{French}}<span class="gender-tag" id="gender-tag">{{WordType}}</span>{{#Audio}}<span class="audio-inline">{{Audio}}</span>{{/Audio}}</div>
<script>
(function() {
    var g = '{{WordType}}'.trim().toLowerCase().replace('/', '_').replace(/\s+/g, '_');
    var mw = document.getElementById('main-word');
    var gt = document.getElementById('gender-tag');
    var types = ['m','f','m_f','m_pl','f_pl','v','adj','adv','loc_adv','conj','prep','pron','num','interj','expr'];
    if (types.includes(g)) { mw.classList.add('gender-' + g); gt.classList.add('gender-' + g); }
    else { gt.classList.add('gender-other'); }
})();
</script>
"""

RECOG_BACK = r"""
<div class="direction">FR → RU</div>
<div class="main-word" id="main-word">{{French}}<span class="gender-tag" id="gender-tag">{{WordType}}</span>{{#Audio}}<span class="audio-inline">{{Audio}}</span>{{/Audio}}</div>
{{#ExampleFrench}}<div class="example">{{ExampleFrench}}{{#AudioExample}}<span class="audio-inline">{{AudioExample}}</span>{{/AudioExample}}</div>{{/ExampleFrench}}
<hr>
<div class="main-word answer-word">{{#Emoji}}<span class="emoji">{{Emoji}}</span>{{/Emoji}}{{Russian}}</div>
{{#ExampleRussian}}<div class="example"><div class="example-translation">{{ExampleRussian}}</div></div>{{/ExampleRussian}}
{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
<script>
(function() {
    var g = '{{WordType}}'.trim().toLowerCase().replace('/', '_').replace(/\s+/g, '_');
    var mw = document.getElementById('main-word');
    var gt = document.getElementById('gender-tag');
    var types = ['m','f','m_f','m_pl','f_pl','v','adj','adv','loc_adv','conj','prep','pron','num','interj','expr'];
    if (types.includes(g)) { mw.classList.add('gender-' + g); gt.classList.add('gender-' + g); }
    else { gt.classList.add('gender-other'); }
})();
</script>
"""

PROD_FRONT = """
<div class="direction">RU → FR</div>
<div class="main-word">{{Russian}}</div>
{{#ExampleRussian}}<div class="example">{{ExampleRussian}}</div>{{/ExampleRussian}}
"""

PROD_BACK = r"""
<div class="direction">RU → FR</div>
<div class="main-word">{{Russian}}</div>
{{#ExampleRussian}}<div class="example">{{ExampleRussian}}</div>{{/ExampleRussian}}
<hr>
<div class="main-word" id="main-word">{{#Emoji}}<span class="emoji">{{Emoji}}</span>{{/Emoji}}{{French}}<span class="gender-tag" id="gender-tag">{{WordType}}</span>{{#Audio}}<span class="audio-inline">{{Audio}}</span>{{/Audio}}</div>
{{#ExampleFrench}}<div class="example">{{ExampleFrench}}{{#AudioExample}}<span class="audio-inline">{{AudioExample}}</span>{{/AudioExample}}</div>{{/ExampleFrench}}
{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
<script>
(function() {
    var g = '{{WordType}}'.trim().toLowerCase().replace('/', '_').replace(/\s+/g, '_');
    var mw = document.getElementById('main-word');
    var gt = document.getElementById('gender-tag');
    var types = ['m','f','m_f','m_pl','f_pl','v','adj','adv','loc_adv','conj','prep','pron','num','interj','expr'];
    if (types.includes(g)) { mw.classList.add('gender-' + g); gt.classList.add('gender-' + g); }
    else { gt.classList.add('gender-other'); }
})();
</script>
"""

CLOZE_TEMPLATE = """
<div class="verb-header">{{Verb}}</div>
<div class="verb-translation">{{Translation}}</div>
{{#Pattern}}<div class="pattern">{{Pattern}}</div>{{/Pattern}}
<div class="group-label">Singulier</div>
<div class="conjugation">{{cloze:ConjSingular}}</div>
<div class="group-label">Pluriel</div>
<div class="conjugation">{{cloze:ConjPlural}}</div>
{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
"""

# =============================================================================
# Models
# =============================================================================

vocab_model = genanki.Model(
    VOCAB_MODEL_ID,
    'French Vocabulary v4 (FR-RU)',
    fields=[
        {'name': 'French'},
        {'name': 'Russian'},
        {'name': 'WordType'},
        {'name': 'ExampleFrench'},
        {'name': 'ExampleRussian'},
        {'name': 'Notes'},
        {'name': 'Emoji'},
        {'name': 'Audio'},
        {'name': 'AudioExample'},
    ],
    templates=[
        {'name': 'Recognition (FR→RU)', 'qfmt': RECOG_FRONT, 'afmt': RECOG_BACK},
        {'name': 'Production (RU→FR)', 'qfmt': PROD_FRONT, 'afmt': PROD_BACK},
    ],
    css=VOCAB_CSS,
)

cloze_model = genanki.Model(
    CLOZE_MODEL_ID,
    'French Conjugation v4 (Cloze)',
    model_type=genanki.Model.CLOZE,
    fields=[
        {'name': 'Verb'},
        {'name': 'Translation'},
        {'name': 'ConjSingular'},
        {'name': 'ConjPlural'},
        {'name': 'Pattern'},
        {'name': 'Notes'},
    ],
    templates=[{'name': 'Conjugation Cloze', 'qfmt': CLOZE_TEMPLATE, 'afmt': CLOZE_TEMPLATE}],
    css=CLOZE_CSS,
)

# =============================================================================
# Audio helpers
# =============================================================================

class MediaCollector:
    """
    Collects audio files and handles filename uniqueness for Anki.

    Anki stores all media in a flat folder, so filenames must be unique.
    This class adds category prefixes to ensure uniqueness.
    """

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.files: dict[str, Path] = {}  # anki_name -> source_path
        self.conflicts: list[str] = []
        self.missing_count = 0

    def add_file(self, source_path: Path, anki_name: str) -> bool:
        """
        Register a file for inclusion in the Anki package.

        Returns True if added successfully, False if conflict detected.
        """
        if anki_name in self.files:
            existing = self.files[anki_name]
            if existing != source_path:
                self.conflicts.append(
                    f"  {anki_name}: {source_path} vs {existing}"
                )
                return False
        self.files[anki_name] = source_path
        return True

    def get_media_paths(self) -> list[str]:
        """
        Copy files to temp directory with Anki-safe names and return paths.

        Tracks missing files for diagnostics.
        """
        result = []
        self.missing_count = 0
        for anki_name, source_path in self.files.items():
            if source_path.exists():
                dest = self.temp_dir / anki_name
                shutil.copy2(source_path, dest)
                result.append(str(dest))
            else:
                self.missing_count += 1
        return result

    def report_issues(self):
        """Print any conflicts or missing files detected."""
        if self.conflicts:
            print(f"  ⚠️  Filename conflicts: {len(self.conflicts)}")
            for conflict in self.conflicts[:5]:
                print(conflict)
            if len(self.conflicts) > 5:
                print(f"  ... and {len(self.conflicts) - 5} more")
        if self.missing_count > 0:
            print(f"  ⚠️  Missing files: {self.missing_count}")


def get_audio_field(
    french: str,
    audio_dir: Path,
    prefix: str,
    suffix: str,
    collector: MediaCollector | None,
) -> str:
    """
    Get Anki audio field value for a French word.

    Args:
        french: French text to find audio for
        audio_dir: Directory where audio file is stored
        prefix: Category prefix for unique Anki filename
        suffix: File suffix ("" for word, "_ex" for example)
        collector: MediaCollector to register file with

    Returns [sound:prefixed_filename.mp3] if file exists, empty string otherwise.
    """
    slug = slugify(french)
    source_filename = f"{slug}{suffix}.mp3"
    source_path = audio_dir / source_filename

    if not source_path.exists():
        return ""

    # Create unique Anki filename with prefix
    anki_filename = f"{prefix}{slug}{suffix}.mp3"

    if collector:
        collector.add_file(source_path, anki_filename)

    return f"[sound:{anki_filename}]"


# =============================================================================
# Helpers
# =============================================================================

def read_csv(path: Path) -> list[dict]:
    """Read CSV file and return list of dicts. Handles BOM."""
    if not path.exists():
        print(f"  Warning: {path} not found")
        return []
    with open(path, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def get_audio_context(
    source: Path,
    include_audio: bool,
) -> tuple[Path | None, str]:
    """
    Get audio directory and prefix for a source file.

    Returns (audio_dir, audio_prefix) tuple.
    If include_audio is False, returns (None, "").
    """
    if not include_audio:
        return None, ""
    return get_audio_dir(source), get_audio_prefix(source, CONTENT_DIR)


def _note_guid(tag: str, key: str) -> str:
    """
    Generate unique guid from tag + key.

    Prevents Anki from merging notes with same French/Verb across decks
    (e.g. «barrer» in B1 vocabulary vs «barrer» in Expressions).
    """
    return hashlib.sha256(f"{tag}:{key}".encode()).hexdigest()[:10]


def create_vocab_note(
    row: dict,
    tag: str,
    audio_dir: Path | None = None,
    audio_prefix: str = "",
    collector: MediaCollector | None = None,
) -> genanki.Note:
    """Create vocabulary note from CSV row."""
    french = row.get('French', '')

    # Get audio fields if directory provided
    audio = ""
    audio_example = ""
    if audio_dir:
        audio = get_audio_field(french, audio_dir, audio_prefix, "", collector)
        audio_example = get_audio_field(french, audio_dir, audio_prefix, "_ex", collector)

    fields = [
        french,
        row.get('Russian', ''),
        row.get('WordType', ''),
        row.get('ExampleFrench', ''),
        row.get('ExampleRussian', ''),
        row.get('Notes', ''),
        row.get('Emoji', ''),
        audio,
        audio_example,
    ]
    return genanki.Note(
        model=vocab_model,
        fields=fields,
        tags=[tag],
        guid=_note_guid(tag, french),
    )


def create_conj_note(row: dict, tag: str) -> genanki.Note:
    """Create conjugation note from CSV row."""
    fields = [
        row.get('Verb', ''),
        row.get('Translation', ''),
        row.get('ConjSingular', ''),
        row.get('ConjPlural', ''),
        row.get('Pattern', ''),
        row.get('Notes', ''),
    ]
    return genanki.Note(
        model=cloze_model,
        fields=fields,
        tags=[tag],
        guid=_note_guid(tag, row.get('Verb', '')),
    )


# =============================================================================
# Main
# =============================================================================

def build_deck(output_path: str = "French_TEF_TCF.apkg", include_audio: bool = True):
    """Build complete Anki deck."""
    print("=" * 60)
    print("Building Anki Deck")
    print("=" * 60)

    errors = BuildErrors()
    decks = {}
    stats = {}
    # Track duplicates within vocabulary group (A1-C1 + Autres)
    seen_vocab: Counter = Counter()
    # Track audio coverage
    total_audio_expected = 0
    total_audio_missing = 0

    # Use context manager for automatic cleanup of temp directory
    with tempfile.TemporaryDirectory(prefix="anki_audio_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        collector = MediaCollector(temp_dir) if include_audio else None

        # Helper to get or create deck
        def get_deck(name: str) -> genanki.Deck:
            if name not in decks:
                decks[name] = genanki.Deck(stable_id(name), name)
            return decks[name]

        def process_vocab_deck(deck_name, info, tag, seen_counter):
            nonlocal total_audio_expected, total_audio_missing
            source = PROJECT_ROOT / info['source']
            rows = read_csv(source)
            deck = get_deck(deck_name)
            short = deck_name.split("::")[-1]

            validate_count(len(rows), info['count'], short, errors)
            audio_dir, audio_prefix = get_audio_context(source, include_audio)
            validate_vocab_rows(rows, short, seen_counter, errors, include_audio, audio_dir)

            deck_missing = 0
            for row in rows:
                if not row.get('WordType'):
                    row['WordType'] = 'expr'
                note = create_vocab_note(row, tag, audio_dir, audio_prefix, collector)
                deck.add_note(note)

                # Track audio coverage
                if include_audio and audio_dir:
                    total_audio_expected += 1
                    french = row.get('French', '').strip()
                    if french:
                        slug = slugify(french)
                        if not (audio_dir / f"{slug}.mp3").exists():
                            deck_missing += 1

            if deck_missing > 0:
                errors.warning(f"{short}: {deck_missing} entries missing word audio")
            total_audio_missing += deck_missing

            stats[deck_name] = len(rows)
            print(f"  {short}: {len(rows)} entries")

        # Process vocabulary decks (shared duplicate tracker)
        print("\n--- Vocabulary ---")
        for deck_name, info in VOCABULARY_DECKS.items():
            tag = deck_name.split("::")[-1].lower().replace(" ", "_").replace("+", "plus")
            process_vocab_deck(deck_name, info, tag, seen_vocab)

        for deck_name, info in AUTRES_DECK.items():
            process_vocab_deck(deck_name, info, 'autres', seen_vocab)

        # Content decks (separate duplicate trackers — polysemy is expected)
        print("\n--- Content ---")
        for deck_name, info in CONTENT_DECKS.items():
            tag = deck_name.split("::")[-1].lower()
            seen_content: Counter = Counter()
            process_vocab_deck(deck_name, info, tag, seen_content)

        # Process conjugation decks
        print("\n--- Conjugation ---")
        for deck_name, info in CONJUGATION_DECKS.items():
            source = PROJECT_ROOT / info['source']
            rows = read_csv(source)
            deck = get_deck(deck_name)
            short = deck_name.split("::")[-1]
            tag = short.lower().replace(" ", "_")

            validate_count(len(rows), info['count'], short, errors)

            # [23] Only validate cloze for decks that use ConjSingular/ConjPlural
            if 'ConjSingular' in (rows[0] if rows else {}):
                validate_conj_rows(rows, short, errors)

            for row in rows:
                deck.add_note(create_conj_note(row, tag))

            stats[deck_name] = len(rows)
            print(f"  {short}: {len(rows)} entries")

        # [21] Check stable_id collisions across all decks and models
        print("\n--- Integrity ---")
        all_ids: dict[int, str] = {}
        for name in decks:
            sid = stable_id(name)
            if sid in all_ids:
                errors.error(f"stable_id collision: «{name}» and «{all_ids[sid]}»")
            all_ids[sid] = name
        for label, mid in [("vocab_model", VOCAB_MODEL_ID), ("cloze_model", CLOZE_MODEL_ID)]:
            if mid in all_ids:
                errors.error(f"stable_id collision: model {label} and deck «{all_ids[mid]}»")
            all_ids[mid] = label
        print(f"  ✅ {len(all_ids)} unique IDs (no collisions)")

        # Fail fast on validation errors
        if errors.has_errors():
            errors.summary()
            print("\nBuild aborted. Fix errors above and retry.")
            sys.exit(1)

        # Collect media files with unique names
        media_files: list[str] = []
        if collector:
            print(f"\n--- Audio ---")
            media_files = collector.get_media_paths()
            print(f"  Collected {len(media_files)} audio files")
            if total_audio_missing > 0:
                print(f"  Missing: {total_audio_missing}/{total_audio_expected} word audio files")
            collector.report_issues()

            # [19] Check for orphaned audio files
            all_audio_dirs = set()
            for deck_name, info in {**VOCABULARY_DECKS, **AUTRES_DECK, **CONTENT_DECKS}.items():
                source = PROJECT_ROOT / info['source']
                all_audio_dirs.add(get_audio_dir(source))

            referenced_files: set[str] = set()
            for deck_name, info in {**VOCABULARY_DECKS, **AUTRES_DECK, **CONTENT_DECKS}.items():
                source = PROJECT_ROOT / info['source']
                rows = read_csv(source)
                audio_dir = get_audio_dir(source)
                for row in rows:
                    french = row.get('French', '').strip()
                    if french:
                        slug = slugify(french)
                        referenced_files.add(str(audio_dir / f"{slug}.mp3"))
                        referenced_files.add(str(audio_dir / f"{slug}_ex.mp3"))

            orphaned = 0
            for audio_dir in all_audio_dirs:
                if audio_dir.exists():
                    for mp3 in audio_dir.glob("*.mp3"):
                        if str(mp3) not in referenced_files:
                            orphaned += 1
            if orphaned > 0:
                errors.warning(f"{orphaned} orphaned audio files across content/audio/")
            else:
                print(f"  ✅ No orphaned audio files")

        # Create package
        print("\n--- Exporting ---")
        all_decks = list(decks.values())
        package = genanki.Package(all_decks)

        if media_files:
            package.media_files = media_files

        package.write_to_file(output_path)

        # Summary
        total_entries = sum(stats.values())
        conj_deck_names = set(CONJUGATION_DECKS.keys())
        vocab_entries = sum(v for k, v in stats.items() if k not in conj_deck_names)
        conj_entries = sum(v for k, v in stats.items() if k in conj_deck_names)
        total_cards = vocab_entries * 2 + conj_entries

        print(f"\nSaved: {output_path}")
        print(f"Decks: {len(decks)}")
        print(f"Entries: {total_entries}")
        print(f"Cards: ~{total_cards} (vocab {vocab_entries}×2 + conj {conj_entries})")
        if media_files:
            print(f"Audio files: {len(media_files)}")
        errors.summary()

        return stats


def main():
    parser = argparse.ArgumentParser(description="Build Anki deck from content files")
    parser.add_argument("--output", "-o", default="French_TEF_TCF.apkg", help="Output file path")
    parser.add_argument("--no-audio", action="store_true", help="Skip audio fields")
    args = parser.parse_args()

    build_deck(args.output, include_audio=not args.no_audio)


if __name__ == "__main__":
    main()
