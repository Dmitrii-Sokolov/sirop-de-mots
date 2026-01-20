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
from pathlib import Path

import genanki

from config import PROJECT_ROOT
from deck_config import (
    ROOT_DECK,
    VOCABULARY_DECKS,
    AUTRES_DECK,
    CONTENT_DECKS,
    CONJUGATION_DECKS,
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
<div class="main-word" id="main-word">{{French}}<span class="gender-tag" id="gender-tag">{{WordType}}</span></div>
{{#ExampleFrench}}<div class="example">{{ExampleFrench}}</div>{{/ExampleFrench}}
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
<div class="main-word" id="main-word">{{French}}<span class="gender-tag" id="gender-tag">{{WordType}}</span></div>
{{#ExampleFrench}}<div class="example">{{ExampleFrench}}</div>{{/ExampleFrench}}
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
<div class="main-word" id="main-word">{{#Emoji}}<span class="emoji">{{Emoji}}</span>{{/Emoji}}{{French}}<span class="gender-tag" id="gender-tag">{{WordType}}</span></div>
{{#ExampleFrench}}<div class="example">{{ExampleFrench}}</div>{{/ExampleFrench}}
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
# Helpers
# =============================================================================

def read_csv(path: Path) -> list[dict]:
    """Read CSV file and return list of dicts."""
    if not path.exists():
        print(f"  Warning: {path} not found")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def create_vocab_note(row: dict, tag: str, include_audio: bool = True) -> genanki.Note:
    """Create vocabulary note from CSV row."""
    fields = [
        row.get('French', ''),
        row.get('Russian', ''),
        row.get('WordType', ''),
        row.get('ExampleFrench', ''),
        row.get('ExampleRussian', ''),
        row.get('Notes', ''),
        row.get('Emoji', ''),
        row.get('Audio', '') if include_audio else '',
        row.get('AudioExample', '') if include_audio else '',
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

        for row in rows:
            deck.add_note(create_vocab_note(row, tag, include_audio))

        stats[deck_name] = len(rows)
        print(f"  {deck_name.split('::')[-1]}: {len(rows)} entries")

    # Process Autres deck
    for deck_name, info in AUTRES_DECK.items():
        source = PROJECT_ROOT / info['source']
        rows = read_csv(source)
        deck = get_deck(deck_name)

        for row in rows:
            deck.add_note(create_vocab_note(row, 'autres', include_audio))

        stats[deck_name] = len(rows)
        print(f"  {deck_name.split('::')[-1]}: {len(rows)} entries")

    # Process content decks (expressions, quebecismes)
    print("\n--- Content ---")
    for deck_name, info in CONTENT_DECKS.items():
        source = PROJECT_ROOT / info['source']
        rows = read_csv(source)
        deck = get_deck(deck_name)
        tag = deck_name.split("::")[-1].lower()

        for row in rows:
            # Expressions/Quebecismes use 'expr' as WordType if not set
            if not row.get('WordType'):
                row['WordType'] = 'expr'
            deck.add_note(create_vocab_note(row, tag, include_audio))

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

    # Create package
    print("\n--- Exporting ---")
    all_decks = list(decks.values())
    package = genanki.Package(all_decks)
    package.write_to_file(output_path)

    # Summary
    total_entries = sum(stats.values())
    total_cards = sum(v * 2 for v in stats.values())  # vocab: 2 templates, conj: 2 clozes

    print(f"\nSaved: {output_path}")
    print(f"Decks: {len(decks)}")
    print(f"Entries: {total_entries}")
    print(f"Cards: ~{total_cards}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Build Anki deck from content files")
    parser.add_argument("--output", "-o", default="French_TEF_TCF.apkg", help="Output file path")
    parser.add_argument("--no-audio", action="store_true", help="Skip audio fields")
    args = parser.parse_args()

    build_deck(args.output, include_audio=not args.no_audio)


if __name__ == "__main__":
    main()
