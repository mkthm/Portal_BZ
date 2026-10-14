import json
import sqlite3
import os
import re
from datetime import datetime

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_JSON = os.path.join(os.path.dirname(BASE_DIR), 'instagram_saved', 'instagram_saved_posts_clean.json')
DB_PATH = os.path.join(BASE_DIR, 'knowledge_base.db')
MD_PATH = os.path.join(BASE_DIR, 'knowledge_base_summary.md')
TOOLS_JSON = os.path.join(BASE_DIR, 'tools_catalog.json')

TAXONOMY = {
    'AI: Кодинг и Разработка': re.compile(r'(claude code|cursor|github|кодинг|программирован|mcp|скилл|python|javascript|v0|bolt|код|developer)', re.I),
    'AI: Видео и Анимация': re.compile(r'(видео|video|kling|runway|sora|wan|luma|hanyuan|cog|pika|gen-3|генерация видео)', re.I),
    'AI: Изображения и Дизайн': re.compile(r'(midjourney|flux|stable diffusion|dall-e|генерация фото|арт|дизайн|картинк|image|визуал)', re.I),
    'AI: Текст, Промпты и LLM': re.compile(r'(chatgpt|gpt|claude|deepseek|gemini|промпт|prompt|текст|копирайт|llm)', re.I),
    'AI: Голос, Музыка и Звук': re.compile(r'(голос|voice|suno|udio|elevenlabs|озвучк|аудио|музык)', re.I),
    'AI: Автоматизация и Агенты': re.compile(r'(n8n|make|автоматизац|агент|agent|crewai|интеграц|workflow|бот)', re.I),
    'Маркетинг: Reels и Контент': re.compile(r'(reels|рилс|shorts|контент|сценари|охват|вирусн|просмотр|алгоритм)', re.I),
    'Маркетинг: Воронки и Продажи': re.compile(r'(воронк|лид|продаж|директ|direct|триггер|клиент|запуск|оффер)', re.I),
    'Маркетинг: Трафик и Реклама': re.compile(r'(трафик|таргет|реклам|маркетинг|marketing|smm|ads|продвижен)', re.I),
    'Бизнес и Управление': re.compile(r'(бизнес|business|стартап|управлен|менеджмент|команд|делегирован|деньги|финанс)', re.I),
    'Инструменты и Сервисы': re.compile(r'(сервис|сайт|инструмент|приложен|app|tool|расширени|плагин|soft|софт)', re.I),
}

KNOWN_TOOLS = [
    'n8n', 'Make', 'Zapier', 'Claude Code', 'Claude', 'ChatGPT', 'GPT-4', 'Midjourney', 'Flux', 
    'Runway', 'Kling', 'Luma', 'Sora', 'Wan 2.1', 'Pika', 'ElevenLabs', 'Suno', 'Udio', 
    'Cursor', 'v0', 'Bolt', 'GitHub', 'Notion', 'Airtable', 'CapCut', 'Canva', 'Telegram',
    'DeepSeek', 'Perplexity', 'Gemini', 'Stable Diffusion', 'ComfyUI', 'HeyGen', 'D-ID',
    'Krea', 'Magnific', 'Leonardo', 'Gamma', 'Beautiful.ai', 'Submagic',
    'Opus Clip', 'Captions', 'ManyChat', 'TgStat', 'SpyWords', 'TargetHunter'
]

def clean_summary(text, max_len=240):
    if not text:
        return 'Без описания'
    first_lines = [line.strip() for line in text.split('\n') if line.strip() and not line.strip().startswith('#')]
    cleaned = ' '.join(first_lines)
    if len(cleaned) > max_len:
        return cleaned[:max_len].rstrip() + '...'
    return cleaned

