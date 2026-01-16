# Инструкция: Генерация CSV для French Conjugation Deck

## Формат CSV

```csv
Verb,Translation,Tense,ConjSingular,ConjPlural,Notes
```

### Поля

| Поле | Описание | Пример |
|------|----------|--------|
| **Verb** | Инфинитив | `aller`, `se souvenir` |
| **Translation** | Перевод | `идти, ехать` |
| **Tense** | Время | `Présent`, `Passé composé` |
| **ConjSingular** | je, tu, il/elle с `{{c1::...}}` | см. ниже |
| **ConjPlural** | nous, vous, ils/elles с `{{c2::...}}` | см. ниже |
| **Notes** | Группа, особенности, выражения | `Неправильный. Futur proche: je vais + inf.` |

---

## Структура Cloze-полей

### ConjSingular (c1)
```html
<span class="pronoun">je</span> {{c1::parle}}<br><span class="pronoun">tu</span> {{c1::parles}}<br><span class="pronoun">il/elle</span> {{c1::parle}}
```

### ConjPlural (c2)
```html
<span class="pronoun">nous</span> {{c2::parlons}}<br><span class="pronoun">vous</span> {{c2::parlez}}<br><span class="pronoun">ils/elles</span> {{c2::parlent}}
```

### Особые случаи

