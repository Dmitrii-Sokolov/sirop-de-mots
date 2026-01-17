#!/usr/bin/env python3
"""
Выборка лемм из Lexique383:
- VER, NOM, ADJ, ADV: топ-10000 по сумме частотностей
- Остальные категории: все леммы
- Разделение по файлам: категории ≥100 слов отдельно, остальные в other.csv
"""

import pandas as pd
from pathlib import Path

LEXIQUE_PATH = Path("Lexique383.tsv")
OUTPUT_DIR = Path("categories")

# Категории с фильтром по частотности
FREQ_FILTERED_CATEGORIES = ['VER', 'NOM', 'ADJ', 'ADV']
TOP_N = 10000

# Порог для отдельного файла
MIN_CATEGORY_SIZE = 100

# Выходные колонки
OUTPUT_COLS = ['lemme', 'cgram', 'genre', 'freqlem', 'forms', 'nbhomogr']


def get_word_forms(df: pd.DataFrame) -> dict[tuple[str, str], str]:
    """
    Собирает формы слов по роду и числу для каждой леммы+cgram.

    Returns:
        dict[(lemme, cgram)] -> "форма1/форма2 форма3/форма4"
    """
    forms_dict = {}

    # Группируем по лемме и грамматической категории
    for (lemme, cgram), group in df.groupby(['lemme', 'cgram']):
        # Собираем формы по роду и числу
        forms_by_gn = {}  # (genre, nombre) -> set(ortho)

        for _, row in group.iterrows():
            genre = row['genre'] if pd.notna(row['genre']) else ''
            nombre = row['nombre'] if pd.notna(row['nombre']) else ''
            ortho = row['ortho']

            key = (genre, nombre)
            if key not in forms_by_gn:
                forms_by_gn[key] = set()
            forms_by_gn[key].add(ortho)

        # Формируем строку форм
        forms_str = _format_forms(lemme, forms_by_gn)
        forms_dict[(lemme, cgram)] = forms_str

    return forms_dict


def _format_forms(lemme: str, forms_by_gn: dict) -> str:
    """
    Форматирует формы слова в строку.

    Форматы:
    - Одна форма: lemme
    - Две формы (ед./мн.): ед, мн
    - Четыре формы (м/ж × ед/мн): м.ед/ж.ед м.мн/ж.мн
    """
    # Извлекаем формы по позициям
    ms = forms_by_gn.get(('m', 's'), forms_by_gn.get(('', 's'), set()))
    fs = forms_by_gn.get(('f', 's'), set())
    mp = forms_by_gn.get(('m', 'p'), forms_by_gn.get(('', 'p'), set()))
    fp = forms_by_gn.get(('f', 'p'), set())

    # Если нет данных о числе, берём формы без указания числа
    if not ms and not mp:
        ms = forms_by_gn.get(('m', ''), forms_by_gn.get(('', ''), set()))
    if not fs and not fp:
        fs = forms_by_gn.get(('f', ''), set())

    # Получаем первую форму из каждого множества
    def first(s):
        return next(iter(s)) if s else ''

    ms_form = first(ms)
    fs_form = first(fs)
    mp_form = first(mp)
    fp_form = first(fp)

    # Собираем уникальные формы
    all_forms = {f for f in [ms_form, fs_form, mp_form, fp_form] if f}

    if len(all_forms) == 0:
        return lemme

    if len(all_forms) == 1:
        return first(all_forms)

    # Есть различия по роду?
    has_gender_diff = fs_form and ms_form and fs_form != ms_form
    # Есть различия по числу?
    has_number_diff = (mp_form and ms_form and mp_form != ms_form) or \
                      (fp_form and fs_form and fp_form != fs_form)

    if has_gender_diff and has_number_diff:
        # Четыре формы: м.ед/ж.ед м.мн/ж.мн
        sg = f"{ms_form}/{fs_form}" if ms_form and fs_form else (ms_form or fs_form)
        pl = f"{mp_form}/{fp_form}" if mp_form and fp_form else (mp_form or fp_form)
        if pl:
            return f"{sg} {pl}"
        return sg
    elif has_gender_diff:
        # Две формы по роду: м/ж
        return f"{ms_form}/{fs_form}"
    elif has_number_diff:
        # Две формы по числу: ед, мн
        sg = ms_form or fs_form
        pl = mp_form or fp_form
        return f"{sg}, {pl}"
    else:
        # Одна форма
        return first(all_forms)


