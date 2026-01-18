#!/usr/bin/env python3
"""
Выборка лемм из Lexique383:
- VER, NOM, ADJ, ADV: топ-10000 по сумме частотностей
- Остальные категории: все леммы
- Разделение по файлам: категории ≥100 слов отдельно, остальные в other.csv
"""

import sys
import pandas as pd
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from scripts.config import FREQ_FILMS_WEIGHT, FREQ_BOOKS_WEIGHT

LEXIQUE_PATH = Path("Lexique383.tsv")
OUTPUT_DIR = Path("categories")

# Категории с фильтром по частотности
FREQ_FILTERED_CATEGORIES = ['VER', 'NOM', 'ADJ', 'ADV']
TOP_N = 10000

# Порог для отдельного файла
MIN_CATEGORY_SIZE = 100

# Выходные колонки
OUTPUT_COLS = ['lemme', 'cgram', 'genre', 'freqlem', 'forms']


def get_verb_forms(df: pd.DataFrame) -> dict[tuple[str, str], str]:
    """
    Собирает формы глаголов по infover для каждой леммы.

    Returns:
        dict[(lemme, cgram)] -> "inf, par.passé (par.présent)"
    """
    verb_forms = {}

    # Фильтруем только глаголы
    verbs_df = df[df['cgram'].isin(['VER', 'AUX'])].copy()

    for (lemme, cgram), group in verbs_df.groupby(['lemme', 'cgram']):
        forms = {
            'inf': '',
            'par_pas_ms': '',  # причастие прош. м.ед.
            'par_pas_fs': '',  # причастие прош. ж.ед.
            'par_pre': '',     # причастие наст.
        }

        for _, row in group.iterrows():
            infover = row['infover'] if pd.notna(row['infover']) else ''
            ortho = row['ortho']
            genre = row['genre'] if pd.notna(row['genre']) else ''
            nombre = row['nombre'] if pd.notna(row['nombre']) else ''

            if 'inf' in infover:
                # Предпочитаем форму, совпадающую с леммой (защита от ошибок в данных)
                if ortho == lemme or not forms['inf']:
                    forms['inf'] = ortho
            elif 'par:pas' in infover:
                # nombre может быть пустым для м.р. ед.ч. (pris, mis, etc.)
                if genre == 'm' and nombre in ('s', ''):
                    forms['par_pas_ms'] = ortho
                elif genre == 'f' and nombre == 's':
                    forms['par_pas_fs'] = ortho
            elif 'par:pre' in infover:
                forms['par_pre'] = ortho

        # Формируем строку
        verb_forms[(lemme, cgram)] = _format_verb_forms(lemme, forms)

    return verb_forms


def _format_verb_forms(lemme: str, forms: dict) -> str:
    """
    Форматирует глагольные формы.

    Формат: "inf, par.passé (par.présent)"
    Примеры:
        parler, parlé/parlée (parlant)
        être, été (étant)
        finir, fini/finie (finissant)
    """
    inf = forms['inf'] or lemme
    par_pas_ms = forms['par_pas_ms']
    par_pas_fs = forms['par_pas_fs']
    par_pre = forms['par_pre']

    parts = [inf]

    # Причастие прошедшего времени
    if par_pas_ms:
        if par_pas_fs and par_pas_fs != par_pas_ms:
            parts.append(f"{par_pas_ms}/{par_pas_fs}")
        else:
            parts.append(par_pas_ms)

    # Причастие настоящего времени
    if par_pre:
        result = ', '.join(parts)
        return f"{result} ({par_pre})"

    return ', '.join(parts)


