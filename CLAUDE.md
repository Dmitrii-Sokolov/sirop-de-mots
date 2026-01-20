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

**Conjugation (restructured, pattern-based):**
Five card types instead of all tenses × all verbs:

1. **Présent** (343 cards) — 3e groupe + samples 1er/2e groupe
   - Fields: Verb, Translation, ConjSingular, ConjPlural, Pattern, Notes
   - Cloze: `{{c1::vais}}` singular, `{{c2::allons}}` plural

2. **Subjonctif** (10 cards) — irregular only (être, avoir, aller, faire, etc.)
   - Same cloze format with `que je/tu/il`, `que nous/vous/ils`

3. **Participes passés** (110 cards) — irregular only
   - Fields: Verb, Translation, Participe (cloze), Auxiliaire, Pattern, Related

4. **Futur stems** (22 cards) — irregular only
   - Fields: Verb, Translation, FuturStem (cloze), Example

5. **Être verbs** (17 cards) — DR MRS VANDERTRAMP
   - Fields: Verb, Translation, Participe, Notes

**Total: ~500 cards** (vs ~16700 with old 8-tense approach)

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
- `blacklist.csv` — 183 entries to exclude (composite numerals, parse errors, roman numerals, archaic)

**Québécismes raw sources (in `data/quebecismes/`):**
- `oqlf_termes_officialises.csv` — 1471 official OQLF terms (from Données Québec)
- `cameleon_quebecismes.csv` — 544 québécismes with definitions (from lecameleon.eu)
- `wiktionary_quebecismes.csv` — 2968 words from fr.wiktionary "français du Québec" category
- `exionnaire_quebecismes.csv` — 225 words (from exionnaire.com)

**Expressions & Idioms:**
- `content/expressions/all.csv` — **469 expressions** in final Anki format (complete)

**Expression sources (in `data/`):**
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
- `05b_generate_conjugation.py` — **Generate conjugation skeletons** (restructured, 5 types)
- `06_fetch_quebecismes.py` — Fetch québécismes from 4 sources (OQLF, Caméléon, Wiktionary, Exionnaire)
- `07_merge_quebecismes.py` — Merge and deduplicate québécismes
- `08_filter_quebecismes.py` — Filter by definition presence, add Lexique383 frequency
- `09_generate_audio.py` — **Generate TTS audio** via Azure Speech (fr-CA voices)

**Skeletons (in `output/`, gitignored, regenerable):**

From `05_generate_cards.py`:
- `vocabulary_skeleton.csv` — 10695 entries (French, WordType, Notes, Source, freqlem)
- `quebecismes_skeleton.csv` — 566 entries (French, WordType, Notes, Source, Priority)

From `05b_generate_conjugation.py` (restructured):
- `conj_present_skeleton.csv` — 343 entries (Verb, Group, Pattern, freqlem)
- `conj_subjonctif_skeleton.csv` — 10 entries (Verb, freqlem)
- `conj_participes_skeleton.csv` — 110 entries (Verb, Participe, Auxiliaire, Pattern, Related, freqlem)
- `conj_futur_stems_skeleton.csv` — 22 entries (Verb, FuturStem, freqlem)
- `conj_etre_verbs_skeleton.csv` — 17 entries (Verb, Participe, freqlem)

**AI content (in `content/`, tracked in git):**
- `expressions/all.csv` — 469 expressions (complete, audio needed)
- `quebecismes/all.csv` — 566 québécismes (complete, audio needed)
- `vocabulary/*.csv` — French, Russian, ExampleFrench, ExampleRussian, Emoji
- `conjugation/present.csv` — Verb, Translation, ConjSingular, ConjPlural, Notes
- `conjugation/subjonctif.csv` — Verb, Translation, ConjSingular, ConjPlural, Notes
- `conjugation/participes.csv` — Verb, Translation, Notes
- `conjugation/futur_stems.csv` — Verb, Translation, Example, Notes
- `conjugation/etre_verbs.csv` — Verb, Translation, Notes

**Merge strategy (skeleton + content → final):**
- Key: `French` for vocabulary/quebecismes, `Verb` for conjugation
- Rename Notes fields: skeleton `Notes` → `GrammarNotes`, content `Notes` → `LearningNotes`

**Verb group classification:**
- 1st group: -er verbs (regular, except "aller")
- 2nd group: -ir with -issant participle (finir → finissant)
- 3rd group: all others (irregular) — -ir sans -issant, -re, -oir, aller

**Pattern-based learning rationale:**
- Imparfait, Futur simple, Conditionnel — derivable from Présent + rules
- Only irregular forms need explicit memorization
- ~500 cards cover what ~16700 would have (95% reduction)

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

## Audio Files

**Storage (in `content/audio/`, tracked in git):**
```
content/audio/
├── words/          # word pronunciation: un_homme.mp3
└── examples/       # example sentences: un_homme_ex.mp3
```

**Filename convention:**
- Slug from French field: `un homme` → `un_homme.mp3`
- Example suffix: `un_homme_ex.mp3`

**Anki field format:**
```
Audio: [sound:un_homme.mp3]
AudioExample: [sound:un_homme_ex.mp3]
```

**Azure TTS settings (from config.py):**
- Voices: fr-CA-SylvieNeural, fr-CA-JeanNeural, fr-CA-AntoineNeural, fr-CA-ThierryNeural
- Format: audio-16khz-128kbitrate-mono-mp3

## TODO

### Completed
- [x] `05_generate_cards.py` — Generate card skeletons (10695 vocab + 566 qc)
- [x] `05b_generate_conjugation.py` — Restructured conjugation (502 cards vs 16700)
- [x] Expressions — 469 entries complete in `content/expressions/all.csv`
- [x] Québécismes — 566 entries complete in `content/quebecismes/all.csv`
- [x] `09_generate_audio.py` — TTS script created
- [x] Vocabulary batches — 122 batches (~10591 words)
- [x] Conjugation — all 5 types (present, subjonctif, participes, futur_stems, être verbs)
- [x] `.env` support in `09_generate_audio.py`

### Pending tasks
- [ ] Azure TTS: get subscription key, generate audio
- [ ] Final .apkg assembly with audio
