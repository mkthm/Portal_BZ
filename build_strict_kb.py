import json
import sqlite3
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_JSON = os.path.join(os.path.dirname(BASE_DIR), 'instagram_saved', 'instagram_saved_posts_clean.json')
COLL_JSON = os.path.join(os.path.dirname(BASE_DIR), 'instagram_saved', 'saved_collections.json')
DB_PATH = os.path.join(BASE_DIR, 'knowledge_base.db')
POSTS_JSON_PATH = os.path.join(BASE_DIR, 'web_app', 'posts.json')

# Strict mapping of user's own collections to category hubs
COLLECTION_HUBS = {
    # 🤖 1. AI и Нейросети
    'AI Instruments ': {'hub': 'ai', 'name': 'AI: Инструменты', 'icon': '🤖'},
    'AI': {'hub': 'ai', 'name': 'AI: Общее', 'icon': '⚡'},
    'Prompts ai': {'hub': 'ai', 'name': 'AI: Промпты', 'icon': '📝'},
    'AI guides': {'hub': 'ai', 'name': 'AI: Гайды', 'icon': '📚'},
    'coding ai': {'hub': 'ai', 'name': 'AI: Кодинг', 'icon': '💻'},
    'Voice': {'hub': 'ai', 'name': 'AI: Голос и Звук', 'icon': '🎙'},

    # 📈 2. Маркетинг и Reels
    'Mrktng': {'hub': 'marketing', 'name': 'Маркетинг: Стратегии и Reels', 'icon': '📱'},
    'Adds': {'hub': 'marketing', 'name': 'Маркетинг: Реклама и Трафик', 'icon': '📢'},
    'MPlaces': {'hub': 'marketing', 'name': 'Маркетинг: Маркетплейсы и AI', 'icon': '🛒'},
    'Mrktplcs': {'hub': 'marketing', 'name': 'Маркетинг: E-commerce', 'icon': '📦'},

    # 🛠 3. Бизнес, Инструменты и Схемы
    'bsnss_instruments': {'hub': 'business', 'name': 'Бизнес: Инструменты и Софт', 'icon': '🛠'},
    'Temki': {'hub': 'business', 'name': 'Бизнес: Сервисы и Схемы', 'icon': '💡'},
    'Ideas': {'hub': 'business', 'name': 'Бизнес: Идеи и Проекты', 'icon': '✨'},
    'Рабочее': {'hub': 'business', 'name': 'Бизнес: Рабочие процессы', 'icon': '💼'},
    'Mngmnt': {'hub': 'business', 'name': 'Бизнес: Менеджмент', 'icon': '📊'},
    'Bssnss': {'hub': 'business', 'name': 'Бизнес: Управление', 'icon': '🏢'},
    'Tech': {'hub': 'business', 'name': 'Технологии: IT и Сервисы', 'icon': '💻'},
    'dsgn_sklls': {'hub': 'business', 'name': 'Дизайн: Навыки и Графика', 'icon': '🎨'},
    'apps': {'hub': 'business', 'name': 'Инструменты: Приложения', 'icon': '📱'},
    'sklls': {'hub': 'business', 'name': 'Навыки: Продуктивность', 'icon': '🎯'},
    'Wrk': {'hub': 'business', 'name': 'Бизнес: Работа', 'icon': '⚙️'},
    'Technlgs': {'hub': 'business', 'name': 'Технологии: Инновации', 'icon': '🚀'},
    'Lfhcks': {'hub': 'business', 'name': 'Лайфхаки: Полезное', 'icon': '🔑'},
    'crypto': {'hub': 'business', 'name': 'Технологии: Web3 и Крипта', 'icon': '🪙'},

    # 💡 4. Смежное
    'Полезное': {'hub': 'useful', 'name': 'Смежное: IT, Софт и Налоги', 'icon': '📌'}
}