**Элизия (j' вместо je):**
```html
<span class="pronoun">j'</span>{{c1::ai}}<br>...
```

**Возвратные глаголы:**
```html
<span class="pronoun">je</span> {{c1::me souviens}}<br><span class="pronoun">tu</span> {{c1::te souviens}}<br><span class="pronoun">il/elle</span> {{c1::se souvient}}
```

---

## Времена для изучения (по уровням)

### A1-A2
| Время | Пример | Использование |
|-------|--------|---------------|
| **Présent** | je parle | Настоящее, привычки |
| **Passé composé** | j'ai parlé | Завершённое прошлое |
| **Futur proche** | je vais parler | Ближайшее будущее |
| **Impératif** | Parle! Parlons! | Приказы, советы |

### B1
| Время | Пример | Использование |
|-------|--------|---------------|
| **Imparfait** | je parlais | Описание в прошлом |
| **Futur simple** | je parlerai | Будущее |
| **Conditionnel présent** | je parlerais | Вежливость, гипотезы |

### B2
| Время | Пример | Использование |
|-------|--------|---------------|
| **Subjonctif présent** | que je parle | После que + эмоции/сомнение |
| **Plus-que-parfait** | j'avais parlé | Предпрошедшее |
| **Conditionnel passé** | j'aurais parlé | Сожаление о прошлом |

---

## Примеры по временам

### Présent (правильный -er)
```csv
parler,говорить,Présent,"<span class=""pronoun"">je</span> {{c1::parle}}<br><span class=""pronoun"">tu</span> {{c1::parles}}<br><span class=""pronoun"">il/elle</span> {{c1::parle}}","<span class=""pronoun"">nous</span> {{c2::parlons}}<br><span class=""pronoun"">vous</span> {{c2::parlez}}<br><span class=""pronoun"">ils/elles</span> {{c2::parlent}}","Groupe 1 (-er). Образец для всех глаголов на -er."
```

### Présent (правильный -ir с -iss-)
```csv
finir,заканчивать,Présent,"<span class=""pronoun"">je</span> {{c1::finis}}<br><span class=""pronoun"">tu</span> {{c1::finis}}<br><span class=""pronoun"">il/elle</span> {{c1::finit}}","<span class=""pronoun"">nous</span> {{c2::finissons}}<br><span class=""pronoun"">vous</span> {{c2::finissez}}<br><span class=""pronoun"">ils/elles</span> {{c2::finissent}}","Groupe 2 (-ir с -iss-). Образец: choisir, réussir, réfléchir."
```

### Présent (неправильный)
```csv
aller,"идти, ехать",Présent,"<span class=""pronoun"">je</span> {{c1::vais}}<br><span class=""pronoun"">tu</span> {{c1::vas}}<br><span class=""pronoun"">il/elle</span> {{c1::va}}","<span class=""pronoun"">nous</span> {{c2::allons}}<br><span class=""pronoun"">vous</span> {{c2::allez}}<br><span class=""pronoun"">ils/elles</span> {{c2::vont}}","Неправильный! Futur proche: je vais + infinitif."
```

### Passé composé (с avoir)
```csv
parler,говорить,Passé composé,"<span class=""pronoun"">j'</span>{{c1::ai parlé}}<br><span class=""pronoun"">tu</span> {{c1::as parlé}}<br><span class=""pronoun"">il/elle</span> {{c1::a parlé}}","<span class=""pronoun"">nous</span> {{c2::avons parlé}}<br><span class=""pronoun"">vous</span> {{c2::avez parlé}}<br><span class=""pronoun"">ils/elles</span> {{c2::ont parlé}}","Вспомогательный: avoir. Participe passé: parlé."
```

### Passé composé (с être)
```csv
aller,"идти, ехать",Passé composé,"<span class=""pronoun"">je</span> {{c1::suis allé(e)}}<br><span class=""pronoun"">tu</span> {{c1::es allé(e)}}<br><span class=""pronoun"">il/elle</span> {{c1::est allé(e)}}","<span class=""pronoun"">nous</span> {{c2::sommes allé(e)s}}<br><span class=""pronoun"">vous</span> {{c2::êtes allé(e)(s)}}<br><span class=""pronoun"">ils/elles</span> {{c2::sont allé(e)s}}","Вспомогательный: être! Согласование с подлежащим."
```

### Imparfait
```csv
parler,говорить,Imparfait,"<span class=""pronoun"">je</span> {{c1::parlais}}<br><span class=""pronoun"">tu</span> {{c1::parlais}}<br><span class=""pronoun"">il/elle</span> {{c1::parlait}}","<span class=""pronoun"">nous</span> {{c2::parlions}}<br><span class=""pronoun"">vous</span> {{c2::parliez}}<br><span class=""pronoun"">ils/elles</span> {{c2::parlaient}}","Основа от nous (présent) + окончания: -ais, -ais, -ait, -ions, -iez, -aient."
```

### Futur simple
```csv
parler,говорить,Futur simple,"<span class=""pronoun"">je</span> {{c1::parlerai}}<br><span class=""pronoun"">tu</span> {{c1::parleras}}<br><span class=""pronoun"">il/elle</span> {{c1::parlera}}","<span class=""pronoun"">nous</span> {{c2::parlerons}}<br><span class=""pronoun"">vous</span> {{c2::parlerez}}<br><span class=""pronoun"">ils/elles</span> {{c2::parleront}}","Инфинитив + окончания avoir: -ai, -as, -a, -ons, -ez, -ont."
```

### Conditionnel présent
```csv
vouloir,хотеть,Conditionnel présent,"<span class=""pronoun"">je</span> {{c1::voudrais}}<br><span class=""pronoun"">tu</span> {{c1::voudrais}}<br><span class=""pronoun"">il/elle</span> {{c1::voudrait}}","<span class=""pronoun"">nous</span> {{c2::voudrions}}<br><span class=""pronoun"">vous</span> {{c2::voudriez}}<br><span class=""pronoun"">ils/elles</span> {{c2::voudraient}}","Вежливая просьба: Je voudrais un café. Основа futur + окончания imparfait."
```

### Subjonctif présent
```csv
faire,делать,Subjonctif présent,"<span class=""pronoun"">que je</span> {{c1::fasse}}<br><span class=""pronoun"">que tu</span> {{c1::fasses}}<br><span class=""pronoun"">qu'il/elle</span> {{c1::fasse}}","<span class=""pronoun"">que nous</span> {{c2::fassions}}<br><span class=""pronoun"">que vous</span> {{c2::fassiez}}<br><span class=""pronoun"">qu'ils/elles</span> {{c2::fassent}}","После: il faut que, je veux que, bien que, pour que."
```

---

## Приоритетные глаголы

### Неправильные (учить первыми)
```
être, avoir, aller, faire, pouvoir, vouloir, devoir, savoir, 
venir, prendre, mettre, dire, voir, partir, sortir, connaître
```

### Groupe 1 (-er) — образцы
```
parler, travailler, habiter, aimer, chercher, arriver, 
demander, penser, trouver, donner, passer, rester
```

### Groupe 2 (-ir с -iss-)
```
finir, choisir, réussir, réfléchir, remplir, établir
```

### Возвратные
```
se lever, se coucher, s'appeler, se souvenir, se débrouiller
```

---

## Notes — что включать

- **Группа глагола**: `Groupe 1 (-er)`, `Groupe 2 (-ir)`, `Groupe 3 (неправильный)`
- **Вспомогательный**: `Passé composé с être!`
- **Согласование**: `Participe passé согласуется с подлежащим`
- **Особенности основы**: `Основа меняется: je veux, nous voulons`
- **Полезные выражения**: `Faire attention, faire la cuisine`
- **Похожие глаголы**: `Спрягается как venir: devenir, revenir, se souvenir`
- **Québec**: `В Québec чаще: je vas (разг.) вместо je vais`

---

## Формат CSV — технические детали

### Экранирование
- Кавычки внутри поля: `""` вместо `"`
- Переносы строк: `<br>` вместо реальных переносов
- Запятые в тексте: оборачивай поле в кавычки

### Пример полной строки
```csv
aller,"идти, ехать",Présent,"<span class=""pronoun"">je</span> {{c1::vais}}<br><span class=""pronoun"">tu</span> {{c1::vas}}<br><span class=""pronoun"">il/elle</span> {{c1::va}}","<span class=""pronoun"">nous</span> {{c2::allons}}<br><span class=""pronoun"">vous</span> {{c2::allez}}<br><span class=""pronoun"">ils/elles</span> {{c2::vont}}","Неправильный глагол! Futur proche: je vais + infinitif."
```

---

## Чеклист перед выдачей

- [ ] Инфинитив корректный (с se для возвратных)?
- [ ] Время указано правильно?
- [ ] ConjSingular содержит je, tu, il/elle с `{{c1::...}}`?
- [ ] ConjPlural содержит nous, vous, ils/elles с `{{c2::...}}`?
- [ ] Элизия учтена (j' вместо je перед гласной)?
- [ ] `<br>` между формами (не реальные переносы)?
- [ ] Кавычки экранированы (`""`)?
- [ ] Notes содержат группу и особенности?

---

## Порядок изучения времён для TEF/TCF

1. **Présent** — база всего
2. **Passé composé** — рассказ о прошлом
3. **Futur proche** (aller + inf) — планы
4. **Imparfait** — описания, привычки в прошлом
5. **Futur simple** — формальное будущее
6. **Conditionnel présent** — вежливость (je voudrais)
7. **Subjonctif présent** — после que + эмоции
8. **Plus-que-parfait** — для сложных нарративов

---

*«La conjugaison, c'est la gymnastique de la langue.»*
Спряжение — это гимнастика языка.

🇨🇦 CLB 7 требует уверенного владения временами до Conditionnel включительно!
