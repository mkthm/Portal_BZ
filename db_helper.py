import sqlite3
import json
import os
import uuid
import math

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge_base.db')

HUBS = {
    'ai': {'id': 'ai', 'title': '🤖 AI & Нейросети', 'icon': '🤖'},
    'marketing': {'id': 'marketing', 'title': '📈 Маркетинг & E-com', 'icon': '📈'},
    'business': {'id': 'business', 'title': '🛠 Бизнес & Управление', 'icon': '🛠'},
    'useful': {'id': 'useful', 'title': '📌 Полезный софт & IT', 'icon': '📌'}
}

CATEGORIES = {
    1: {'id': 1, 'hub': 'ai', 'name': 'Вайб-кодинг & Разработка', 'icon': '💻'},
    2: {'id': 2, 'hub': 'ai', 'name': 'Языковые модели & Промпты', 'icon': '🧠'},
    3: {'id': 3, 'hub': 'ai', 'name': 'Автоматизация & AI-Агенты', 'icon': '⚡'},
    4: {'id': 4, 'hub': 'ai', 'name': 'Креативный AI & Медиа', 'icon': '🎨'},
    5: {'id': 5, 'hub': 'ai', 'name': 'Прикладные AI-инструменты', 'icon': '🛠'},
    6: {'id': 6, 'hub': 'marketing', 'name': 'Контент & Reels', 'icon': '📱'},
    7: {'id': 7, 'hub': 'marketing', 'name': 'Маркетплейсы (WB / Ozon)', 'icon': '🛍'},
    8: {'id': 8, 'hub': 'marketing', 'name': 'B2B-Продажи & Лидогенерация', 'icon': '👔'},
    9: {'id': 9, 'hub': 'marketing', 'name': 'Трафик & Платная реклама', 'icon': '🎯'},
    10: {'id': 10, 'hub': 'business', 'name': 'Бизнес-модели & Схемы заработка', 'icon': '💡'},
    11: {'id': 11, 'hub': 'business', 'name': 'Финансы & Управленческий учет', 'icon': '📊'},
    12: {'id': 12, 'hub': 'business', 'name': 'Менеджмент & Процессы', 'icon': '👥'},
    13: {'id': 13, 'hub': 'business', 'name': 'Товарный бизнес, ВЭД & Производство', 'icon': '🚢'},
    14: {'id': 14, 'hub': 'useful', 'name': 'IT, Безопасность & Утилиты', 'icon': '🛡'},
    15: {'id': 15, 'hub': 'useful', 'name': 'Дизайн, UI/UX & Web', 'icon': '🎨'},
    16: {'id': 16, 'hub': 'business', 'name': 'Инструменты, Сервисы & Подрядчики', 'icon': '🧰'}
}

