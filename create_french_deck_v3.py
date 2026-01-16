#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
French Vocabulary Anki Deck Generator v3
"""

import genanki

# Unique IDs
VOCAB_MODEL_ID = 1607392330
CLOZE_MODEL_ID = 1607392331
VOCAB_DECK_ID = 2059400110
CONJ_DECK_ID = 2059400111

# CSS STYLING
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

/* Main word with article - top of card */
.main-word {
    font-size: 38px;
    font-weight: bold;
    margin-bottom: 20px;
    padding: 15px;
    border-radius: 10px;
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
    color: #333;
}

/* Night mode for main-word without gender class */
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
.main-word.gender-loc { color: #4527a0; background: linear-gradient(135deg, #ede7f6 0%, #d1c4e9 100%); }
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
.gender-tag.gender-loc { background-color: #4527a0; color: white; }
.gender-tag.gender-other { background-color: #616161; color: white; }

/* Example sentence */
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

/* KEY WORD HIGHLIGHTING in sentences */
.example b, .example strong {
    color: #d84315;
    font-weight: bold;
    background-color: #fff3e0;
    padding: 2px 4px;
    border-radius: 4px;
}

/* Translation */
.translation {
    font-size: 28px;
    color: #333;
    margin: 20px 0;
    padding: 10px;
}
.night_mode .translation { color: #f5f5f5; }
.emoji { font-size: 32px; margin-right: 10px; vertical-align: middle; }
.audio-btn { display: inline-block; margin-left: 8px; vertical-align: middle; }
.example-translation {
    font-size: 16px;
    color: #666;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px dashed #ddd;
    font-style: italic;
}
.notes {
    font-size: 15px;
    color: #555;
    margin-top: 20px;
    padding: 12px;
    background-color: #fff8e1;
    border-radius: 8px;
    text-align: left;
    border-left: 4px solid #ffc107;
}
hr { border: none; border-top: 2px solid #e0e0e0; margin: 25px 0; }
.direction {
    font-size: 12px;
    color: #999;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
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
.tense {
    font-size: 16px;
    color: #1b5e20;
    background-color: #c8e6c9;
    padding: 5px 15px;
    border-radius: 15px;
    display: inline-block;
    margin-bottom: 20px;
    font-weight: 500;
}
.conjugation {
    font-size: 24px;
    line-height: 2;
    text-align: left;
    padding: 20px 30px;
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    display: inline-block;
}
.cloze {
    font-weight: bold;
    color: #d84315;
    background-color: #fff3e0;
    padding: 2px 6px;
    border-radius: 4px;
}
.pronoun { color: #666; min-width: 50px; display: inline-block; }
.notes {
    font-size: 15px;
    color: #555;
    margin-top: 20px;
    padding: 12px;
    background-color: #fff8e1;
    border-radius: 8px;
    text-align: left;
    border-left: 4px solid #ffc107;
}
.group-label { font-size: 12px; color: #888; margin: 15px 0 5px 0; }
"""

# TEMPLATES
RECOG_FRONT = """
<div class="direction">FR -> RU</div>
<div class="main-word" id="main-word">
    {{French}}{{#Audio}}<span class="audio-btn">{{Audio}}</span>{{/Audio}}<span class="gender-tag" id="gender-tag">{{WordType}}</span>
</div>
{{#ExampleFrench}}
<div class="example">
    {{ExampleFrench}}{{#AudioExample}}<span class="audio-btn">{{AudioExample}}</span>{{/AudioExample}}
</div>
{{/ExampleFrench}}
<script>
(function() {
    var g = '{{WordType}}'.trim().toLowerCase();
    var mainWord = document.getElementById('main-word');
    var genderTag = document.getElementById('gender-tag');
    var validTypes = ['m','f','v','adj','adv','conj','prep','pron','num','interj','expr','loc'];
    if (validTypes.includes(g)) {
        mainWord.classList.add('gender-' + g);
        genderTag.classList.add('gender-' + g);
    } else {
        genderTag.classList.add('gender-other');
    }
})();
</script>
"""

