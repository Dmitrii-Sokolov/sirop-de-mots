# French Learning Deck v3 — Инструкция

## Быстрый старт

1. **Удали старые Note Types** (если импортировал v1 или v2):
   - Tools → Manage Note Types → удали "French Vocabulary v2 (FR-RU)" и "French Vocabulary (FR-RU)"
   
2. **Импортируй** `French_Learning_Deck_v3.apkg` (File → Import)

3. Появятся две колоды:
   - `French::Vocabulary::Core` — слова
   - `French::Grammar::Conjugation` — спряжения

---

## Часть 1: Vocabulary (Словарь)

### Структура карточки

| Поле | Что писать | Пример |
|------|------------|--------|
| **French** | Слово **С АРТИКЛЕМ** | `une maison` |
| **Russian** | Перевод | `дом` |
| **WordType** | Тип слова | `f` |
| **ExampleFrench** | Предложение, слово в `<b>` | `Nous avons acheté <b>une maison</b>.` |
| **ExampleRussian** | Перевод, слово в `<b>` | `Мы купили <b>дом</b>.` |
| **Notes** | Заметки | `Не путать с bâtiment (здание)` |
| **Emoji** | Эмодзи для визуализации | `🏠` |
| **Audio** | Аудио слова (Forvo) | *заполняется через AwesomeTTS* |
| **AudioExample** | Аудио примера (Azure) | *заполняется через AwesomeTTS* |

### Правила заполнения French

**Существительные — ВСЕГДА с артиклем:**
```
✅ une maison
✅ le travail  
✅ un appartement
✅ l'immigration (f)    ← если артикль l', укажи род в скобках

❌ maison
❌ travail
```

**Глаголы — инфинитив:**
```
✅ améliorer
✅ se débrouiller       ← возвратные с se
```

**Остальное — как есть:**
```
✅ cependant           (conj)
✅ rapidement          (adv)
✅ par conséquent      (conj)
```

### Значения поля WordType

| Код | Тип | Цвет | Примеры |
|-----|-----|------|---------|
| `m` | мужской род | 🔵 синий | le travail, un homme |
| `f` | женский род | 🩷 розовый | la maison, une femme |
| `v` | глагол | 🟢 зелёный | parler, aller, se souvenir |
| `adj` | прилагательное | 🟣 фиолетовый | grand, important, québécois |
| `adv` | наречие | 🩵 бирюзовый | rapidement, très, bien |
| `conj` | союз/коннектор | 🟠 оранжевый | cependant, mais, parce que |
| `prep` | предлог | 🟤 коричневый | dans, pour, avec, à |
| `pron` | местоимение | 🩶 серо-синий | celui, lequel, y, en |
| `num` | числительное | 💜 пурпурный | premier, vingt, centaine |
| `interj` | междометие | 🔴 красно-оранж. | hélas, voyons, tiens |
| `expr` | выражение/идиома | 🌲 тёмно-бирюзовый | avoir beau, il s'agit de |
| `loc` | устойчивое сочетание | 💙 индиго | à peu près, en effet |

### Выделение ключевого слова

**ОБЯЗАТЕЛЬНО** оборачивай ключевое слово в `<b>...</b>`:

```html
ExampleFrench:
Nous avons acheté <b>une maison</b> dans la banlieue de Montréal.

ExampleRussian:
Мы купили <b>дом</b> в пригороде Монреаля.
```

Это слово подсветится оранжевым на карточке.

### Расположение элементов на карточке

**Recognition (FR → RU):**
```
┌─────────────────────────────────────┐
│  FRONT (вопрос)                     │
│  ┌─────────────────────────────┐    │
│  │ une maison 🔊 [f]           │    │  ← French + Audio + WordType
│  └─────────────────────────────┘    │
│  Nous avons acheté... 🔊            │  ← ExampleFrench + AudioExample
├─────────────────────────────────────┤
│  BACK (ответ)                       │
│  🏠 дом                             │  ← Emoji + Russian (награда!)
│  Мы купили дом...                   │  ← ExampleRussian
│  💡 Женский род!                    │  ← Notes
└─────────────────────────────────────┘
```