def build_kb():
    os.makedirs(BASE_DIR, exist_ok=True)
    
    with open(SAVED_JSON, 'r', encoding='utf-8') as f:
        posts = json.load(f)

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
            category_main TEXT,
            categories TEXT,
            tools_mentioned TEXT
        )
    ''')

    cur.execute('''
        CREATE VIRTUAL TABLE posts_fts USING fts5(
            id UNINDEXED,
            caption,
            summary,
            author_username,
            author_name,
            collections,
            categories,
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

    tool_to_posts = {}
    categorized_count = 0
    records_to_insert = []
    fts_records = []

    for p in posts:
        colls_list = p.get('collections', [])
        colls_str = ', '.join(colls_list)
        caption = p.get('caption', '')
        tags_list = p.get('hashtags', [])
        tags_str = ', '.join(tags_list)
        full_text = f'{colls_str} {caption} {tags_str}'

        # Detect categories
        matched_cats = []
        for cat_name, pat in TAXONOMY.items():
            if pat.search(full_text):
                matched_cats.append(cat_name)

        if not matched_cats:
            # If from specific known collections, default assign
            for c in colls_list:
                if 'AI' in c:
                    matched_cats.append('Инструменты и Сервисы')
                    break
                elif 'Mrktng' in c:
                    matched_cats.append('Маркетинг: Трафик и Реклама')
                    break

        if not matched_cats:
            continue

        categorized_count += 1
        cat_main = matched_cats[0]

        # Detect tools
        tools_found = []
        for t in KNOWN_TOOLS:
            if re.search(r'\b' + re.escape(t) + r'\b', full_text, re.I):
                tools_found.append(t)

        summary = clean_summary(caption)

        records_to_insert.append((
            p.get('url', ''),
            p.get('author_username', ''),
            p.get('author_name', ''),
            p.get('author_url', ''),
            p.get('date', ''),
            caption,
            summary,
            tags_str,
            colls_str,
            cat_main,
            json.dumps(matched_cats, ensure_ascii=False),
            json.dumps(tools_found, ensure_ascii=False)
        ))

    cur.executemany('''
        INSERT INTO posts (
            url, author_username, author_name, author_url, date, caption, summary,
            hashtags, collections, category_main, categories, tools_mentioned
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', records_to_insert)

    # Fetch inserted ids for tools mapping and FTS
    cur.execute('SELECT id, caption, summary, author_username, author_name, collections, categories, tools_mentioned FROM posts')
    rows = cur.fetchall()
    for row in rows:
        pid, capt, summ, auth_u, auth_n, colls, cats, tools = row
        cur.execute('''
            INSERT INTO posts_fts (id, caption, summary, author_username, author_name, collections, categories, tools_mentioned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (pid, capt, summ, auth_u, auth_n, colls, cats, tools))

        tools_list = json.loads(tools)
        for t in tools_list:
            tool_to_posts.setdefault(t, []).append(pid)

    # Insert tools
    for t_name, p_ids in sorted(tool_to_posts.items(), key=lambda x: -len(x[1])):
        cur.execute('INSERT INTO tools (name, mention_count, post_ids) VALUES (?, ?, ?)',
                    (t_name, len(p_ids), json.dumps(p_ids)))

    conn.commit()

    # Generate Markdown Summary
    md_content = ["# 🧠 База знаний для Telegram-бота\n"]
    md_content.append(f"> Собрано из сохраненных постов Instagram: **{categorized_count} публикаций** по нейросетям, маркетингу и инструментам.\n")

    # Categories breakdown
    cur.execute('SELECT category_main, COUNT(*) FROM posts GROUP BY category_main ORDER BY COUNT(*) DESC')
    cat_counts = cur.fetchall()
    
    md_content.append("## 📂 Рубрикатор категорий\n")
    for cat, count in cat_counts:
        md_content.append(f"* **{cat}**: {count} постов")
    md_content.append("\n---\n")

    md_content.append("## 🛠 Каталог упоминаемых инструментов\n")
    for t_name, p_ids in sorted(tool_to_posts.items(), key=lambda x: -len(x[1])):
        md_content.append(f"* **{t_name}** ({len(p_ids)} постов)")
    md_content.append("\n---\n")

    # Sample posts by category
    md_content.append("## 📌 Избранные посты по категориям\n")
    for cat, _ in cat_counts:
        md_content.append(f"### {cat}\n")
        cur.execute('SELECT url, author_username, summary, tools_mentioned FROM posts WHERE category_main = ? ORDER BY id ASC LIMIT 5', (cat,))
        for post_row in cur.fetchall():
            url, auth, summ, tools_str = post_row
            tools = json.loads(tools_str)
            tools_badge = f" `[{', '.join(tools)}]`" if tools else ""
            author_badge = f"@{auth}" if auth else "Instagram"
            md_content.append(f"- **[{author_badge}]({url})**{tools_badge}\n  _{summ}_\n")
        md_content.append("")

    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))

    # Write tools catalog json
    with open(TOOLS_JSON, 'w', encoding='utf-8') as f:
        json.dump(tool_to_posts, f, ensure_ascii=False, indent=2)

    conn.close()
    print(f"Knowledge Base DB created: {DB_PATH}")
    print(f"Total posts categorized: {categorized_count}")
    print(f"Markdown summary saved: {MD_PATH}")

if __name__ == '__main__':
    build_kb()