SUBCATEGORIES = {
    1: {'id': 1, 'cat_id': 1, 'name': 'AI-редакторы & IDE (Cursor, v0, Spec Builder)', 'icon': '💻'},
    2: {'id': 2, 'cat_id': 1, 'name': 'Скиллы, MCP & Коннекторы', 'icon': '🔌'},
    3: {'id': 3, 'cat_id': 1, 'name': 'Терминальные агенты & CLI (Claude Code)', 'icon': '🖥'},
    4: {'id': 4, 'cat_id': 2, 'name': 'Настройка контекста & Проектные файлы (CLAUDE.md)', 'icon': '⚙️'},
    5: {'id': 5, 'cat_id': 2, 'name': 'Промпт-инжиниринг & Шаблоны', 'icon': '📝'},
    6: {'id': 6, 'cat_id': 2, 'name': 'Флагманские LLM (Claude, ChatGPT, Gemini, DeepSeek)', 'icon': '🌐'},
    7: {'id': 7, 'cat_id': 3, 'name': 'Автономные AI-Агенты & Мультиагенты', 'icon': '🤖'},
    8: {'id': 8, 'cat_id': 3, 'name': 'Сценарии n8n & No-code интеграции', 'icon': '⚡'},
    9: {'id': 9, 'cat_id': 4, 'name': 'Видео-генерация & Монтаж', 'icon': '🎬'},
    10: {'id': 10, 'cat_id': 4, 'name': 'Генерация изображений & Графика', 'icon': '🎨'},
    11: {'id': 11, 'cat_id': 4, 'name': 'Синтез речи & Голос', 'icon': '🎙'},
    12: {'id': 12, 'cat_id': 5, 'name': 'No-code генераторы сайтов', 'icon': '🌐'},
    13: {'id': 13, 'cat_id': 5, 'name': 'Ассистенты встреч & Заметки', 'icon': '📝'},
    14: {'id': 14, 'cat_id': 5, 'name': 'Обработка изображений & Апскейл', 'icon': '🖼'},
    15: {'id': 15, 'cat_id': 5, 'name': 'Презентации & Документы', 'icon': '📑'},
    16: {'id': 16, 'cat_id': 5, 'name': 'Универсальные AI-утилиты под задачи', 'icon': '🛠'},
    17: {'id': 17, 'cat_id': 6, 'name': 'Автоворонки в Direct & Чат-боты', 'icon': '🔄'},
    18: {'id': 18, 'cat_id': 6, 'name': 'Алгоритмы & Охваты в Reels', 'icon': '📱'},
    19: {'id': 19, 'cat_id': 6, 'name': 'Контент-завод & Сценарии', 'icon': '🏭'},
    20: {'id': 20, 'cat_id': 7, 'name': 'AI-автоматизация селлеров', 'icon': '🤖'},
    21: {'id': 21, 'cat_id': 7, 'name': 'Аналитика ниш & Топ-позиции (MPStats)', 'icon': '📊'},
    22: {'id': 22, 'cat_id': 7, 'name': 'Оптимизация карточек & СПП', 'icon': '🏷'},
    23: {'id': 23, 'cat_id': 7, 'name': 'Фулфилмент, Сборка FBS & Маркировка', 'icon': '📦'},
    24: {'id': 24, 'cat_id': 8, 'name': 'Поиск контактов ЛПР & Скрипты', 'icon': '👔'},
    25: {'id': 25, 'cat_id': 9, 'name': 'Яндекс.Директ, SEO, Авито & GEO', 'icon': '🎯'},
    26: {'id': 26, 'cat_id': 10, 'name': 'Госзакупки & Электронные тендеры', 'icon': '🏛'},
    27: {'id': 27, 'cat_id': 10, 'name': 'Кейсы ниш & Проверенные связки', 'icon': '💡'},
    28: {'id': 28, 'cat_id': 10, 'name': 'Финтех, P2P & Прием платежей', 'icon': '💳'},
    29: {'id': 29, 'cat_id': 11, 'name': 'Автоматизация в Excel & Google Sheets', 'icon': '📑'},
    30: {'id': 30, 'cat_id': 11, 'name': 'Налоги, 115-ФЗ & Безопасность счетов', 'icon': '⚖️'},
    31: {'id': 31, 'cat_id': 11, 'name': 'Управленческий учет (P&L, ДДС & Юнит-экономика)', 'icon': '📊'},
    32: {'id': 32, 'cat_id': 12, 'name': 'Делегирование, Регламенты & Отчетность', 'icon': '📋'},
    33: {'id': 33, 'cat_id': 13, 'name': 'Закупки 1688, Фабрики & Карго', 'icon': '🇨🇳'},
    34: {'id': 34, 'cat_id': 14, 'name': 'VPN, OSINT & Веб-сервисы', 'icon': '🛡'},
    35: {'id': 35, 'cat_id': 15, 'name': 'Figma, WebGPU & Продающие лендинги', 'icon': '🎨'},
    36: {'id': 36, 'cat_id': 16, 'name': 'Платежки, Крипта & Зарубежные карты', 'icon': '💳'},
    37: {'id': 37, 'cat_id': 16, 'name': 'Сервисы, Связь & VPN', 'icon': '⚙️'},
    38: {'id': 38, 'cat_id': 16, 'name': 'Логистика, Карго & Авто', 'icon': '📦'},
    39: {'id': 39, 'cat_id': 16, 'name': 'Услуги, Продвижение & Подрядчики', 'icon': '🤝'}
}