RECOG_BACK = """
<div class="direction">FR -> RU</div>
<div class="main-word" id="main-word">
    {{French}}{{#Audio}}<span class="audio-btn">{{Audio}}</span>{{/Audio}}<span class="gender-tag" id="gender-tag">{{WordType}}</span>
</div>
{{#ExampleFrench}}
<div class="example">
    {{ExampleFrench}}{{#AudioExample}}<span class="audio-btn">{{AudioExample}}</span>{{/AudioExample}}
</div>
{{/ExampleFrench}}
<hr>
<div class="translation">{{#Emoji}}<span class="emoji">{{Emoji}}</span>{{/Emoji}}{{Russian}}</div>
{{#ExampleFrench}}
<div class="example">
    {{#ExampleRussian}}
    <div class="example-translation">{{ExampleRussian}}</div>
    {{/ExampleRussian}}
</div>
{{/ExampleFrench}}
{{#Notes}}
<div class="notes">{{Notes}}</div>
{{/Notes}}
<script>
(function() {
    var g = '{{WordType}}'.trim().toLowerCase();
    var mainWord = document.getElementById('main-word');
    var genderTag = document.getElementById('gender-tag');
    var validTypes = ['m','f','v','adj','adv','conj','prep','pron','num','interj','expr','loc'];
    if (validTypes.includes(g)) {
        mainWord.classList.add('gender-' + g);
        genderTag.classList.add('gender-' + g);
    } else {
        genderTag.classList.add('gender-other');
    }
})();
</script>
"""

PROD_FRONT = """
<div class="direction">RU -> FR</div>
<div class="main-word">{{Russian}}</div>
{{#ExampleRussian}}
<div class="example">{{ExampleRussian}}</div>
{{/ExampleRussian}}
"""

PROD_BACK = """
<div class="direction">RU -> FR</div>
<div class="main-word">{{Russian}}</div>
{{#ExampleRussian}}
<div class="example">{{ExampleRussian}}</div>
{{/ExampleRussian}}
<hr>
<div class="main-word" id="main-word">
    {{#Emoji}}<span class="emoji">{{Emoji}}</span>{{/Emoji}}{{French}}{{#Audio}}<span class="audio-btn">{{Audio}}</span>{{/Audio}}<span class="gender-tag" id="gender-tag">{{WordType}}</span>
</div>
{{#ExampleFrench}}
<div class="example">
    {{ExampleFrench}}{{#AudioExample}}<span class="audio-btn">{{AudioExample}}</span>{{/AudioExample}}
</div>
{{/ExampleFrench}}
{{#Notes}}
<div class="notes">{{Notes}}</div>
{{/Notes}}
<script>
(function() {
    var g = '{{WordType}}'.trim().toLowerCase();
    var mainWord = document.getElementById('main-word');
    var genderTag = document.getElementById('gender-tag');
    var validTypes = ['m','f','v','adj','adv','conj','prep','pron','num','interj','expr','loc'];
    if (validTypes.includes(g)) {
        mainWord.classList.add('gender-' + g);
        genderTag.classList.add('gender-' + g);
    } else {
        genderTag.classList.add('gender-other');
    }
})();
</script>
"""

CLOZE_TEMPLATE = """
<div class="verb-header">{{Verb}}</div>
<div class="verb-translation">{{Translation}}</div>
{{#Tense}}<div class="tense">{{Tense}}</div>{{/Tense}}
{{#c1}}
<div class="group-label">Singulier</div>
<div class="conjugation">{{cloze:ConjSingular}}</div>
{{/c1}}
{{#c2}}
<div class="group-label">Pluriel</div>
<div class="conjugation">{{cloze:ConjPlural}}</div>
{{/c2}}
{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
"""

# MODELS
vocab_model = genanki.Model(
    VOCAB_MODEL_ID,
    'French Vocabulary v3 (FR-RU)',
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
        {'name': 'Recognition (FR->RU)', 'qfmt': RECOG_FRONT, 'afmt': RECOG_BACK},
        {'name': 'Production (RU->FR)', 'qfmt': PROD_FRONT, 'afmt': PROD_BACK},
    ],
    css=VOCAB_CSS,
)

