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

## Быстрый старт

**Репозиторий содержит всё необходимое:** контент, переводы и 23000+ аудиофайлов.

```bash
git clone https://github.com/your-username/sirop-de-mots.git
cd sirop-de-mots
pip install pandas genanki
python scripts/11_build_deck.py
```

Результат: `French_TEF_TCF.apkg` (750 MB, 12000+ карточек с аудио)

Импортируйте в [Anki](https://apps.ankiweb.net/) и начинайте учить!

## Сборка колоды (подробно)

### Требования

- Python 3.9+
- Git (для клонирования с аудиофайлами)

### Шаги

1. **Клонирование репозитория**
   ```bash
   git clone https://github.com/your-username/sirop-de-mots.git
   cd sirop-de-mots
   ```

2. **Установка зависимостей**
   ```bash
   pip install pandas genanki
   ```

3. **Сборка колоды**
   ```bash
   python scripts/11_build_deck.py
   ```

Готово! Файл `French_TEF_TCF.apkg` появится в корне проекта.

### Сборка без аудио (лёгкая версия)

Если не нужно аудио или хотите быстро проверить:

```bash
python scripts/11_build_deck.py --no-audio
```

Результат: ~5 MB вместо 750 MB.

## Перегенерация аудио (для разработчиков)

Аудиофайлы уже включены в репозиторий. Этот раздел нужен только если вы хотите изменить голоса или добавить новые слова.

### Настройка Azure Speech

```bash
pip install azure-cognitiveservices-speech python-dotenv
```

Создайте файл `.env`:
```
AZURE_SPEECH_KEY=ваш_ключ
AZURE_SPEECH_REGION=canadacentral
```

Получить ключ: [Azure Portal](https://portal.azure.com) → Cognitive Services → Speech

### Генерация

```bash
# Все файлы (~23000 mp3, ~3 часа)
python scripts/09_generate_audio.py

# Конкретный уровень
python scripts/09_generate_audio.py --input content/vocabulary/b1.csv
```

Скрипт пропускает существующие файлы. Для перезаписи: `--no-skip`.

## Структура колоды

```
French TEF-TCF/
├── Vocabulaire/
│   ├── A1-A2 (769)     ← базовая лексика
│   ├── B1 (1821)       ← средний уровень
│   ├── B2 (1829)       ← продвинутый
│   ├── C1+ (5120)      ← углублённый
│   └── Autres (990)    ← наречия, местоимения, предлоги
├── Expressions (469)   ← идиомы и устойчивые выражения
├── Québécismes (566)   ← канадский французский
└── Conjugaison/        ← спряжение неправильных глаголов
    ├── Présent (360)
    ├── Subjonctif (10)
    ├── Participes (110)
    ├── Futur (22)
    └── Verbes être (17)
```

## Скрипты

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

## Quick Start

**The repository includes everything:** content, translations, and 23,000+ audio files.

```bash
git clone https://github.com/your-username/sirop-de-mots.git
cd sirop-de-mots
pip install pandas genanki
python scripts/11_build_deck.py
```

Result: `French_TEF_TCF.apkg` (750 MB, 12,000+ cards with audio)

Import into [Anki](https://apps.ankiweb.net/) and start learning!

## Build Options

### Without audio (lightweight)

```bash
python scripts/11_build_deck.py --no-audio
```

Result: ~5 MB instead of 750 MB.

### Regenerate audio (developers only)

Audio files are already in the repo. Only needed if changing voices or adding words.

```bash
pip install azure-cognitiveservices-speech python-dotenv
# Create .env with AZURE_SPEECH_KEY and AZURE_SPEECH_REGION
python scripts/09_generate_audio.py
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