COLUMNS_SELECT = '''
    id, url, author_username, author_name, date, summary, caption, 
    tools_mentioned, category_main, card_title, core_idea, action_steps, key_insight, tags,
    user_collection, hub_name, level1_hub, level1_hub_title, level2_category, level3_subcategory
'''

SEARCH_SESSIONS = {}

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_hub_counts():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT level1_hub, COUNT(*) FROM posts GROUP BY level1_hub')
        return dict(cur.fetchall())

def get_categories_by_hub(hub_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT level2_category, COUNT(*) FROM posts WHERE level1_hub = ? GROUP BY level2_category', (hub_id,))
        counts = dict(cur.fetchall())
        res = []
        for cid, info in CATEGORIES.items():
            if info['hub'] == hub_id:
                cnt = counts.get(info['name'], 0)
                res.append((cid, info['name'], info['icon'], cnt))
        return res

def get_subcategories_by_cat(cat_id):
    cat_info = CATEGORIES.get(cat_id)
    if not cat_info:
        return []
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT level3_subcategory, COUNT(*) FROM posts WHERE level2_category = ? GROUP BY level3_subcategory', (cat_info['name'],))
        counts = dict(cur.fetchall())
        res = []
        for sid, info in SUBCATEGORIES.items():
            if info['cat_id'] == cat_id:
                cnt = counts.get(info['name'], 0)
                res.append((sid, info['name'], info['icon'], cnt))
        return res

# --- Catalog / List Views (5 items per page) ---
def get_subcat_posts_page(sub_id, page=1, per_page=5):
    sub_info = SUBCATEGORIES.get(sub_id)
    if not sub_info:
        return [], 0, 1
    sub_name = sub_info['name']
    offset = (page - 1) * per_page

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT id, card_title, author_username, tools_mentioned, date
            FROM posts
            WHERE level3_subcategory = ?
            ORDER BY id ASC
            LIMIT ? OFFSET ?
        ''', (sub_name, per_page, offset))
        items = cur.fetchall()

        cur.execute('SELECT COUNT(*) FROM posts WHERE level3_subcategory = ?', (sub_name,))
        total = cur.fetchone()[0]
        total_pages = max(1, math.ceil(total / per_page))
        return items, total, total_pages

def get_category_posts_page(cat_id, page=1, per_page=5):
    cat_info = CATEGORIES.get(cat_id)
    if not cat_info:
        return [], 0, 1
    cat_name = cat_info['name']
    offset = (page - 1) * per_page

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT id, card_title, author_username, tools_mentioned, date
            FROM posts
            WHERE level2_category = ?
            ORDER BY id ASC
            LIMIT ? OFFSET ?
        ''', (cat_name, per_page, offset))
        items = cur.fetchall()

        cur.execute('SELECT COUNT(*) FROM posts WHERE level2_category = ?', (cat_name,))
        total = cur.fetchone()[0]
        total_pages = max(1, math.ceil(total / per_page))
        return items, total, total_pages

def get_tool_posts_page(tool_id, page=1, per_page=5):
    offset = (page - 1) * per_page
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT name, post_ids FROM tools WHERE id = ?', (tool_id,))
        row = cur.fetchone()
        if not row:
            return [], 0, 1, ''
        tool_name, p_ids_json = row
        p_ids = json.loads(p_ids_json)
        total = len(p_ids)
        total_pages = max(1, math.ceil(total / per_page))
        
        current_ids = p_ids[offset:offset + per_page]
        if not current_ids:
            return [], total, total_pages, tool_name

        placeholders = ','.join('?' for _ in current_ids)
        cur.execute(f'''
            SELECT id, card_title, author_username, tools_mentioned, date
            FROM posts
            WHERE id IN ({placeholders})
        ''', current_ids)
        return cur.fetchall(), total, total_pages, tool_name

