import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'knowledge_base.db')
POSTS_JSON_PATH = os.path.join(BASE_DIR, 'web_app', 'posts.json')
DATA_JS_PATH = os.path.join(BASE_DIR, 'web_app', 'data.js')

HUB_TITLES = {
    'ai': '🤖 AI & Нейросети',
    'marketing': '📈 Маркетинг & E-com',
    'business': '🛠 Бизнес & Управление',
    'useful': '📌 Полезный софт & IT'
}

def classify_post(pid, u_coll, title, tools, tags, cap, idea, ins):
    tls_str = ' '.join(tools).lower()
    tags_str = ' '.join(tags).lower()
    text = f'{title} {cap} {idea} {ins} {tls_str} {tags_str}'.lower()
    u_coll_clean = (u_coll or '').strip().lower()

    # =========================================================================
    # 1. МАРКЕТПЛЕЙСЫ (Highest priority for any WB / Ozon / MPStats)
    # =========================================================================
    if u_coll_clean == 'mplaces' or any(k in text for k in [
        'wildberries', 'вайлдберриз', 'ozon', 'озон', 'mpstats', 'карточка товара', 
        'спп', 'соинвест ozon', 'transgran', 'fbs', 'fbo', 'честный знак', 'киз'
    ]):
        if any(k in text for k in ['claude', 'клод', 'агент', 'ии', 'нейросеть']):
            return ('marketing', 'Маркетплейсы (WB / Ozon)', 'AI-автоматизация селлеров')
        if any(k in text for k in ['mpstats', 'ниша', 'топ']):
            return ('marketing', 'Маркетплейсы (WB / Ozon)', 'Аналитика ниш & Топ-позиции (MPStats)')
        if any(k in text for k in ['сборк', 'fbs', 'fbo', 'стикер', 'transgran', 'киз', 'маркировк']):
            return ('marketing', 'Маркетплейсы (WB / Ozon)', 'Фулфилмент, Сборка FBS & Маркировка')
        return ('marketing', 'Маркетплейсы (WB / Ozon)', 'Оптимизация карточек & СПП')

    # =========================================================================
    # 2. МЕНЕДЖМЕНТ & ДЕЛЕГИРОВАНИЕ
    # =========================================================================
    if u_coll_clean == 'mngmnt' or any(k in text for k in [
        'делегирован', 'зарков', 'дашкиев', 'петроченков', 'генштаб наполеона', 
        'управленческих компетенций', 'муда', 'найм', 'регламент', 'отчет руководителю'
    ]):
        return ('business', 'Менеджмент & Процессы', 'Делегирование, Регламенты & Отчетность')

    # =========================================================================
    # 3. ФИНАНСЫ, УЧЕТ, НАЛОГИ & EXCEL
    # =========================================================================
    if any(k in text for k in [
        'p&l', 'ддс', 'юнит-экономика', '115-фз', 'налоги', 'налог ', 'амортизационн', 
        'инвентаризаци', 'себестоимост', 'кассовый разрыв', 'баланс'
    ]) or (u_coll_clean in ['рабочее', 'bsnss_instruments'] and any(k in text for k in ['excel', 'таблиц', 'формул'])):
        if any(k in text for k in ['налог', '115-фз', 'банк', 'личный фонд', 'ооо', 'ао']):
            return ('business', 'Финансы & Управленческий учет', 'Налоги, 115-ФЗ & Безопасность счетов')
        if any(k in text for k in ['excel', 'таблиц', 'формул', 'shortcut']):
            return ('business', 'Финансы & Управленческий учет', 'Автоматизация в Excel & Google Sheets')
        return ('business', 'Финансы & Управленческий учет', 'Управленческий учет (P&L, ДДС & Юнит-экономика)')

    # =========================================================================
    # 4. ТОВАРКА, ВЭД & КИТАЙ
    # =========================================================================
    if u_coll_clean == 'wrk' or any(k in text for k in [
        '1688', 'китай', 'карго', 'пошив футбол', 'hajtex', 'текстильн', 'байер', 
        'фабрик', 'узбекистан', 'доставка из китая', 'упаковка хрупкого'
    ]):
        return ('business', 'Товарный бизнес, ВЭД & Производство', 'Закупки 1688, Фабрики & Карго')

    # =========================================================================
    # 5. ВАЙБ-КОДИНГ & AI-РАЗРАБОТКА
    # =========================================================================
    if u_coll_clean == 'coding ai' or any(k in text for k in [
        'claude code', 'cursor', 'вайб-кодинг', 'vibecoding', 'v0', 'spec builder', 
        'rapid spec', 'superpowers', 'mcp', 'windsurf', 'коннектор'
    ]):
        if any(k in text for k in ['скилл', 'mcp', 'superpowers', 'коннектор', 'плагин']):
            return ('ai', 'Вайб-кодинг & Разработка', 'Скиллы, MCP & Коннекторы')
        if any(k in text for k in ['cursor', 'v0', 'spec builder', 'редактор', 'ide', 'тз', 'архитектур']):
            return ('ai', 'Вайб-кодинг & Разработка', 'AI-редакторы & IDE (Cursor, v0, Spec Builder)')
        return ('ai', 'Вайб-кодинг & Разработка', 'Терминальные агенты & CLI (Claude Code)')

    # =========================================================================
    # 6. AI-АГЕНТЫ & АВТОМАТИЗАЦИЯ
    # =========================================================================
    if u_coll_clean == 'ai guides' or any(k in text for k in [
        'n8n', 'make', 'агент', 'agent', 'model selector', 'мультиагент'
    ]) or 'n8n' in tls_str or 'make' in tls_str:
        if 'n8n' in text or 'make' in text:
            return ('ai', 'Автоматизация & AI-Агенты', 'Сценарии n8n & No-code интеграции')
        return ('ai', 'Автоматизация & AI-Агенты', 'Автономные AI-Агенты & Мультиагенты')

    # =========================================================================
    # 7. КРЕАТИВНЫЙ AI & МЕДИА
    # =========================================================================
    if any(t in ['Midjourney', 'Kling', 'Runway', 'Luma', 'Flux', 'ElevenLabs', 'Wan 2.1'] for t in tools) or \
       any(k in text for k in [
           'kling', 'runway', 'luma', 'wan 2.1', 'flux', 'midjourney', 'генерация видео', 
           'видео нейросет', 'elevenlabs', 'голос', 'озвучк', 'клонирован', 'синтез речи'
       ]):
        if any(k in text for k in ['видео', 'video', 'kling', 'runway', 'luma', 'wan', 'монтаж']):
            return ('ai', 'Креативный AI & Медиа', 'Видео-генерация & Монтаж')
        if any(k in text for k in ['голос', 'озвучк', 'elevenlabs', 'речь']):
            return ('ai', 'Креативный AI & Медиа', 'Синтез речи & Голос')
        return ('ai', 'Креативный AI & Медиа', 'Генерация изображений & Графика')

    # =========================================================================
    # 8. ЯЗЫКОВЫЕ МОДЕЛИ & ПРОМПТЫ
    # =========================================================================
    if u_coll_clean == 'prompts ai' or any(k in text for k in [
        'промпт', 'промт', 'prompt', 'chatgpt', 'gpt', 'deepseek', 'gemini', 'perplexity', 'claude.md'
    ]):
        if any(k in text for k in ['контекст', 'настройка', 'claude.md', 'инструкци', 'память']):
            return ('ai', 'Языковые модели & Промпты', 'Настройка контекста & Проектные файлы (CLAUDE.md)')
        if any(k in text for k in ['промпт', 'промт', 'prompt', 'шаблон', 'фреймворк']):
            return ('ai', 'Языковые модели & Промпты', 'Промпт-инжиниринг & Шаблоны')
        return ('ai', 'Языковые модели & Промпты', 'Флагманские LLM (Claude, ChatGPT, Gemini, DeepSeek)')

    # =========================================================================
    # 9. REELS, КОНТЕНТ & ВОРОНКИ
    # =========================================================================
    if any(k in text for k in [
        'reels', 'рилс', 'воронка', 'воронки', 'chatplace', 'direct', 'директ', 'контент-завод', 'охват'
    ]):
        if any(k in text for k in ['воронка', 'воронки', 'chatplace', 'директ', 'автоворонка']):
            return ('marketing', 'Контент & Reels', 'Автоворонки в Direct & Чат-боты')
        if any(k in text for k in ['контент-завод', 'смысл', 'съемк']):
            return ('marketing', 'Контент & Reels', 'Контент-завод & Сценарии')
        return ('marketing', 'Контент & Reels', 'Алгоритмы & Охваты в Reels')

    # =========================================================================
    # 10. ТРАФИК, РЕКЛАМА & B2B-ЛИДГЕН
    # =========================================================================
    if u_coll_clean == 'mrktng' or any(k in text for k in [
        'директ', 'яндекс директ', 'авито', 'seo', 'поисков', 'b2b', 'лид', 'лидогенераци', 
        'клиент', 'лпр', 'продаж', 'скрипт', 'leadgen'
    ]):
        if any(k in text for k in ['b2b', 'лпр', 'клиент', 'продаж', 'скрипт', 'переписк', 'leadgen']):
            return ('marketing', 'B2B-Продажи & Лидогенерация', 'Поиск контактов ЛПР & Скрипты')
        return ('marketing', 'Трафик & Платная реклама', 'Яндекс.Директ, SEO, Авито & GEO')

    # =========================================================================
    # 11. БИЗНЕС-МОДЕЛИ & СВЯЗКИ
    # =========================================================================
    if u_coll_clean in ['temki', 'ideas', 'bssnss', 'crypto'] or any(k in text for k in [
        'бизнес', 'стартап', 'идея', 'тендер', 'p2p', 'платеж', 'аренд', 'вендинг', 'госзаказ', 'whitebird'
    ]):
        if any(k in text for k in ['тендер', 'госзаказ', 'торгов']):
            return ('business', 'Бизнес-модели & Схемы заработка', 'Госзакупки & Электронные тендеры')
        if any(k in text for k in ['p2p', 'платеж', 'карт', 'крипт', 'whitebird', 'sbp']):
            return ('business', 'Бизнес-модели & Схемы заработка', 'Финтех, P2P & Прием платежей')
        return ('business', 'Бизнес-модели & Схемы заработка', 'Кейсы ниш & Проверенные связки')

    # =========================================================================
    # 12. ДИЗАЙН & WEB
    # =========================================================================
    if any(k in text for k in ['figma', 'дизайн', 'webgpu', '3d', 'лендинг', 'tilda']) or u_coll_clean == 'dsgn_sklls':
        return ('useful', 'Дизайн, UI/UX & Web', 'Figma, WebGPU & Продающие лендинги')

    # =========================================================================
    # 13. ПРИКЛАДНЫЕ AI ИНСТРУМЕНТЫ (for remaining AI collections)
    # =========================================================================
    if u_coll_clean in ['ai instruments', 'ai']:
        if any(k in text for k in ['поиск', 'исследован', 'felo', 'scispace', 'genspark', 'ресерч']):
            return ('ai', 'Прикладные AI-инструменты', 'Ресерч, Поиск & Анализ данных')
        if any(k in text for k in ['презентаци', 'gamma', 'pdf', 'документ', 'chatpdf', 'notebooklm']):
            return ('ai', 'Прикладные AI-инструменты', 'Презентации & Документы')
        if any(k in text for k in ['встреч', 'заметк', 'транскриб', 'granola', 'plaud']):
            return ('ai', 'Прикладные AI-инструменты', 'Ассистенты встреч & Заметки')
        if any(k in text for k in ['апскейл', 'улучш', 'фон', 'upscale', 'krea', 'magnific']):
            return ('ai', 'Прикладные AI-инструменты', 'Обработка изображений & Апскейл')
        if any(k in text for k in ['сайт', 'landing', 'лендинг', 'lovable', 'bolt', 'relume']):
            return ('ai', 'Прикладные AI-инструменты', 'No-code генераторы сайтов')
        return ('ai', 'Прикладные AI-инструменты', 'Универсальные AI-утилиты под задачи')

    # =========================================================================
    # 14. ПОЛЕЗНЫЙ СОФТ / FALLBACK
    # =========================================================================
    return ('useful', 'IT, Безопасность & Утилиты', 'VPN, OSINT & Веб-сервисы')