**Production (RU → FR):**
```
┌─────────────────────────────────────┐
│  FRONT (вопрос)                     │
│  дом                                │  ← Russian (БЕЗ emoji — честный тест!)
│  Мы купили дом...                   │  ← ExampleRussian
├─────────────────────────────────────┤
│  BACK (ответ)                       │
│  дом                                │  ← Russian (напоминание)
│  ─────────────────────────────────  │
│  ┌─────────────────────────────┐    │
│  │ 🏠 une maison 🔊 [f]        │    │  ← Emoji + French (награда!)
│  └─────────────────────────────┘    │
│  Nous avons acheté... 🔊            │  ← ExampleFrench + AudioExample
│  💡 Женский род!                    │  ← Notes
└─────────────────────────────────────┘
```

**Принцип:** Emoji всегда на Back, рядом с ответом — как награда и мнемоника после правильного воспоминания.

### CSV для импорта словаря

Формат файла (разделитель — запятая):

```csv
French,Russian,WordType,ExampleFrench,ExampleRussian,Notes,Emoji
une maison,дом,f,"Nous avons acheté <b>une maison</b>.","Мы купили <b>дом</b>.","Женский род!",🏠
un travail,работа,m,"Je cherche <b>un travail</b>.","Я ищу <b>работу</b>.",,💼
améliorer,улучшать,v,"Il faut <b>améliorer</b> mon français.","Нужно <b>улучшить</b> мой французский.",,📈
```

Поля Audio, AudioExample заполняются отдельно через AwesomeTTS после импорта.

**При импорте:**
- Note Type: `French Vocabulary v3 (FR-RU)`
- Deck: `French::Vocabulary::Core`
- ✅ First line contains field names

---

## Часть 2: Conjugation (Спряжения)

### Структура карточки

| Поле | Что писать | Пример |
|------|------------|--------|
| **Verb** | Инфинитив | `aller` |
| **Translation** | Перевод | `идти, ехать` |
| **Tense** | Время | `Présent` |
| **ConjSingular** | je, tu, il/elle с `{{c1::...}}` | см. ниже |
| **ConjPlural** | nous, vous, ils/elles с `{{c2::...}}` | см. ниже |
| **Notes** | Заметки | `Неправильный глагол` |

### Как это работает

Каждый глагол создаёт **2 карточки**:
- **Карточка c1**: показывает только Singulier (je, tu, il/elle)
- **Карточка c2**: показывает только Pluriel (nous, vous, ils/elles)

```
┌─────────────────────────────────────┐
│           aller                     │
│       идти, ехать                   │
│          Présent                    │
│  ┌─────────────────────────────┐    │
│  │        Singulier            │    │
│  │  je     [____]              │    │
│  │  tu     [____]              │    │
│  │  il/elle [____]             │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### Формат полей

**ConjSingular:**
```html
<span class="pronoun">je</span> {{c1::vais}}<br>
<span class="pronoun">tu</span> {{c1::vas}}<br>
<span class="pronoun">il/elle</span> {{c1::va}}
```

**ConjPlural:**
```html
<span class="pronoun">nous</span> {{c2::allons}}<br>
<span class="pronoun">vous</span> {{c2::allez}}<br>
<span class="pronoun">ils/elles</span> {{c2::vont}}
```

### CSV для импорта спряжений

```csv
Verb,Translation,Tense,ConjSingular,ConjPlural,Notes
aller,"идти, ехать",Présent,"<span class=""pronoun"">je</span> {{c1::vais}}<br><span class=""pronoun"">tu</span> {{c1::vas}}<br><span class=""pronoun"">il/elle</span> {{c1::va}}","<span class=""pronoun"">nous</span> {{c2::allons}}<br><span class=""pronoun"">vous</span> {{c2::allez}}<br><span class=""pronoun"">ils/elles</span> {{c2::vont}}","Неправильный глагол"
```

⚠️ **Внимание:** 
- В CSV кавычки внутри поля удваиваются (`""` вместо `"`)
- Используй `<br>` для переноса строк вместо реальных переносов