JUNK_REGEXES = [
    re.compile(r'(любое\s+использование|копирование|распространение|допускается\s+только|согласия|правообладатель|авторский\s+контент|все\s+права\s+защищены)', re.I),
    re.compile(r'(пиши|напиши|пишите|напишите|отправь|скинь|пришли).*(в\s+(коммент|директ|лс)|отправлю|вышлю|пришлю|инструкци|гайд|ссылк|чек-лист)', re.I),
    re.compile(r'(сохрани|сохраняй|сохраните|сохраняйте)(\s+чтобы|\s+полезно|\s+себе|\s*[\!\,])?', re.I),
    re.compile(r'(подпишись|подписывайся|в\s+профиле|у\s+меня\s+в\s+профиле|еще\s+больше\s+в\s+профиле|переходи\s+в\s+профиль)', re.I),
    re.compile(r'(ссылка\s+в\s+шапке|в\s+шапке\s+профиля|по\s+ссылке\s+в\s+шапке|по\s+ссылке\s+в\s+описании|в\s+описании\s+профиля)', re.I),
    re.compile(r'(разверните|читай(те)?\s+описание|смотри(те)?\s+до\s+конца|жми|лайк|репост|отправь\s+другу)', re.I),
    re.compile(r'(comment\s+.*(send|link|dm)|save\s+this|link\s+in\s+bio|follow\s+for\s+more)', re.I),
    re.compile(r'^(goweb|it\s+курсы|чирчик|школа\s+программирования).*', re.I),
    re.compile(r'^команды\s+вставляй\s+прямо\s+в.*', re.I),
    re.compile(r'^@\w+\s*$', re.I),
    re.compile(r'^#\w+.*', re.I)
]

TRAILING_CLEAN = re.compile(r'[\s\.\,\:\;👇👇🏼👉👀💥🔥✨]+$')

STEP_PATTERN = re.compile(
    r'^((\d+[\.\)\:\-]|[\u0030-\u0039][\uFE0F]?[\u20E3]|[\u2022\u25aa\u25cf\-\*🔹🔸✅✔︎►▪▫])|'
    r'(шаг|пункт|инструмент|модель|сервис|скилл|правило|этап|способ|совет|лайфхак)\s*\d*|'
    r'\/(plugin|marketplace|reload|install|add)[a-z0-9_\-\@\.\/]*|'
    r'(npm|pip|git|curl|docker|python)\s+)',
    re.I
)

TAG_KEYWORDS = {
    'claude-code': re.compile(r'(claude\s+code)', re.I),
    'mcp': re.compile(r'\b(mcp|model\s+context\s+protocol)\b', re.I),
    'n8n': re.compile(r'\b(n8n)\b', re.I),
    'make': re.compile(r'\b(make|integromat)\b', re.I),
    'prompts': re.compile(r'(промпт|prompt)', re.I),
    'chatgpt': re.compile(r'(chatgpt|gpt-4|gpt-4o)', re.I),
    'claude': re.compile(r'\b(claude|anthropic)\b', re.I),
    'cursor': re.compile(r'\b(cursor)\b', re.I),
    'video-ai': re.compile(r'(kling|runway|sora|wan|luma|cogvideo|pika|генерация\s+видео)', re.I),
    'image-ai': re.compile(r'(midjourney|flux|stable\s+diffusion|dall-e)', re.I),
    'voice-ai': re.compile(r'(elevenlabs|suno|udio|озвучк|голос)', re.I),
    'agents': re.compile(r'(ии-агент|ai\s+agent|автономн|crewai|autogen)', re.I),
    'funnels': re.compile(r'(воронк|автоворонк|лид-магнит|лидген)', re.I),
    'reels-growth': re.compile(r'(reels|рилс|удержани|просмотр|охват|вирусн)', re.I),
    'sales': re.compile(r'(продаж|оффер|клиент|запуск|триггер)', re.I),
    'tools': re.compile(r'(сервис|инструмент|софт|приложен|расширени)', re.I),
}

KNOWN_TOOLS = [
    'Claude Code', 'Claude', 'n8n', 'Make', 'ChatGPT', 'GPT-4', 'Midjourney', 'Flux',
    'Runway', 'Kling', 'Luma', 'Sora', 'Wan 2.1', 'Pika', 'ElevenLabs', 'Suno', 'Udio',
    'Cursor', 'v0', 'Bolt', 'GitHub', 'Notion', 'Airtable', 'CapCut', 'Canva', 'Telegram',
    'DeepSeek', 'Perplexity', 'Gemini', 'Stable Diffusion', 'ComfyUI', 'HeyGen', 'D-ID',
    'ManyChat', 'FireCrawl', 'Obsidian', 'ChatPlace'
]

def fix_text(val):
    if not isinstance(val, str):
        return val
    try:
        return val.encode('latin1').decode('utf-8')
    except:
        return val

def is_junk_line(line):
    line = line.strip()
    if not line or len(line) < 3:
        return True
    for rgx in JUNK_REGEXES:
        if rgx.search(line):
            return True
    return False

def clean_text_line(line):
    line = re.sub(r'[\t\r]+', ' ', line)
    line = re.sub(r'\s{2,}', ' ', line)
    return line.strip()