def get_word_forms(df: pd.DataFrame) -> dict[tuple[str, str], str]:
    """
    Собирает формы слов по роду и числу для каждой леммы+cgram.
    Для глаголов используйте get_verb_forms().

    При наличии нескольких форм в одной группе (genre, nombre) выбирается
    форма с наибольшей частотностью (например, yeux вместо oeils).

    Returns:
        dict[(lemme, cgram)] -> "форма1/форма2 форма3/форма4"
    """
    forms_dict = {}

    # Группируем по лемме и грамматической категории (исключаем глаголы)
    non_verbs = df[~df['cgram'].isin(['VER', 'AUX'])]

    for (lemme, cgram), group in non_verbs.groupby(['lemme', 'cgram']):
        # Собираем формы по роду и числу с частотностью
        # (genre, nombre) -> {ortho: freq}
        forms_by_gn = {}

        for _, row in group.iterrows():
            genre = row['genre'] if pd.notna(row['genre']) else ''
            nombre = row['nombre'] if pd.notna(row['nombre']) else ''
            ortho = row['ortho']
            # Частотность формы (не леммы)
            freq = (row['freqfilms2'] if pd.notna(row['freqfilms2']) else 0) + \
                   (row['freqlivres'] if pd.notna(row['freqlivres']) else 0)

            key = (genre, nombre)
            if key not in forms_by_gn:
                forms_by_gn[key] = {}
            # Сохраняем форму с максимальной частотностью
            if ortho not in forms_by_gn[key] or freq > forms_by_gn[key][ortho]:
                forms_by_gn[key][ortho] = freq

        # Конвертируем в set, выбирая самую частую форму для каждой группы
        forms_by_gn_sets = {}
        for key, ortho_freq in forms_by_gn.items():
            genre, nombre = key
            if len(ortho_freq) == 1:
                forms_by_gn_sets[key] = set(ortho_freq.keys())
            elif nombre == '':
                # Группы без числа ('m', ''), ('f', ''), ('', '') — сохраняем все формы
                # Это могут быть ед./мн. формы (cinquième/cinquièmes) или invariable
                forms_by_gn_sets[key] = set(ortho_freq.keys())
            else:
                # Выбираем форму с максимальной частотностью
                # При равной частотности — предпочитаем более длинную (нерегулярную)
                max_freq = max(ortho_freq.values())
                top_forms = [o for o, f in ortho_freq.items() if f >= max_freq * 0.9]
                if len(top_forms) == 1:
                    forms_by_gn_sets[key] = {top_forms[0]}
                else:
                    # При равной частотности — предпочитаем длинную форму (glaciaux > glacials)
                    # При равной длине — предпочитаем нерегулярную форму (не на -s)
                    best_ortho = max(top_forms, key=lambda x: (len(x), not x.endswith('s')))
                    forms_by_gn_sets[key] = {best_ortho}

        # Формируем строку форм
        forms_str = _format_forms(lemme, forms_by_gn_sets)
        forms_dict[(lemme, cgram)] = forms_str

    return forms_dict


