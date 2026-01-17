# Sirop de Mots

Инструменты для изучения канадского французского языка, предназначенные для русскоязычных.

## Описание

Проект содержит Python-скрипты для извлечения, анализа и форматирования французской лексики из базы данных Lexique383 для создания Anki-колод. Ориентирован на подготовку к языковым тестам TEF/TCF.

## Возможности

- Анализ частотности слов (по фильмам и книгам)
- Извлечение топ-N слов по частотности
- Разбивка по грамматическим категориям (существительные, глаголы, прилагательные, наречия)
- Анализ рода существительных
- Готовые Anki-колоды с двусторонними карточками (FR-RU)

## Структура проекта

```
├── Lexique383.tsv              # База данных Lexique383 (~140k слов)
├── French_Learning_Deck_v3.apkg # Готовая Anki-колода
├── count_lemma_types.py        # Статистика лемм по категориям
├── create_french_deck_v3.py    # Генерация Anki-колоды
├── extract_lexique_selection.py # Извлечение выборки лемм
├── categories/                 # Леммы по категориям (NOM, VER, ADJ...)
└── lemma_type_stats.csv        # Статистика по категориям
```

## Использование

```bash
# Статистика лемм по грамматическим категориям
python count_lemma_types.py

# Извлечение выборки лемм (топ-10k VER/NOM/ADJ/ADV + редкие категории)
python extract_lexique_selection.py

# Генерация Anki-колоды с демо-карточками
python create_french_deck_v3.py
```

## Источник данных

Данные взяты с сайта [Lexique.org](http://www.lexique.org) — база данных Lexique383, содержащая около 140 000 французских слов с информацией о частотности, грамматических категориях, роде и других характеристиках.

**Скачать базу данных:** http://www.lexique.org/databases/Lexique383/Lexique383.tsv

## Формула частотности

Для подготовки к TEF/TCF используется комбинированная частотность с приоритетом устной речи:

```python
freq_combined = 0.6 * freqlemfilms2 + 0.4 * freqlemlivres
```

## Anki-колоды

Подробная инструкция по использованию Anki-колод находится в файле [French_Learning_Deck_v3_README.md](French_Learning_Deck_v3_README.md).

## Лицензия

[CC BY-SA 4.0](LICENSE-CC-BY-SA4.0.txt) (Creative Commons Attribution-ShareAlike 4.0 International)

Проект включает данные из базы Lexique383, которая распространяется под той же лицензией CC BY-SA 4.0.

## Отказ от ответственности

Код и данные предоставляются «как есть» (as is). Автор не несёт ответственности за их использование, точность данных или любые последствия, связанные с применением материалов из этого репозитория.

---

# Sirop de Mots (English)

Tools for learning Canadian French.

> **Note:** The author is not a native English speaker. However, these tools can be used by anyone learning Canadian French, regardless of their native language. The Anki flashcard deck included in this repository uses French-Russian translations, but the Python scripts and Lexique383 data can be adapted for any language pair.

## Description

This project contains Python scripts for extracting, analyzing, and formatting French vocabulary from the Lexique383 database to create Anki flashcard decks. It is designed for TEF/TCF language test preparation.

## Features

- Word frequency analysis (based on films and books)
- Extraction of top-N words by frequency
- Breakdown by grammatical categories (nouns, verbs, adjectives, adverbs)
- Noun gender analysis
- Ready-to-use Anki decks with bidirectional cards

## Project Structure

```
├── Lexique383.tsv              # Lexique383 database (~140k words)
├── French_Learning_Deck_v3.apkg # Ready-to-use Anki deck
├── count_lemma_types.py        # Lemma statistics by category
├── create_french_deck_v3.py    # Anki deck generator
├── extract_lexique_selection.py # Extract lemma selection
├── categories/                 # Lemmas by category (NOM, VER, ADJ...)
└── lemma_type_stats.csv        # Category statistics
```

## Usage

```bash
# Count lemmas by grammatical category
python count_lemma_types.py

# Extract lemma selection (top 10k VER/NOM/ADJ/ADV + rare categories)
python extract_lexique_selection.py

# Generate Anki deck with demo cards
python create_french_deck_v3.py
```

## Data Source

Data is sourced from [Lexique.org](http://www.lexique.org) — the Lexique383 database containing approximately 140,000 French words with information about frequency, grammatical categories, gender, and other characteristics.

**Download the database:** http://www.lexique.org/databases/Lexique383/Lexique383.tsv

## Frequency Formula

For TEF/TCF preparation, a combined frequency is used with priority given to spoken language:

```python
freq_combined = 0.6 * freqlemfilms2 + 0.4 * freqlemlivres
```

## Anki Decks

Detailed instructions for using the Anki decks can be found in [French_Learning_Deck_v3_README.md](French_Learning_Deck_v3_README.md) (in Russian).

## License

[CC BY-SA 4.0](LICENSE-CC-BY-SA4.0.txt) (Creative Commons Attribution-ShareAlike 4.0 International)

This project includes data from the Lexique383 database, which is distributed under the same CC BY-SA 4.0 license.

## Disclaimer

The code and data are provided "as is". The author assumes no responsibility for their use, data accuracy, or any consequences arising from the use of materials in this repository.