def extract_clean_card(caption, tools_list, category, author_name):
    caption = caption.strip() if caption else ""
    raw_lines = [clean_text_line(l) for l in caption.split('\n')]
    valid_lines = [l for l in raw_lines if not is_junk_line(l)]

    # 1. Title
    title = ""
    start_idx = 0
    for idx, l in enumerate(valid_lines[:3]):
        cleaned = TRAILING_CLEAN.sub('', l).strip()
        if len(cleaned) >= 8 and not re.search(r'^(чистый|разверни|смотри)', cleaned, re.I):
            title = cleaned
            start_idx = idx + 1
            break

    if not title:
        if valid_lines:
            title = TRAILING_CLEAN.sub('', valid_lines[0]).strip()
            start_idx = 1
        else:
            tools_str = f" ({', '.join(tools_list)})" if tools_list else ""
            title = f"Практическое решение по теме {category}{tools_str}"
            start_idx = 0

    if len(title) > 115:
        title = title[:112].rstrip() + "..."

    # 2. Steps & Body
    steps = []
    body_lines = []

    for l in valid_lines[start_idx:]:
        l_clean = TRAILING_CLEAN.sub('', l).strip()
        if not l_clean or is_junk_line(l_clean):
            continue
        if STEP_PATTERN.search(l_clean) or l_clean.startswith('/') or l_clean.startswith('http'):
            steps.append(l_clean)
        else:
            if not steps:
                body_lines.append(l_clean)
            else:
                if len(l_clean) > 30 and not is_junk_line(l_clean):
                    steps.append(l_clean)

    # 3. Core Idea
    if body_lines:
        core_idea = " ".join(body_lines[:3])
    elif steps:
        core_idea = f"Пошаговый разбор и практическая инструкция: {title}."
    else:
        core_idea = f"Прикладной обзор решения и готовая инструкция по теме {category}."

    core_idea = TRAILING_CLEAN.sub('', core_idea).strip()
    if len(core_idea) > 350:
        core_idea = core_idea[:347].rstrip() + "..."

    # 4. Steps
    clean_steps = []
    for s in steps[:7]:
        s = TRAILING_CLEAN.sub('', s).strip()
        if s and not is_junk_line(s):
            if len(s) > 260:
                s = s[:257].rstrip() + "..."
            clean_steps.append(s)

    if not clean_steps:
        clean_steps = [
            "Изучите продемонстрированный алгоритм в оригинальном видео.",
            "Адаптируйте ключевые принципы и инструменты под свой проект."
        ]

    # 5. Insight
    tools_str = ', '.join(tools_list)
    if tools_list:
        insight = f"Связка на базе {tools_str}. Позволяет автоматизировать рутину и масштабировать результат."
    elif "AI" in category:
        insight = "Использование проверенных нейросетей экономит часы ручной работы и повышает качество контента."
    elif "Маркетинг" in category:
        insight = "Ключ к конверсии — мгновенный переход от вовлекающего контента к ценному материалу без барьеров."
    else:
        insight = "Готовое прикладное решение для ускорения рабочих и маркетинговых процессов."

    # 6. Tags
    text_for_tags = f"{title} {core_idea} {' '.join(clean_steps)} {category}"
    tags = []
    for tag_name, pat in TAG_KEYWORDS.items():
        if pat.search(text_for_tags):
            tags.append(tag_name)
    if not tags:
        tags.append('tools')

    return {
        "title": title,
        "core_idea": core_idea,
        "action_steps": clean_steps,
        "key_insight": insight,
        "tags": tags
    }

