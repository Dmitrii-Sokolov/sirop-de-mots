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
import shutil
import tempfile
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
from utils import slugify

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

RECOG_FRONT = """
<div class="direction">FR → RU</div>
<div class="main-word" id="main-word">{{French}}<span class="gender-tag" id="gender-tag">{{WordType}}</span>{{#Audio}}<span class="audio-inline">{{Audio}}</span>{{/Audio}}</div>
<script>
(function() {
    var g = '{{WordType}}'.trim().toLowerCase().replace('/', '_');
    var mw = document.getElementById('main-word');
    var gt = document.getElementById('gender-tag');
    var types = ['m','f','m_f','v','adj','adv','conj','prep','pron','num','interj','expr'];
    if (types.includes(g)) { mw.classList.add('gender-' + g); gt.classList.add('gender-' + g); }
    else { gt.classList.add('gender-other'); }
})();
</script>
"""

RECOG_BACK = """
<div class="direction">FR → RU</div>
<div class="main-word" id="main-word">{{French}}<span class="gender-tag" id="gender-tag">{{WordType}}</span>{{#Audio}}<span class="audio-inline">{{Audio}}</span>{{/Audio}}</div>
{{#ExampleFrench}}<div class="example">{{ExampleFrench}}{{#AudioExample}}<span class="audio-inline">{{AudioExample}}</span>{{/AudioExample}}</div>{{/ExampleFrench}}
<hr>
<div class="main-word answer-word">{{#Emoji}}<span class="emoji">{{Emoji}}</span>{{/Emoji}}{{Russian}}</div>
{{#ExampleRussian}}<div class="example"><div class="example-translation">{{ExampleRussian}}</div></div>{{/ExampleRussian}}
{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
<script>
(function() {
    var g = '{{WordType}}'.trim().toLowerCase().replace('/', '_');
    var mw = document.getElementById('main-word');
    var gt = document.getElementById('gender-tag');
    var types = ['m','f','m_f','v','adj','adv','conj','prep','pron','num','interj','expr'];
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

PROD_BACK = """
<div class="direction">RU → FR</div>
<div class="main-word">{{Russian}}</div>
{{#ExampleRussian}}<div class="example">{{ExampleRussian}}</div>{{/ExampleRussian}}
<hr>
<div class="main-word" id="main-word">{{#Emoji}}<span class="emoji">{{Emoji}}</span>{{/Emoji}}{{French}}<span class="gender-tag" id="gender-tag">{{WordType}}</span>{{#Audio}}<span class="audio-inline">{{Audio}}</span>{{/Audio}}</div>
{{#ExampleFrench}}<div class="example">{{ExampleFrench}}{{#AudioExample}}<span class="audio-inline">{{AudioExample}}</span>{{/AudioExample}}</div>{{/ExampleFrench}}
{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
<script>
(function() {
    var g = '{{WordType}}'.trim().toLowerCase().replace('/', '_');
    var mw = document.getElementById('main-word');
    var gt = document.getElementById('gender-tag');
    var types = ['m','f','m_f','v','adj','adv','conj','prep','pron','num','interj','expr'];
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

def get_audio_prefix(source_file: Path) -> str:
    """
    Get unique prefix for audio files based on source category.

    This ensures unique filenames in Anki's flat media storage.

    Examples:
        vocabulary/a1_a2.csv -> "v_a1a2_"
        vocabulary/b1.csv -> "v_b1_"
        expressions/all.csv -> "expr_"
        quebecismes/all.csv -> "qc_"
    """
    rel_path = source_file.relative_to(CONTENT_DIR)
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
        """
        result = []
        for anki_name, source_path in self.files.items():
            if source_path.exists():
                dest = self.temp_dir / anki_name
                shutil.copy2(source_path, dest)
                result.append(str(dest))
        return result

    def report_conflicts(self):
        """Print any filename conflicts detected."""
        if self.conflicts:
            print(f"\n⚠️  Audio filename conflicts detected ({len(self.conflicts)}):")
            for conflict in self.conflicts[:10]:
                print(conflict)
            if len(self.conflicts) > 10:
                print(f"  ... and {len(self.conflicts) - 10} more")


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
    """Read CSV file and return list of dicts."""
    if not path.exists():
        print(f"  Warning: {path} not found")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


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
    return genanki.Note(model=vocab_model, fields=fields, tags=[tag])


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
    return genanki.Note(model=cloze_model, fields=fields, tags=[tag])


# =============================================================================
# Main
# =============================================================================

def build_deck(output_path: str = "French_TEF_TCF.apkg", include_audio: bool = True):
    """Build complete Anki deck."""
    print("="*60)
    print("Building Anki Deck")
    print("="*60)

    decks = {}
    stats = {}

    # Use context manager for automatic cleanup of temp directory
    with tempfile.TemporaryDirectory(prefix="anki_audio_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        collector = MediaCollector(temp_dir) if include_audio else None

        # Helper to get or create deck
        def get_deck(name: str) -> genanki.Deck:
            if name not in decks:
                decks[name] = genanki.Deck(stable_id(name), name)
            return decks[name]

        # Process vocabulary decks
        print("\n--- Vocabulary ---")
        for deck_name, info in VOCABULARY_DECKS.items():
            source = PROJECT_ROOT / info['source']
            rows = read_csv(source)
            deck = get_deck(deck_name)
            tag = deck_name.split("::")[-1].lower().replace(" ", "_").replace("+", "plus")

            # Get audio directory and prefix if audio enabled
            audio_dir, audio_prefix = None, ""
            if include_audio:
                audio_dir = get_audio_dir(source)
                audio_prefix = get_audio_prefix(source)

            for row in rows:
                deck.add_note(create_vocab_note(
                    row, tag, audio_dir, audio_prefix, collector
                ))

            stats[deck_name] = len(rows)
            print(f"  {deck_name.split('::')[-1]}: {len(rows)} entries")

        # Process Autres deck
        for deck_name, info in AUTRES_DECK.items():
            source = PROJECT_ROOT / info['source']
            rows = read_csv(source)
            deck = get_deck(deck_name)

            audio_dir, audio_prefix = None, ""
            if include_audio:
                audio_dir = get_audio_dir(source)
                audio_prefix = get_audio_prefix(source)

            for row in rows:
                deck.add_note(create_vocab_note(
                    row, 'autres', audio_dir, audio_prefix, collector
                ))

            stats[deck_name] = len(rows)
            print(f"  {deck_name.split('::')[-1]}: {len(rows)} entries")

        # Process content decks (expressions, quebecismes)
        print("\n--- Content ---")
        for deck_name, info in CONTENT_DECKS.items():
            source = PROJECT_ROOT / info['source']
            rows = read_csv(source)
            deck = get_deck(deck_name)
            tag = deck_name.split("::")[-1].lower()

            audio_dir, audio_prefix = None, ""
            if include_audio:
                audio_dir = get_audio_dir(source)
                audio_prefix = get_audio_prefix(source)

            for row in rows:
                if not row.get('WordType'):
                    row['WordType'] = 'expr'
                deck.add_note(create_vocab_note(
                    row, tag, audio_dir, audio_prefix, collector
                ))

            stats[deck_name] = len(rows)
            print(f"  {deck_name.split('::')[-1]}: {len(rows)} entries")

        # Process conjugation decks
        print("\n--- Conjugation ---")
        for deck_name, info in CONJUGATION_DECKS.items():
            source = PROJECT_ROOT / info['source']
            rows = read_csv(source)
            deck = get_deck(deck_name)
            tag = deck_name.split("::")[-1].lower().replace(" ", "_")

            for row in rows:
                deck.add_note(create_conj_note(row, tag))

            stats[deck_name] = len(rows)
            print(f"  {deck_name.split('::')[-1]}: {len(rows)} entries")

        # Collect media files with unique names
        media_files: list[str] = []
        if collector:
            print(f"\n--- Audio ---")
            media_files = collector.get_media_paths()
            print(f"  Collected {len(media_files)} audio files")
            collector.report_conflicts()

        # Create package
        print("\n--- Exporting ---")
        all_decks = list(decks.values())
        package = genanki.Package(all_decks)

        if media_files:
            package.media_files = media_files

        package.write_to_file(output_path)

        # Summary
        total_entries = sum(stats.values())
        total_cards = sum(v * 2 for v in stats.values())

        print(f"\nSaved: {output_path}")
        print(f"Decks: {len(decks)}")
        print(f"Entries: {total_entries}")
        print(f"Cards: ~{total_cards}")
        if media_files:
            print(f"Audio files: {len(media_files)}")

        return stats


def main():
    parser = argparse.ArgumentParser(description="Build Anki deck from content files")
    parser.add_argument("--output", "-o", default="French_TEF_TCF.apkg", help="Output file path")
    parser.add_argument("--no-audio", action="store_true", help="Skip audio fields")
    args = parser.parse_args()

    build_deck(args.output, include_audio=not args.no_audio)


if __name__ == "__main__":
    main()
