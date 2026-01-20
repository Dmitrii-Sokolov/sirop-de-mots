"""
Anki deck hierarchy configuration.

Deck naming uses :: separator for hierarchy.
"""

# Root deck name
ROOT_DECK = "French TEF-TCF"

# Vocabulary subdecks by CEFR level and batch ranges
VOCABULARY_DECKS = {
    f"{ROOT_DECK}::Vocabulaire::A1-A2 (Top 1000)": {
        "batches": range(1, 11),      # batch_001 - batch_010
        "description": "1000 most frequent words",
    },
    f"{ROOT_DECK}::Vocabulaire::B1 (Top 3000)": {
        "batches": range(11, 31),     # batch_011 - batch_030
        "description": "Words 1001-3000 by frequency",
    },
    f"{ROOT_DECK}::Vocabulaire::B2 (Top 5000)": {
        "batches": range(31, 51),     # batch_031 - batch_050
        "description": "Words 3001-5000 by frequency",
    },
    f"{ROOT_DECK}::Vocabulaire::C1+ (Top 10000)": {
        "batches": range(51, 123),    # batch_051 - batch_122
        "description": "Words 5001+ by frequency",
    },
}

# Other content decks
CONTENT_DECKS = {
    f"{ROOT_DECK}::Expressions": {
        "source": "content/expressions/all.csv",
        "description": "469 French expressions and idioms",
    },
    f"{ROOT_DECK}::Québécismes": {
        "source": "content/quebecismes/all.csv",
        "description": "566 Quebec French words",
    },
}

# Conjugation subdecks
CONJUGATION_DECKS = {
    f"{ROOT_DECK}::Conjugaison::Présent": {
        "source": "content/conjugation/present.csv",
        "description": "341 verbs - present tense",
    },
    f"{ROOT_DECK}::Conjugaison::Subjonctif": {
        "source": "content/conjugation/subjonctif.csv",
        "description": "10 irregular verbs - subjunctive",
    },
    f"{ROOT_DECK}::Conjugaison::Participes": {
        "source": "content/conjugation/participes.csv",
        "description": "110 irregular past participles",
    },
    f"{ROOT_DECK}::Conjugaison::Futur": {
        "source": "content/conjugation/futur_stems.csv",
        "description": "22 irregular future stems",
    },
    f"{ROOT_DECK}::Conjugaison::Verbes être": {
        "source": "content/conjugation/etre_verbs.csv",
        "description": "17 DR MRS VANDERTRAMP verbs",
    },
}

# Summary
def print_summary():
    """Print deck structure summary."""
    print(f"\n{ROOT_DECK}/")

    print(f"├── {ROOT_DECK}::Vocabulaire/")
    for deck, info in VOCABULARY_DECKS.items():
        batches = info["batches"]
        name = deck.split("::")[-1]
        print(f"│   ├── {name} (batches {batches.start:03d}-{batches.stop-1:03d})")

    for deck, info in CONTENT_DECKS.items():
        name = deck.split("::")[-1]
        print(f"├── {name}")

    print(f"└── {ROOT_DECK}::Conjugaison/")
    for deck, info in CONJUGATION_DECKS.items():
        name = deck.split("::")[-1]
        print(f"    ├── {name}")


if __name__ == "__main__":
    print_summary()