**При импорте:**
- Note Type: `French Conjugation v3 (Cloze)`
- Deck: `French::Grammar::Conjugation`
- ✅ Allow HTML in fields

---

## Настройки отображения

### Смешать Recognition и Production

Чтобы обе карточки появлялись вперемешку (а не сначала все Recognition):

**Deck Options → Display Order:**
- New card gather order: `Deck`
- New card sort order: `Random`

**ИЛИ:**
- Bury related new cards: `OFF`

### Порядок новых слов

По умолчанию — в порядке добавления. Для частотного порядка:
1. Отсортируй CSV по частотности перед импортом
2. Или: New card gather order → `Random`

### FSRS (рекомендуется)

Deck Options → FSRS:
- Enable FSRS: ✅
- Desired retention: `0.90`
- Maximum interval: `180` (для подготовки к TEF)

### Настройка аудио (AwesomeTTS)

1. **Установи аддон AwesomeTTS** (код: `1436550454`)

2. **Для поля Audio (слова)** — Forvo:
   - Tools → AwesomeTTS → Add Audio to Notes
   - Source field: `French`
   - Destination field: `Audio`
   - Service: `Forvo` (реальные носители)
   - Language: `French`

3. **Для поля AudioExample (предложения)** — Azure:
   - Source field: `ExampleFrench`
   - Destination field: `AudioExample`
   - Service: `Microsoft Azure`
   - Voice: `fr-CA-...` (канадский французский!)
   - Требуется бесплатный API ключ Azure

**Рекомендуемая комбинация:**
- Слова → Forvo (живые голоса, разные акценты)
- Предложения → Azure fr-CA (стабильное качество, канадский акцент)

---

## Система тегов

```
level::a1, level::a2, level::b1, level::b2
topic::travail, topic::logement, topic::immigration
source::frequency-1000, source::innerfrench, source::personal
type::irregular, type::regular-er, type::regular-ir
```

### Фильтрованные колоды

Учить только A2 слова:
```
deck:"French::Vocabulary::Core" tag:level::a2
```

Только неправильные глаголы:
```
deck:"French::Grammar::Conjugation" tag:type::irregular
```

---

## Примеры заполнения

### Существительное (женский род)

| Поле | Значение |
|------|----------|
| French | `une voiture` |
| Russian | `машина, автомобиль` |
| WordType | `f` |
| ExampleFrench | `J'ai acheté <b>une voiture</b> d'occasion.` |
| ExampleRussian | `Я купил <b>машину</b> с пробегом.` |
| Notes | `D'occasion = подержанный. Une voiture neuve = новая.` |

### Глагол

| Поле | Значение |
|------|----------|
| French | `se souvenir` |
| Russian | `помнить, вспоминать` |
| WordType | `v` |
| ExampleFrench | `Je <b>me souviens</b> de mon premier jour au Canada.` |
| ExampleRussian | `Я <b>помню</b> свой первый день в Канаде.` |
| Notes | `Se souvenir DE + noun. Groupe 3 (как venir).` |

### Коннектор (союз)

| Поле | Значение |
|------|----------|
| French | `par conséquent` |
| Russian | `следовательно, поэтому` |
| WordType | `conj` |
| ExampleFrench | `Mon score IELTS est bon ; <b>par conséquent</b>, je peux me concentrer sur le français.` |
| ExampleRussian | `Мой балл IELTS хороший; <b>следовательно</b>, я могу сосредоточиться на французском.` |
| Notes | `Синонимы: donc, ainsi, c'est pourquoi. Важно для TEF!` |

### Прилагательное

| Поле | Значение |
|------|----------|
| French | `québécois` |
| Russian | `квебекский` |
| WordType | `adj` |
| ExampleFrench | `L'accent <b>québécois</b> est différent de l'accent français.` |
| ExampleRussian | `<b>Квебекский</b> акцент отличается от французского.` |
| Notes | `Женский: québécoise. Также существительное: un Québécois.` |

### Наречие

