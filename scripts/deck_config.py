"""
Anki deck hierarchy configuration.

Deck naming uses :: separator for hierarchy.
"""

# Root deck name
ROOT_DECK = "French TEF-TCF"

# Vocabulary subdecks by CEFR level (NOM, VER, ADJ only)
VOCABULARY_DECKS = {
    f"{ROOT_DECK}::Vocabulaire::A1-A2": {
        "source": "content/vocabulary/a1_a2.csv",
        "count": 769,
        "description": "Top 1000 nouns, verbs, adjectives",
    },
    f"{ROOT_DECK}::Vocabulaire::B1": {
        "source": "content/vocabulary/b1.csv",
        "count": 1821,
        "description": "Words 1001-3000 by frequency",
    },
    f"{ROOT_DECK}::Vocabulaire::B2": {
        "source": "content/vocabulary/b2.csv",
        "count": 1829,
        "description": "Words 3001-5000 by frequency",
    },
    f"{ROOT_DECK}::Vocabulaire::C1+": {
        "source": "content/vocabulary/c1.csv",
        "count": 5120,
        "description": "Words 5001+ by frequency",
    },
}

# Other word types (adv, pron, prep, conj, interj, num, art)
AUTRES_DECK = {
    f"{ROOT_DECK}::Vocabulaire::Autres": {
        "source": "content/vocabulary/autres.csv",
        "count": 990,
        "description": "Adverbs, pronouns, prepositions, conjunctions, etc.",
    },
}

# Other content decks
CONTENT_DECKS = {
    f"{ROOT_DECK}::Expressions": {
        "source": "content/expressions/all.csv",
        "count": 469,
        "description": "French expressions and idioms",
    },
    f"{ROOT_DECK}::Québécismes": {
        "source": "content/quebecismes/all.csv",
        "count": 566,
        "description": "Quebec French words",
    },
}

# Conjugation subdecks
CONJUGATION_DECKS = {
    f"{ROOT_DECK}::Conjugaison::Présent": {
        "source": "content/conjugation/present.csv",
        "count": 360,
        "description": "Present tense - 3rd group + stem-changing",
    },
    f"{ROOT_DECK}::Conjugaison::Subjonctif": {
        "source": "content/conjugation/subjonctif.csv",
        "count": 10,
        "description": "Subjunctive - irregular only",
    },
    f"{ROOT_DECK}::Conjugaison::Participes": {
        "source": "content/conjugation/participes.csv",
        "count": 110,
        "description": "Past participles - irregular only",
    },
    f"{ROOT_DECK}::Conjugaison::Futur": {
        "source": "content/conjugation/futur_stems.csv",
        "count": 22,
        "description": "Future stems - irregular only",
    },
    f"{ROOT_DECK}::Conjugaison::Verbes être": {
        "source": "content/conjugation/etre_verbs.csv",
        "count": 17,
        "description": "DR MRS VANDERTRAMP verbs",
    },
}

# All vocabulary sources for audio generation
ALL_VOCABULARY_SOURCES = [
    "content/vocabulary/a1_a2.csv",
    "content/vocabulary/b1.csv",
    "content/vocabulary/b2.csv",
    "content/vocabulary/c1.csv",
    "content/vocabulary/autres.csv",
]


def print_summary():
    """Print deck structure summary."""
    print(f"\n{ROOT_DECK}/")

    print(f"├── Vocabulaire/")
    for deck, info in VOCABULARY_DECKS.items():
        name = deck.split("::")[-1]
        print(f"│   ├── {name} ({info['count']})")

    for deck, info in AUTRES_DECK.items():
        name = deck.split("::")[-1]
        print(f"│   └── {name} ({info['count']})")

    for deck, info in CONTENT_DECKS.items():
        name = deck.split("::")[-1]
        print(f"├── {name} ({info['count']})")

    print(f"└── Conjugaison/")
    items = list(CONJUGATION_DECKS.items())
    for i, (deck, info) in enumerate(items):
        name = deck.split("::")[-1]
        prefix = "    └──" if i == len(items) - 1 else "    ├──"
        print(f"{prefix} {name} ({info['count']})")

    # Total
    total_vocab = sum(d["count"] for d in VOCABULARY_DECKS.values())
    total_vocab += sum(d["count"] for d in AUTRES_DECK.values())
    total_content = sum(d["count"] for d in CONTENT_DECKS.values())
    total_conj = sum(d["count"] for d in CONJUGATION_DECKS.values())

    print(f"\nTotals:")
    print(f"  Vocabulaire: {total_vocab}")
    print(f"  Expressions + Québécismes: {total_content}")
    print(f"  Conjugaison: {total_conj}")
    print(f"  TOTAL: {total_vocab + total_content + total_conj}")


if __name__ == "__main__":
    print_summary()