def update_database_taxonomy():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Add columns if not present
    cur.execute("PRAGMA table_info(posts)")
    cols = [r[1] for r in cur.fetchall()]

    new_cols = [
        ('level1_hub', 'TEXT'),
        ('level1_hub_title', 'TEXT'),
        ('level2_category', 'TEXT'),
        ('level3_subcategory', 'TEXT')
    ]
    for col_name, col_type in new_cols:
        if col_name not in cols:
            print(f"Adding column {col_name} ({col_type})...")
            cur.execute(f"ALTER TABLE posts ADD COLUMN {col_name} {col_type}")

    conn.commit()

    # Fetch all posts
    cur.execute('SELECT id, user_collection, card_title, tools_mentioned, tags, caption, core_idea, key_insight FROM posts ORDER BY id ASC')
    rows = cur.fetchall()
    print(f"Loaded {len(rows)} posts from database.")

    stats = {}
    for r in rows:
        pid, u_coll, title, tools_str, tags_str, cap, idea, ins = r
        tls = json.loads(tools_str) if tools_str else []
        tags = json.loads(tags_str) if tags_str else []

        h_id, cat, subcat = classify_post(pid, u_coll, title, tls, tags, cap, idea, ins)
        h_title = HUB_TITLES.get(h_id, 'Каталог')

        cur.execute('''
            UPDATE posts 
            SET level1_hub = ?, level1_hub_title = ?, level2_category = ?, level3_subcategory = ?,
                hub_name = ?, category_main = ?
            WHERE id = ?
        ''', (h_id, h_title, cat, subcat, h_id, cat, pid))

        stats.setdefault(h_title, {}).setdefault(cat, {}).setdefault(subcat, 0)
        stats[h_title][cat][subcat] += 1

    conn.commit()
    print("All posts classified and updated in DB!")

    # Rebuild FTS
    print("Rebuilding posts_fts index with new categories...")
    cur.execute('DROP TABLE IF EXISTS posts_fts')
    cur.execute('''
        CREATE VIRTUAL TABLE posts_fts USING fts5(
            id UNINDEXED,
            caption,
            summary,
            author_username,
            author_name,
            card_title,
            core_idea,
            key_insight,
            user_collection,
            level1_hub,
            level2_category,
            level3_subcategory,
            tools_mentioned
        )
    ''')
    cur.execute('''
        INSERT INTO posts_fts (
            id, caption, summary, author_username, author_name, card_title, core_idea, 
            key_insight, user_collection, level1_hub, level2_category, level3_subcategory, tools_mentioned
        )
        SELECT id, caption, summary, author_username, author_name, card_title, core_idea, 
               key_insight, user_collection, level1_hub, level2_category, level3_subcategory, tools_mentioned
        FROM posts
    ''')
    conn.commit()
    print("FTS index rebuilt successfully.")

    # Export to posts.json and data.js
    cur.execute('''
        SELECT id, url, author_username, author_name, date, user_collection, 
               level1_hub, level1_hub_title, level2_category, level3_subcategory,
               tools_mentioned, card_title, core_idea, action_steps, key_insight, tags
        FROM posts
        ORDER BY id ASC
    ''')
    all_rows = cur.fetchall()

    export_list = []
    for r in all_rows:
        pid, url, auth_u, auth_n, dt, u_coll, h_id, h_title, cat, subcat, tools_str, title, idea, steps_json, ins, tags_json = r
        tls = json.loads(tools_str) if tools_str else []
        steps = json.loads(steps_json) if steps_json else []
        tags = json.loads(tags_json) if tags_json else []

        export_list.append({
            "id": pid,
            "url": url,
            "author_username": auth_u,
            "author_name": auth_n,
            "date": dt[:10] if dt else '',
            "user_collection": (u_coll or '').strip(),
            "level1_hub": h_id,
            "level1_hub_title": h_title,
            "level2_category": cat,
            "level3_subcategory": subcat,
            "tools": tls,
            "card_title": title,
            "core_idea": idea,
            "action_steps": steps,
            "key_insight": ins,
            "tags": tags
        })

    with open(POSTS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(export_list, f, ensure_ascii=False, indent=2)

    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write('// Auto-generated hierarchical dataset for Telegram Mini App\n')
        f.write('window.POSTS_DATA = ')
        json.dump(export_list, f, ensure_ascii=False)
        f.write(';\n')

    conn.close()

    print("\n=== ONTOLOGY STATS ===")
    for h_title, cats in stats.items():
        total_h = sum(sum(sub.values()) for sub in cats.values())
        print(f"\n{h_title} (Всего: {total_h}):")
        for cat_name, subcats in sorted(cats.items()):
            total_cat = sum(subcats.values())
            print(f"  📁 {cat_name} ({total_cat}):")
            for sub_name, cnt in sorted(subcats.items(), key=lambda x: -x[1]):
                print(f"     🏷 {sub_name}: {cnt}")

    print(f"\n Exported {len(export_list)} records to {POSTS_JSON_PATH} and {DATA_JS_PATH}!")

if __name__ == '__main__':
    update_database_taxonomy()