def _format_forms(lemme: str, forms_by_gn: dict) -> str:
    """
    Форматирует формы слова в строку.

    Форматы:
    - Одна форма: lemme
    - Две формы (ед./мн.): "ед, мн"
    - Четыре формы (м/ж × ед/мн): "м.ед/ж.ед м.мн/ж.мн"
    - Invariable с несколькими формами: "форма1, форма2" (отсортировано по длине)
    """
    # Специальный случай 1: группа без числа с несколькими формами
    # Например: cinquième/cinquièmes в ('m', ''), deuxième/deuxièmes в ('', '')
    for key in [('m', ''), ('f', ''), ('', '')]:
        forms = forms_by_gn.get(key, set())
        if len(forms) > 1 and len(forms_by_gn) == 1:
            # Сортируем по длине (ед.ч. обычно короче мн.ч.)
            sorted_forms = sorted(forms, key=len)
            return ', '.join(sorted_forms)

    # Специальный случай 2: ('', '') + ('', 'p') — ед.ч. без числа + мн.ч.
    # Например: livre/livres, mort/morts
    empty_no_number = forms_by_gn.get(('', ''), set())
    empty_p = forms_by_gn.get(('', 'p'), set())
    if empty_no_number and empty_p and len(forms_by_gn) == 2:
        sg = next(iter(empty_no_number))
        pl = next(iter(empty_p))
        return f'{sg}, {pl}'

    # Специальный случай 3: только ('', 's') и ('', 'p') — invariable с ед./мн.
    # Например: fin/fins, где genre пустой но nombre указан
    empty_s = forms_by_gn.get(('', 's'), set())
    if empty_s and empty_p and len(forms_by_gn) == 2:
        sg = next(iter(empty_s))
        pl = next(iter(empty_p))
        return f'{sg}, {pl}'

    # Извлекаем формы по позициям
    empty_s = forms_by_gn.get(('', 's'), set())
    empty_p = forms_by_gn.get(('', 'p'), set())
    empty_no_num = forms_by_gn.get(('', ''), set())

    has_m_s = ('m', 's') in forms_by_gn
    has_f_s = ('f', 's') in forms_by_gn
    has_empty_s = ('', 's') in forms_by_gn

    # Единственное число:
    # - ('m', 's') → ms
    # - ('f', 's') → fs
    # - ('', 's') → ms если есть ('f', 's'), иначе и ms и fs (invariable)
    # - ('', '') → ms/fs fallback если нет других
    ms = forms_by_gn.get(('m', 's'), set())
    fs = forms_by_gn.get(('f', 's'), set())

    # ('', 's') используется как ms когда есть отдельная женская форма
    if not ms and has_empty_s:
        if has_f_s:
            # saint/sainte — ('', 's') это мужская форма
            ms = empty_s
        else:
            # fin — ('', 's') это общая форма (invariable)
            ms = empty_s

    # ('m', '') как мужское (vieux, héros — без числа, одна форма для ед. и мн.)
    m_no_num = forms_by_gn.get(('m', ''), set())
    if not ms and m_no_num:
        ms = m_no_num

    # ('', '') как мужское единственное (mort, livre)
    # Используется когда нет ('m', 's') и нет ('', 's')
    if not ms and empty_no_num:
        ms = empty_no_num

    # Множественное число:
    mp = forms_by_gn.get(('m', 'p'), set())
    fp = forms_by_gn.get(('f', 'p'), set())

    # Fallback для множественного:
    # 1. ('m', '') без числа = ед. и мн. одинаковые (vieux, héros)
    # 2. ('', 'p') используется если есть
    # 3. Иначе, если только одна форма мн.ч. (fp или mp) — используем её
    if not mp:
        if m_no_num:
            # vieux: ('m', '') — одна форма для ед. и мн.
            mp = m_no_num
        elif empty_p and (ms or has_m_s or has_empty_s):
            mp = empty_p
        elif fp and not fs:
            # main: ('', 's') + ('f', 'p') — fp это единственное мн.ч.
            mp = fp
    if not fp and fs:
        if empty_p and not mp:
            fp = empty_p
        elif mp and not ms:
            fp = mp

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
    word_forms = get_word_forms(df)
    print(f"   Собрано форм для {len(word_forms):,} не-глаголов")

    print("📝 Собираем формы глаголов...")
    verb_forms = get_verb_forms(df)
    print(f"   Собрано форм для {len(verb_forms):,} глаголов")

    # Объединяем словари
    forms_dict = {**word_forms, **verb_forms}

    # 1. Только леммы
    lemmas = df[df['islem'] == 1].copy()
    print(f"📋 Лемм (islem=1): {len(lemmas):,}")

    # 2. Вычисляем freqlem (взвешенная формула из config.py)
    lemmas['freqlem'] = (
        FREQ_FILMS_WEIGHT * lemmas['freqlemfilms2'].fillna(0) +
        FREQ_BOOKS_WEIGHT * lemmas['freqlemlivres'].fillna(0)
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

    print(f"\n📝 Превью VER (первые 10 строк):")
    ver_preview = result[result['cgram'] == 'VER'].nlargest(10, 'freqlem')
    print(ver_preview.to_string(index=False))


if __name__ == "__main__":
    main()