cloze_model = genanki.Model(
    CLOZE_MODEL_ID,
    'French Conjugation v3 (Cloze)',
    model_type=genanki.Model.CLOZE,
    fields=[
        {'name': 'Verb'},
        {'name': 'Translation'},
        {'name': 'Tense'},
        {'name': 'ConjSingular'},
        {'name': 'ConjPlural'},
        {'name': 'Notes'},
    ],
    templates=[{'name': 'Conjugation Cloze', 'qfmt': CLOZE_TEMPLATE, 'afmt': CLOZE_TEMPLATE}],
    css=CLOZE_CSS,
)

# DECKS
vocab_deck = genanki.Deck(VOCAB_DECK_ID, 'French::Vocabulary::Core')
conj_deck = genanki.Deck(CONJ_DECK_ID, 'French::Grammar::Conjugation')

# SAMPLE DATA
vocab_samples = [
    ("une maison", "дом", "f",
     "Nous avons acheté <b>une maison</b> dans la banlieue.",
     "Мы купили <b>дом</b> в пригороде.",
     "Женский род", "", "", ""),
    ("un travail", "работа", "m",
     "Je cherche <b>un travail</b>.",
     "Я ищу <b>работу</b>.",
     "Мужской род", "", "", ""),
    ("améliorer", "улучшать", "v",
     "Il faut <b>améliorer</b> mon niveau.",
     "Нужно <b>улучшить</b> мой уровень.",
     "Groupe 1", "", "", ""),
    ("cependant", "однако", "conj",
     "C'est intéressant; <b>cependant</b>, c'est difficile.",
     "Это интересно; <b>однако</b>, это сложно.",
     "Connecteur logique", "", "", ""),
    ("rapidement", "быстро", "adv",
     "Il faut agir <b>rapidement</b>.",
     "Нужно действовать <b>быстро</b>.",
     "", "", "", ""),
    ("important", "важный", "adj",
     "C'est une décision <b>importante</b>.",
     "Это <b>важное</b> решение.",
     "", "", "", ""),
    ("celui-ci", "этот", "pron",
     "<b>Celui-ci</b> est plus intéressant.",
     "<b>Этот</b> интереснее.",
     "Указательное местоимение", "", "", ""),
    ("hélas", "увы", "interj",
     "<b>Hélas</b>, je n'ai pas réussi.",
     "<b>Увы</b>, я не сдал.",
     "", "", "", ""),
]

for card in vocab_samples:
    note = genanki.Note(model=vocab_model, fields=list(card), tags=['demo'])
    vocab_deck.add_note(note)

conj_samples = [
    ("aller", "идти", "Présent",
     '<span class="pronoun">je</span> {{c1::vais}}<br><span class="pronoun">tu</span> {{c1::vas}}<br><span class="pronoun">il</span> {{c1::va}}',
     '<span class="pronoun">nous</span> {{c2::allons}}<br><span class="pronoun">vous</span> {{c2::allez}}<br><span class="pronoun">ils</span> {{c2::vont}}',
     "Неправильный глагол"),
    ("être", "быть", "Présent",
     '<span class="pronoun">je</span> {{c1::suis}}<br><span class="pronoun">tu</span> {{c1::es}}<br><span class="pronoun">il</span> {{c1::est}}',
     '<span class="pronoun">nous</span> {{c2::sommes}}<br><span class="pronoun">vous</span> {{c2::êtes}}<br><span class="pronoun">ils</span> {{c2::sont}}',
     "Вспомогательный глагол"),
    ("avoir", "иметь", "Présent",
     "<span class=\"pronoun\">j'</span>{{c1::ai}}<br><span class=\"pronoun\">tu</span> {{c1::as}}<br><span class=\"pronoun\">il</span> {{c1::a}}",
     '<span class="pronoun">nous</span> {{c2::avons}}<br><span class="pronoun">vous</span> {{c2::avez}}<br><span class="pronoun">ils</span> {{c2::ont}}',
     "Вспомогательный глагол"),
]

for card in conj_samples:
    note = genanki.Note(model=cloze_model, fields=list(card), tags=['demo'])
    conj_deck.add_note(note)

# EXPORT
package = genanki.Package([vocab_deck, conj_deck])
package.write_to_file('French_Learning_Deck_v3.apkg')

print("Created: French_Learning_Deck_v3.apkg")
print(f"Vocabulary: {len(vocab_samples)} cards")
print(f"Conjugation: {len(conj_samples)} verbs")