def create_search_session(query):
    sid = uuid.uuid4().hex[:8]
    SEARCH_SESSIONS[sid] = query
    if len(SEARCH_SESSIONS) > 1000:
        SEARCH_SESSIONS.pop(next(iter(SEARCH_SESSIONS)))
    return sid

def get_search_query(sid):
    return SEARCH_SESSIONS.get(sid, '')

def get_search_posts_page(query, page=1, per_page=5):
    offset = (page - 1) * per_page
    clean_q = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in query).strip()
    if not clean_q:
        return [], 0, 1

    words = [w for w in clean_q.split() if len(w) >= 2]
    if not words:
        return [], 0, 1

    fts_query = ' OR '.join(f'"{w}"*' for w in words)
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute('''
                SELECT p.id, p.card_title, p.author_username, p.tools_mentioned, p.date
                FROM posts_fts f
                JOIN posts p ON p.id = f.id
                WHERE posts_fts MATCH ?
                ORDER BY rank
                LIMIT ? OFFSET ?
            ''', (fts_query, per_page, offset))
            items = cur.fetchall()

            cur.execute('SELECT COUNT(*) FROM posts_fts WHERE posts_fts MATCH ?', (fts_query,))
            total = cur.fetchone()[0]
            total_pages = max(1, math.ceil(total / per_page))
            return items, total, total_pages
        except Exception:
            like_q = f'%{clean_q}%'
            cur.execute('''
                SELECT id, card_title, author_username, tools_mentioned, date
                FROM posts
                WHERE caption LIKE ? OR card_title LIKE ? OR tools_mentioned LIKE ?
                LIMIT ? OFFSET ?
            ''', (like_q, like_q, like_q, per_page, offset))
            items = cur.fetchall()
            cur.execute('SELECT COUNT(*) FROM posts WHERE caption LIKE ? OR card_title LIKE ?', (like_q, like_q))
            total = cur.fetchone()[0]
            total_pages = max(1, math.ceil(total / per_page))
            return items, total, total_pages

def get_favorites_page(user_id, page=1, per_page=5):
    offset = (page - 1) * per_page
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT p.id, p.card_title, p.author_username, p.tools_mentioned, p.date
            FROM favorites f
            JOIN posts p ON p.id = f.post_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
            LIMIT ? OFFSET ?
        ''', (user_id, per_page, offset))
        items = cur.fetchall()
        cur.execute('SELECT COUNT(*) FROM favorites WHERE user_id = ?', (user_id,))
        total = cur.fetchone()[0]
        total_pages = max(1, math.ceil(total / per_page))
        return items, total, total_pages

# --- Single Post Fetch ---
def get_post_by_id(post_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f'''
            SELECT {COLUMNS_SELECT}
            FROM posts
            WHERE id = ?
        ''', (post_id,))
        return cur.fetchone()

def get_random_post():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f'''
            SELECT {COLUMNS_SELECT}
            FROM posts
            WHERE caption IS NOT NULL AND length(caption) > 50
            ORDER BY RANDOM()
            LIMIT 1
        ''')
        return cur.fetchone()

def get_tools_list(limit=24):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, name, mention_count FROM tools ORDER BY mention_count DESC LIMIT ?', (limit,))
        return cur.fetchall()

# Favorites management
def toggle_favorite(user_id, post_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM favorites WHERE user_id = ? AND post_id = ?', (user_id, post_id))
        exists = cur.fetchone()
        if exists:
            cur.execute('DELETE FROM favorites WHERE user_id = ? AND post_id = ?', (user_id, post_id))
            conn.commit()
            return False
        else:
            cur.execute('INSERT OR IGNORE INTO favorites (user_id, post_id) VALUES (?, ?)', (user_id, post_id))
            conn.commit()
            return True

def is_favorite(user_id, post_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM favorites WHERE user_id = ? AND post_id = ?', (user_id, post_id))
        return bool(cur.fetchone())