def rebuild_database():
    print("Reading user collections from saved_collections.json...")
    with open(COLL_JSON, 'r', encoding='utf-8') as f:
        coll_data = json.load(f)

    # Map URLs to target user collections
    url_to_coll = {}
    for c in coll_data:
        coll_name = ''
        for lv in c.get('label_values', []):
            if fix_text(lv.get('label')) == 'Имя':
                coll_name = fix_text(lv.get('value', ''))
                break
        
        if coll_name in COLLECTION_HUBS:
            for lv in c.get('label_values', []):
                if fix_text(lv.get('title')) == 'Медиафайлы':
                    for itm in lv.get('dict', []):
                        for f_entry in itm.get('dict', []):
                            if f_entry.get('label') == 'URL' and f_entry.get('value'):
                                u = f_entry.get('value')
                                url_to_coll.setdefault(u, []).append(coll_name)

    print(f"Total target URLs found across user collections: {len(url_to_coll)}")

    # Read original cleaned posts
    with open(SAVED_JSON, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    # Filter posts strictly to target URLs
    target_posts = []
    for p in posts:
        u = p.get('url', '')
        if u in url_to_coll:
            # Assign user's primary target collection
            colls = url_to_coll[u]
            primary_coll = colls[0]
            
            # Special check for 'Полезное': only keep if relevant
            if primary_coll == 'Полезное' and len(colls) == 1:
                cap = p.get('caption', '')
                if not re.search(r'(ai|нейро|сервис|сайт|бизнес|маркетинг|бот|код|налог|vpn|софт|app|it|инструмент)', cap, re.I):
                    continue

            p['user_collection'] = primary_coll
            p['user_collections_all'] = colls
            p['hub_info'] = COLLECTION_HUBS[primary_coll]
            target_posts.append(p)

    print(f"Total verified posts strictly in target collections: {len(target_posts)}")

    # Recreate database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            author_username TEXT,
            author_name TEXT,
            author_url TEXT,
            date TEXT,
            caption TEXT,
            summary TEXT,
            hashtags TEXT,
            collections TEXT,
            user_collection TEXT,
            category_main TEXT,
            hub_name TEXT,
            tools_mentioned TEXT,
            card_title TEXT,
            core_idea TEXT,
            action_steps TEXT,
            key_insight TEXT,
            tags TEXT
        )
    ''')

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
            category_main,
            tools_mentioned
        )
    ''')

    cur.execute('''
        CREATE TABLE tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            mention_count INTEGER,
            post_ids TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE favorites (
            user_id INTEGER,
            post_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, post_id)
        )
    ''')

    records = []
    tool_to_posts = {}
    posts_for_json = []

    for p in target_posts:
        caption = p.get('caption', '')
        user_coll = p['user_collection']
        hub_info = p['hub_info']
        cat_name = hub_info['name']
        hub_name = hub_info['hub']

        # Scan tools
        full_text = f"{caption} {' '.join(p.get('hashtags', []))}"
        tools_found = []
        for t in KNOWN_TOOLS:
            if re.search(r'\b' + re.escape(t) + r'\b', full_text, re.I):
                tools_found.append(t)

        card = extract_clean_card(caption, tools_found, cat_name, p.get('author_username', ''))

        records.append((
            p.get('url', ''),
            p.get('author_username', ''),
            p.get('author_name', ''),
            p.get('author_url', ''),
            p.get('date', ''),
            caption,
            card['core_idea'],
            ', '.join(p.get('hashtags', [])),
            ', '.join(p.get('user_collections_all', [])),
            user_coll,
            cat_name,
            hub_name,
            json.dumps(tools_found, ensure_ascii=False),
            card['title'],
            card['core_idea'],
            json.dumps(card['action_steps'], ensure_ascii=False),
            card['key_insight'],
            json.dumps(card['tags'], ensure_ascii=False)
        ))

    cur.executemany('''
        INSERT INTO posts (
            url, author_username, author_name, author_url, date, caption, summary,
            hashtags, collections, user_collection, category_main, hub_name,
            tools_mentioned, card_title, core_idea, action_steps, key_insight, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', records)

    # Insert into FTS & tools
    cur.execute('SELECT id, caption, summary, author_username, author_name, card_title, core_idea, key_insight, user_collection, category_main, tools_mentioned, url, date, action_steps, tags FROM posts')
    rows = cur.fetchall()
    for r in rows:
        pid, capt, summ, auth_u, auth_n, title, idea, ins, u_coll, cat, tools_str, url, dt, steps_json, tags_json = r
        cur.execute('''
            INSERT INTO posts_fts (id, caption, summary, author_username, author_name, card_title, core_idea, key_insight, user_collection, category_main, tools_mentioned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (pid, capt, summ, auth_u, auth_n, title, idea, ins, u_coll, cat, tools_str))

        tls = json.loads(tools_str) if tools_str else []
        for t in tls:
            tool_to_posts.setdefault(t, []).append(pid)

        posts_for_json.append({
            "id": pid,
            "url": url,
            "author_username": auth_u,
            "author_name": auth_n,
            "date": dt[:10] if dt else '',
            "user_collection": u_coll,
            "category_main": cat,
            "tools": tls,
            "card_title": title,
            "core_idea": idea,
            "action_steps": json.loads(steps_json) if steps_json else [],
            "key_insight": ins,
            "tags": json.loads(tags_json) if tags_json else []
        })

    for t_name, p_ids in sorted(tool_to_posts.items(), key=lambda x: -len(x[1])):
        cur.execute('INSERT INTO tools (name, mention_count, post_ids) VALUES (?, ?, ?)',
                    (t_name, len(p_ids), json.dumps(p_ids)))

    conn.commit()
    conn.close()

    # Save to Mini App posts.json
    with open(POSTS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(posts_for_json, f, ensure_ascii=False, indent=2)

    print(f"\n✅ База знаний успешно пересобрана! Всего постов: {len(rows)}")
    print(f"✅ Экспортировано в Mini App: {POSTS_JSON_PATH}")

if __name__ == '__main__':
    rebuild_database()
