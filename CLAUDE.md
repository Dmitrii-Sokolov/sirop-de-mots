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
- `irregular_verbs.csv` — 338 irregular verbs (3rd group) with conjugation patterns
- `professions_check.csv` — 875 NOM with both m/f forms + 490 m-only with profession suffixes
- `m_only_profession_reviewed.csv` — Manual review of 490 m-only nouns (267 objects, 188 persons)
- `missing_f_forms.csv` — 188 persons requiring f-form consideration (141 add_f, 38 m_only, etc.)
- `blacklist.csv` — 93 entries to exclude (composite numerals, parse errors, roman numerals)
- `whitelist_numerals.csv` — 35 basic numerals to include (un-dix-neuf, tens, cent, mille)

**Québécismes raw sources (in `data/quebecismes/`):**
- `oqlf_termes_officialises.csv` — 1471 official OQLF terms (from Données Québec)
- `cameleon_quebecismes.csv` — 544 québécismes with definitions (from lecameleon.eu)
- `wiktionary_quebecismes.csv` — 2968 words from fr.wiktionary "français du Québec" category
- `exionnaire_quebecismes.csv` — 225 words (from exionnaire.com)

**Expressions & Idioms (in `data/`):**
- `all_expressions.csv` — **469 expressions** in final Anki format (French, Russian, WordType, ExampleFrench, ExampleRussian, Notes, Emoji, Source)
- `expressions_idiomatiques.csv` — 67 French idioms (avoir le cafard, poser un lapin, etc.)
- `expressions_quebecoises.csv` — 40 Quebec expressions (tiguidou, attache ta tuque, etc.)
- `vocabulaire_quebecois.csv` — 50 Quebec vocabulary (char, blonde, dépanneur, etc.)
- `sacres_quebecois.csv` — 18 Quebec swear words (tabarnak, câlice + euphemisms)
- `proverbes_francais.csv` — 58 French proverbs with Russian equivalents
- `connecteurs_logiques.csv` — 67 logical connectors for TEF B2 (cependant, néanmoins, etc.)
- `constructions_verbales.csv` — 52 verbal constructions (avoir beau, être censé, il s'agit de, etc.)
- `expressions_opinion.csv` — 40 opinion expressions (à mon avis, je trouve que, etc.)
- `expressions_temps.csv` — 39 time expressions (désormais, au fur et à mesure, etc.)
- `fillers_formules.csv` — 38 fillers and formal phrases (du coup, veuillez agréer, etc.)

**Additions (in `additions/`):**
- `professions_f.csv` — 141 feminine forms missing from Lexique383 (lieutenante, ingénieure, etc.)
- `quebecismes.csv` — 566 québécismes with Russian translations (309 HIGH + 257 MEDIUM priority)
  - Format: word, pos, definition, translation, sources, priority
  - Needs: examples (ExampleFrench, ExampleRussian), emoji for Anki conversion

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
- `04d_find_irregular_verbs.py` — Find 3rd group irregular verbs
- `05_generate_cards.py` — **Generate card skeletons** from categories + additions
- `06_fetch_quebecismes.py` — Fetch québécismes from 4 sources (OQLF, Caméléon, Wiktionary, Exionnaire)
- `07_merge_quebecismes.py` — Merge and deduplicate québécismes
- `08_filter_quebecismes.py` — Filter by definition presence, add Lexique383 frequency

**Output from 05_generate_cards.py (in `output/`):**
- `vocabulary_skeleton.csv` — 11261 entries (French, WordType, Notes, Source, freqlem, Priority)
  - Includes verbs (infinitive form) for translation cards
- `conjugation_skeleton.csv` — 2088 verbs (Verb, Notes, freqlem, Group)
  - For conjugation table generation
- `expressions.csv` — 469 expressions (copy of all_expressions, already complete)

**Verb group classification:**
- 1st group: -er verbs (regular, except "aller")
- 2nd group: -ir with -issant participle (finir → finissant)
- 3rd group: all others (irregular) — -ir sans -issant, -re, -oir, aller

## Québécismes Sources

External sources for Quebec French vocabulary:
- **Données Québec** (donneesquebec.ca) — Official OQLF terminology, CSV download
- **Le Caméléon** (lecameleon.eu) — ~650 québécismes with definitions
- **Wiktionary** (fr.wiktionary.org) — Category "français du Québec" via API
- **Exionnaire** (exionnaire.com) — Curated word list

Filtering strategy:
- **HIGH priority** (309 words): confirmed by 2+ sources — core québécismes
- **MEDIUM priority** (257 words): from Caméléon only — conversational, less essential

Most have freq=0 in Lexique383 (France-centric corpus), so source count is better quality signal than frequency.

## TODO

### Completed
- [x] `05_generate_cards.py` — Generate card skeletons (11261 vocab + 2088 conj + 469 expressions)

### Pending tasks
- [ ] AI content fill — Examples, emoji via Claude (translations mostly ready)
- [ ] Azure TTS audio generation (fr-CA voices)
- [ ] Final .apkg assembly with audio