def main():
    if not LEXIQUE_PATH.exists():
        print(f"❌ Файл {LEXIQUE_PATH} не найден!")
        print("   Скачай с: http://www.lexique.org/databases/Lexique383/Lexique383.tsv")
        return

    # Создаём папку для выходных файлов
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Загрузка
    df = pd.read_csv(LEXIQUE_PATH, sep='\t', low_memory=False)
    print(f"✅ Загружено {len(df):,} записей из Lexique383")

    # Собираем формы слов (до фильтрации по islem)
    print("📝 Собираем формы слов...")
    forms_dict = get_word_forms(df)
    print(f"   Собрано форм для {len(forms_dict):,} лемм")

    # 1. Только леммы
    lemmas = df[df['islem'] == 1].copy()
    print(f"📋 Лемм (islem=1): {len(lemmas):,}")

    # 2. Вычисляем freqlem
    lemmas['freqlem'] = (
        lemmas['freqlemfilms2'].fillna(0) +
        lemmas['freqlemlivres'].fillna(0)
    )

    # 3. Добавляем формы
    lemmas['forms'] = lemmas.apply(
        lambda row: forms_dict.get((row['lemme'], row['cgram']), row['lemme']),
        axis=1
    )

    # 4. Разделяем на две группы
    freq_filtered = lemmas[lemmas['cgram'].isin(FREQ_FILTERED_CATEGORIES)].copy()
    other = lemmas[~lemmas['cgram'].isin(FREQ_FILTERED_CATEGORIES)].copy()

    print(f"\n📊 Категории с фильтром ({', '.join(FREQ_FILTERED_CATEGORIES)}):")
    print(f"   Всего: {len(freq_filtered):,}")

    # 5. Для VER/NOM/ADJ/ADV: топ-10000 по freqlem
    freq_filtered = freq_filtered.nlargest(TOP_N, 'freqlem')
    print(f"✂️  После фильтра топ-{TOP_N:,}: {len(freq_filtered):,}")

    # Статистика по категориям в топе
    print(f"\n📈 Распределение в топ-{TOP_N:,}:")
    for cat in FREQ_FILTERED_CATEGORIES:
        count = len(freq_filtered[freq_filtered['cgram'] == cat])
        print(f"   {cat:<6} {count:>6}")

    # 6. Объединяем (исключаем записи без категории)
    other = other[other['cgram'].notna()]
    result = pd.concat([freq_filtered, other], ignore_index=True)

    # 7. Оставляем нужные колонки
    result = result[OUTPUT_COLS].copy()

    # 8. Разделяем по категориям
    category_counts = result['cgram'].value_counts()

    large_categories = category_counts[category_counts >= MIN_CATEGORY_SIZE].index.tolist()
    small_categories = category_counts[category_counts < MIN_CATEGORY_SIZE].index.tolist()

    print(f"\n📁 Категории для отдельных файлов (≥{MIN_CATEGORY_SIZE}):")
    for cat in sorted(large_categories):
        print(f"   {cat:<12} {category_counts[cat]:>6}")

    print(f"\n📁 Категории для other.csv (<{MIN_CATEGORY_SIZE}):")
    for cat in sorted(small_categories):
        print(f"   {cat:<12} {category_counts[cat]:>6}")

    # 9. Сохраняем файлы
    total_saved = 0

    for cat in large_categories:
        cat_data = result[result['cgram'] == cat].copy()
        cat_data = cat_data.sort_values('freqlem', ascending=False)

        # Имя файла: заменяем : на _
        filename = cat.replace(':', '_') + '.csv'
        filepath = OUTPUT_DIR / filename
        cat_data.to_csv(filepath, index=False)

        print(f"   💾 {filename}: {len(cat_data):,} лемм")
        total_saved += len(cat_data)

    # Сохраняем other.csv
    other_data = result[result['cgram'].isin(small_categories)].copy()
    other_data = other_data.sort_values(['cgram', 'freqlem'], ascending=[True, False])
    other_path = OUTPUT_DIR / 'other.csv'
    other_data.to_csv(other_path, index=False)

    print(f"   💾 other.csv: {len(other_data):,} лемм")
    total_saved += len(other_data)

    print(f"\n" + "=" * 60)
    print(f"✅ ИТОГО: {total_saved:,} лемм")
    print(f"📁 Сохранено в: {OUTPUT_DIR}/")
    print("=" * 60)

    # Превью
    print(f"\n📝 Превью ADJ (первые 5 строк):")
    adj_preview = result[result['cgram'] == 'ADJ'].nlargest(5, 'freqlem')
    print(adj_preview.to_string(index=False))


if __name__ == "__main__":
    main()
