import sqlite3
import json
import re
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge_base.db')

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

SUBCATEGORY_MAPPING = {
    'AI: Кодинг и Разработка': 'ai-coding',
    'AI: Видео и Анимация': 'ai-video',
    'AI: Изображения и Дизайн': 'ai-visual',
    'AI: Текст, Промпты и LLM': 'ai-prompts',
    'AI: Голос, Музыка и Звук': 'ai-audio',
    'AI: Автоматизация и Агенты': 'ai-automation',
    'Маркетинг: Воронки и Продажи': 'mktg-funnels',
    'Маркетинг: Reels и Контент': 'mktg-reels',
    'Маркетинг: Трафик и Реклама': 'mktg-traffic',
    'Бизнес и Управление': 'biz-management',
    'Инструменты и Сервисы': 'biz-tools'
}

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
    subcat = SUBCATEGORY_MAPPING.get(category, 'general')
    
    # 1. Clean lines
    raw_lines = [clean_text_line(l) for l in caption.split('\n')]
    valid_lines = [l for l in raw_lines if not is_junk_line(l)]

    # 2. Extract Title
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

    # 3. Extract Steps and Body
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

    # 4. Synthesize Core Idea
    if body_lines:
        core_idea = " ".join(body_lines[:3])
    elif steps:
        core_idea = f"Пошаговый разбор и практическая инструкция: {title}."
    else:
        if "Кодинг" in category:
            core_idea = f"Инструкция по настройке и применению инструментов разработки: {title}."
        elif "Видео" in category:
            core_idea = f"Методика и стек сервисов для генерации и оптимизации видео: {title}."
        elif "Воронки" in category:
            core_idea = f"Схема автоворонки для привлечения и конвертации лидов: {title}."
        elif "Reels" in category:
            core_idea = f"Алгоритм создания и удержания внимания в вертикальных видео: {title}."
        else:
            core_idea = f"Прикладной обзор решения и готовая инструкция по теме {category}."

    core_idea = TRAILING_CLEAN.sub('', core_idea).strip()
    if len(core_idea) > 350:
        core_idea = core_idea[:347].rstrip() + "..."

    # 5. Clean Action Steps
    clean_steps = []
    for s in steps[:7]:
        s = TRAILING_CLEAN.sub('', s).strip()
        if s and not is_junk_line(s):
            if len(s) > 260:
                s = s[:257].rstrip() + "..."
            clean_steps.append(s)

    if not clean_steps:
        if "Кодинг" in category:
            clean_steps = [
                "Установите указанные расширения и библиотеки в проект.",
                "Проверьте настройки окружения и выполните тестовый запуск.",
                "Интегрируйте готовый скилл в рабочий процесс разработки."
            ]
        elif "Видео" in category:
            clean_steps = [
                "Подготовьте исходный промпт или референсное изображение.",
                "Настройте параметры движения и качества генерации.",
                "Скомпонуйте полученные сцены в единый ролик."
            ]
        elif "Воронки" in category or "Reels" in category:
            clean_steps = [
                "Сформулируйте цепляющий хук в первые 3 секунды видео.",
                "Настройте автоматический ответ в Direct на ключевое слово.",
                "Направьте трафик на бесплатный лид-магнит с высокой ценностью."
            ]
        else:
            clean_steps = [
                "Изучите продемонстрированный алгоритм в оригинальном видео.",
                "Адаптируйте ключевые принципы под текущие задачи вашего проекта."
            ]

    # 6. Key Insight
    tools_str = ', '.join(tools_list)
    if tools_list:
        insight = f"Связка на базе {tools_str}. Позволяет автоматизировать рутину и масштабировать результат."
    elif "Кодинг" in category or "Разработка" in category:
        insight = "Использование проверенных плагинов и скиллов экономит часы ручного написания и проверки кода."
    elif "Видео" in category:
        insight = "Открытые генеративные модели уже не уступают коммерческим — используйте их для снижения себестоимости контента."
    elif "Воронки" in category or "Продажи" in category:
        insight = "Ключ к конверсии — мгновенный переход от вовлекающего контента к ценному материалу без барьеров."
    elif "Reels" in category:
        insight = "Удержание внимания строится на динамичной смене планов и четкой пользе в первые 3 секунды."
    elif "Автоматизация" in category:
        insight = "Автономные сценарии исключают человеческий фактор и ускоряют обработку данных в разы."
    else:
        insight = "Готовое прикладное решение для ускорения рабочих и маркетинговых процессов."

    # 7. Semantic Tags
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
        "tags": tags,
        "subcategory": subcat
    }

def run_clean_enrichment():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, caption, tools_mentioned, category_main, author_name FROM posts")
    rows = cur.fetchall()
    total = len(rows)
    print(f"Deep cleaning and re-enriching {total} posts...")

    updates = []
    for r in rows:
        pid, caption, tools_json, category, author_name = r
        tools = json.loads(tools_json) if tools_json else []
        
        card = extract_clean_card(caption, tools, category, author_name)
        
        updates.append((
            card["title"],
            card["core_idea"],
            json.dumps(card["action_steps"], ensure_ascii=False),
            card["key_insight"],
            json.dumps(card["tags"], ensure_ascii=False),
            card["subcategory"],
            pid
        ))

    cur.executemany("""
        UPDATE posts
        SET card_title = ?, core_idea = ?, action_steps = ?, key_insight = ?, tags = ?, subcategory_id = ?
        WHERE id = ?
    """, updates)

    conn.commit()
    print(f"Successfully cleaned and updated all {total} posts!")

    # Verify samples
    cur.execute("SELECT id, card_title, core_idea, action_steps, key_insight, tags, subcategory_id FROM posts WHERE id IN (1, 2, 3, 13)")
    for r in cur.fetchall():
        print(f"\n[Post #{r[0]}] {r[1]}")
        print(f"  Суть: {r[2]}")
        steps = json.loads(r[3])
        print(f"  Шагов ({len(steps)}):")
        for s in steps[:2]:
            print(f"    • {s}")
        print(f"  Инсайт: {r[4]}")
        print(f"  Теги: {r[5]}")
        print(f"  Subcat: {r[6]}")

    conn.close()

if __name__ == "__main__":
    run_clean_enrichment()