| Поле | Значение |
|------|----------|
| French | `actuellement` |
| Russian | `в настоящее время, сейчас` |
| WordType | `adv` |
| ExampleFrench | `J'habite <b>actuellement</b> en Serbie.` |
| ExampleRussian | `<b>Сейчас</b> я живу в Сербии.` |
| Notes | `⚠️ Faux ami! НЕ "актуально". Actually = en fait.` |

### Предлог

| Поле | Значение |
|------|----------|
| French | `grâce à` |
| Russian | `благодаря` |
| WordType | `prep` |
| ExampleFrench | `<b>Grâce à</b> mon travail, je peux immigrer.` |
| ExampleRussian | `<b>Благодаря</b> работе я могу иммигрировать.` |
| Notes | `Позитивная причина. Негативная: à cause de.` |

### Устойчивое выражение (locution)

| Поле | Значение |
|------|----------|
| French | `en effet` |
| Russian | `действительно, в самом деле` |
| WordType | `loc` |
| ExampleFrench | `Le Québec est attractif ; <b>en effet</b>, il offre beaucoup d'opportunités.` |
| ExampleRussian | `Квебек привлекателен; <b>действительно</b>, он предлагает много возможностей.` |
| Notes | `Для подтверждения. Синоним: effectivement.` |

### Идиома (expression)

| Поле | Значение |
|------|----------|
| French | `avoir beau` |
| Russian | `сколько ни..., как ни старайся` |
| WordType | `expr` |
| ExampleFrench | `J'<b>ai beau</b> étudier, je ne comprends pas cette règle.` |
| ExampleRussian | `<b>Сколько ни</b> учу, не понимаю это правило.` |
| Notes | `Avoir beau + infinitif. Очень французская конструкция!` |

### Числительное

| Поле | Значение |
|------|----------|
| French | `premier / première` |
| Russian | `первый / первая` |
| WordType | `num` |
| ExampleFrench | `C'est la <b>première</b> fois que je visite le Canada.` |
| ExampleRussian | `Это <b>первый</b> раз, когда я посещаю Канаду.` |
| Notes | `Порядковое. Мужской: premier, женский: première.` |

### Числительное (приблизительное)

| Поле | Значение |
|------|----------|
| French | `une dizaine` |
| Russian | `около десяти, десяток` |
| WordType | `num` |
| ExampleFrench | `Il y a <b>une dizaine</b> de personnes dans la salle.` |
| ExampleRussian | `В зале <b>около десяти</b> человек.` |
| Notes | `Также: une vingtaine (≈20), une centaine (≈100), un millier (≈1000).` |

### Междометие

| Поле | Значение |
|------|----------|
| French | `hélas` |
| Russian | `увы, к сожалению` |
| WordType | `interj` |
| ExampleFrench | `<b>Hélas</b>, je n'ai pas réussi l'examen.` |
| ExampleRussian | `<b>Увы</b>, я не сдал экзамен.` |
| Notes | `Книжное/формальное. Разговорное: malheureusement.` |

### Междометие (разговорное)

| Поле | Значение |
|------|----------|
| French | `tiens / tenez` |
| Russian | `вот, на; смотри-ка` |
| WordType | `interj` |
| ExampleFrench | `<b>Tiens</b>, c'est pour toi !` |
| ExampleRussian | `<b>На</b>, это тебе!` |
| Notes | `Tiens = ты, tenez = вы. Также удивление: Tiens, tu es là ?` |

---

## Troubleshooting

**Cloze не работает:**
- Убедись, что Note Type = `French Conjugation v3 (Cloze)` (не обычный)
- Проверь синтаксис: `{{c1::текст}}` — без пробелов внутри скобок

**Цвета не отображаются:**
- Импортируй .apkg заново (не CSV)
- Проверь CSS в Tools → Manage Note Types → Cards → Styling

**HTML-теги видны как текст:**
- При импорте CSV включи ✅ Allow HTML in fields

---

*«Chaque expert était autrefois un débutant.»*
Каждый эксперт когда-то был новичком.

🇨🇦 CLB 7 = +25 CRS points. Ça vaut le coup!
