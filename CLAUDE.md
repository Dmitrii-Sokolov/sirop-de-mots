# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

French language learning tools based on Lexique383 database. The project extracts, analyzes, and formats French vocabulary data for Anki flashcard decks targeting TEF/TCF preparation.

## Data Source

- **Lexique383.tsv** — Main database from http://www.lexique.org (~140,000 French words)
- Key columns: `ortho` (spelling), `lemme` (lemma), `cgram` (grammar category), `genre` (gender m/f), `freqlemfilms2`/`freqlemlivres` (frequency)
- Filter by `islem=1` for lemmas only

## Scripts

All Python scripts use pandas for data processing.

**Important:** Scripts contain emoji in output, run with UTF-8 encoding:
```bash
PYTHONIOENCODING=utf-8 python <script.py>
```

```bash
# Extract lemma selection (top 10k VER/NOM/ADJ/ADV + all other categories)
PYTHONIOENCODING=utf-8 python extract_lexique_selection.py

# Count lemmas by grammatical category → lemma_type_stats.csv
PYTHONIOENCODING=utf-8 python count_lemma_types.py

# Generate Anki deck (.apkg) with demo cards
PYTHONIOENCODING=utf-8 python create_french_deck_v3.py
```

## Anki Card Format

Two note types in `French_Learning_Deck_v3.apkg`:

**Vocabulary (French Vocabulary v3 FR-RU):**
- Fields: French, Russian, WordType, ExampleFrench, ExampleRussian, Notes, Emoji, Audio, AudioExample
- Nouns must include article: `une maison`, `l'immigration (f)`
- Adjectives with both forms: `grand, grande` (variable) or `possible` (invariable)
- WordType codes: `m`/`f` (noun gender), `v`, `adj`, `adv`, `conj`, `prep`, `pron`, `num`, `interj`, `expr`, `loc`
- Examples use `<b>...</b>` for keyword highlighting

**Adjective Format Rules (3 types):**
- **Regular** (m + e = f): `petit, petite`, `grand, grande`, `français, française`
- **Invariable** (m = f): `rouge`, `possible`, `facile`, `rapide`
- **Irregular** (unique f-form): `beau, belle`, `vieux, vieille`, `nouveau, nouvelle`, `fou, folle`

Notes field MUST specify adjective type:
- Regular: `+e au féminin`
- Invariable: `invariable`
- Irregular: create **separate cards** for each form (e.g., one card for `beau`, another for `belle`)

**Profession Nouns (m/f pairs):**
Nouns denoting people/professions have both gender forms. Create **separate cards** for each:
- `un étudiant` (m) + `une étudiante` (f)
- `un acteur` (m) + `une actrice` (f)
- `un chanteur` (m) + `une chanteuse` (f)
- `un directeur` (m) + `une directrice` (f)

Common patterns:
- **-eur → -euse**: chanteur/chanteuse, vendeur/vendeuse
- **-teur → -trice**: acteur/actrice, directeur/directrice
- **-ien → -ienne**: musicien/musicienne, pharmacien/pharmacienne
- **-er → -ère**: boulanger/boulangère, infirmier/infirmière

**Conjugation (French Conjugation v3 Cloze):**
- Fields: Verb, Translation, Tense, ConjSingular, ConjPlural, Notes
- Uses cloze deletions: `{{c1::vais}}` for singular, `{{c2::allons}}` for plural

## Frequency Recommendation

For TEF/TCF use combined frequency:
```python
freq_combined = 0.6 * freqlemfilms2 + 0.4 * freqlemlivres
```
Films weighted higher for oral comprehension testing.

## Output Files

**Data extraction:**
- `categories/` — Filtered lemmas by category (NOM.csv, VER.csv, ADJ.csv, ADV.csv, etc.)
  - Columns: `lemme`, `cgram`, `genre`, `freqlem`, `forms`
  - Top 10k VER/NOM/ADJ/ADV by frequency + all rare categories
- `lemma_type_stats.csv` — Lemma count by grammatical category

**Anki import files:**
- `French_Vocabulary_Import.csv` — Vocabulary cards for Anki import
- `French_Conjugation_Import.csv` — Conjugation cards for Anki import
- `French_200_Verbs_Conjugation.csv` — 200 verbs conjugation data
- `French_Learning_Deck_v3.apkg` — Complete Anki deck with demo cards

## Card Generation Instructions

Two detailed instructions for generating CSV files with Claude:

- **`INSTRUCTION_Generate_French_CSV.md`** — Vocabulary cards format:
  - Fields: French, Russian, WordType, ExampleFrench, ExampleRussian, Notes, Emoji
  - Rules for articles, Quebec French priority, memorable examples
  - Checklist before output

- **`INSTRUCTION_Generate_French_Conjugation_CSV.md`** — Conjugation cards format:
  - Fields: Verb, Translation, Tense, ConjSingular, ConjPlural, Notes
  - Cloze syntax (`{{c1::...}}`, `{{c2::...}}`)
  - Examples for all tenses, priority verbs, TEF/TCF study order

## Data Analysis Files

**Completed analysis (in `data/`):**
- `nom_without_genre.csv` — 547 NOM with genre=NaN, fully classified (homograph/common_gender/f_only/m_only)
- `gender_homographs.csv` — 98 true gender homographs (livre m=book, f=pound)
- `irregular_adjectives.csv` — 534 irregular adjectives with m/f forms and patterns
- `professions_check.csv` — 875 NOM with both m/f forms + 490 m-only with profession suffixes
- `m_only_profession_reviewed.csv` — Manual review of 490 m-only nouns (267 objects, 188 persons)
- `missing_f_forms.csv` — 188 persons requiring f-form consideration (141 add_f, 38 m_only, etc.)

**Lexique383 structure for professions:**
Feminine forms stored as `ortho` with same `lemme`:
```
lemme=acteur → ortho: acteur(m.s), actrice(f.s), acteurs(m.p), actrices(f.p)
```
To find m/f pairs, query by genre+nombre within same lemme, not by separate lemmas.

## Pipeline Scripts

Located in `scripts/`:
- `config.py` — Central configuration (paths, thresholds, patterns)
- `01_extract_categories.py` — Extract categories from Lexique383
- `04a_find_nom_without_genre.py` — Find NOM without genre
- `04b_check_professions.py` — Check m/f pairs for professions
- `04c_find_irregular_adj.py` — Find irregular adjectives

## TODO

See `.claude/plan-anki-pipeline.md` for full pipeline plan.

### Pending tasks
- [ ] `04d_find_irregular_verbs.py` — Extract 3rd group irregular verbs
- [ ] `blacklist.csv` — Create list of words to exclude (archaic, composite numerals)
- [ ] `whitelist_numerals.csv` — Basic numerals to include (un, deux, trois... cent, mille)
- [ ] Pipeline automation scripts (00, 02, 03, 05, 06, 07, run_pipeline.py)
- [ ] Azure TTS audio generation
- [ ] Final .apkg assembly with audio
