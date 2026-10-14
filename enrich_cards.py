import sqlite3
import json
import re
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge_base.db')

STEP_PATTERN = re.compile(
    r'^((\d+[\.\)\:\-]|[\u0030-\u0039][\uFE0F]?[\u20E3]|[\u2022\u25aa\u25cf\-\*🔹🔸✅✔︎👉►▪▫])|'
    r'(шаг|пункт|инструмент|модель|сервис|скилл|правило|этап|способ|совет|лайфхак)\s*\d*|'
    r'\/(plugin|marketplace|reload|install|add)[a-z0-9_\-\@\.\/]*|'
    r'(npm|pip|git|curl|docker|python)\s+)',
    re.I
)

CLEAN_HEADLINE_IGNORE = re.compile(
    r'^(разверните|читай(те)?\s+описание|смотри(те)?\s+до\s+конца|сохраняй(те)?|подпишись|пиши|напиши)\b',
    re.I
)

CTA_IGNORE = re.compile(
    r'(пиши(те)?\s+[«"\'\w]+|в\s+директ|в\s+коммент|ссылка\s+в\s+шапке|сохрани(те)?\s+чтобы|подпишись|подписывайся)',
    re.I
)

def extract_card_components(caption, tools_list, category, author_name):
    caption = caption.strip() if caption else ""
    
    # Fallback for empty or very short posts
    if len(caption) < 40:
        tools_str = f" с использованием {', '.join(tools_list)}" if tools_list else ""
        return {
            "title": f"Материал по теме {category} ({author_name or 'Instagram'})",
            "core_idea": f"Визуальный кейс и практическая демонстрация в категории {category}{tools_str}.",
            "action_steps": [
                "Смотрите оригинальный ролик в Instagram для полного визуального контекста.",
                "Изучите сопутствующие материалы автора профиля."
            ],
            "key_insight": f"Рекомендуется ознакомиться с видео в первоисточнике для наглядного применения {category}."
        }

    lines = [l.strip() for l in caption.split('\n') if l.strip() and not l.strip().startswith('#')]
    
    # 1. Title Extraction
    title = ""
    start_idx = 0
    for idx, line in enumerate(lines[:4]):
        cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', line).strip()
        if CLEAN_HEADLINE_IGNORE.search(cleaned) or len(cleaned) < 5:
            continue
        title = line
        start_idx = idx + 1
        break

    if not title and lines:
        title = lines[0]
        start_idx = 1

    if len(title) > 130:
        title = title[:127].rstrip() + "..."

    # 2. Extract Steps and Body Lines
    remaining_lines = lines[start_idx:]
    steps = []
    body_lines = []

    for line in remaining_lines:
        if CTA_IGNORE.search(line) and len(line) < 120 and not line.startswith('/'):
            continue

        if STEP_PATTERN.search(line):
            steps.append(line)
        else:
            if not steps:
                body_lines.append(line)
            else:
                # If we already have steps, long lines might be explanations or commands
                if line.startswith('/') or line.startswith('http') or len(line) > 30:
                    steps.append(line)

    # 3. Core Idea (В чём суть)
    if body_lines:
        core_idea = " ".join(body_lines[:3])
    else:
        core_idea = title

    if len(core_idea) > 380:
        core_idea = core_idea[:377].rstrip() + "..."

    # 4. Fallback Steps if none detected by regex
    if not steps:
        if len(remaining_lines) >= 2:
            steps = [l for l in remaining_lines[:4] if not CTA_IGNORE.search(l)]
        if not steps:
            steps = [
                "Изучите продемонстрированную механику в исходном Reels.",
                "Примените описанный алгоритм в своем проекте или воронке."
            ]

    # Limit to top 8 concise steps
    clean_steps = []
    for s in steps[:8]:
        if len(s) > 280:
            s = s[:277].rstrip() + "..."
        clean_steps.append(s)

    # 5. Key Insight (Главный инсайт / вывод)
    tools_str = ', '.join(tools_list)
    if tools_list:
        insight = f"Связка базируется на инструментах: {tools_str}. Внедрение автоматизирует ключевые этапы задачи."
    elif "Кодинг" in category or "Разработка" in category:
        insight = "Используйте автоматизацию и готовые плагины для сокращения времени разработки и контроля качества кода."
    elif "Видео" in category or "Анимация" in category:
        insight = "Применяйте открытые и генеративные модели для масштабирования видеоконтента без лишних затрат."
    elif "Воронки" in category or "Продажи" in category:
        insight = "Ключевой фактор конверсии — устранение трения на этапе первого контакта и персонализация оффера."
    elif "Reels" in category or "Контент" in category:
        insight = "Удержание первых 3 секунд и четкая структура сценария определяют попадание ролика в рекомендации."
    elif "Автоматизация" in category:
        insight = "Замена ручных рутинных действий на автономные сценарии освобождает до 80% операционного времени."
    else:
        insight = "Практический подход, готовый к адаптации и внедрению в текущие бизнес-процессы."

    return {
        "title": title,
        "core_idea": core_idea,
        "action_steps": clean_steps,
        "key_insight": insight
    }

def enrich_all():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Ensure columns exist
    cur.execute("PRAGMA table_info(posts)")
    cols = [r[1] for r in cur.fetchall()]
    for col_name in ['card_title', 'core_idea', 'action_steps', 'key_insight']:
        if col_name not in cols:
            cur.execute(f"ALTER TABLE posts ADD COLUMN {col_name} TEXT")

    cur.execute("SELECT id, caption, tools_mentioned, category_main, author_name FROM posts")
    rows = cur.fetchall()
    total = len(rows)
    print(f"Enriching {total} posts with structured card data...")

    updates = []
    for row in rows:
        pid, caption, tools_json, category, author_name = row
        tools = json.loads(tools_json) if tools_json else []
        
        card = extract_card_components(caption, tools, category, author_name)
        
        updates.append((
            card["title"],
            card["core_idea"],
            json.dumps(card["action_steps"], ensure_ascii=False),
            card["key_insight"],
            pid
        ))

    cur.executemany("""
        UPDATE posts
        SET card_title = ?, core_idea = ?, action_steps = ?, key_insight = ?
        WHERE id = ?
    """, updates)

    conn.commit()
    print(f"Successfully enriched {total} posts with cards!")

    # Verify sample
    cur.execute("SELECT id, card_title, core_idea, action_steps, key_insight FROM posts LIMIT 3")
    for r in cur.fetchall():
        print(f"\n[Post #{r[0]}] {r[1]}")
        print(f"  Суть: {r[2][:100]}...")
        steps = json.loads(r[3])
        print(f"  Шагов: {len(steps)} (первый: {steps[0] if steps else 'нет'})")
        print(f"  Инсайт: {r[4]}")

    conn.close()

if __name__ == "__main__":
    enrich_all()
