import os
import sqlite3
import json
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'knowledge_base.db')
BACKUP_PATH = os.path.join(BASE_DIR, 'knowledge_base.db.bak')
POSTS_JSON_PATH = os.path.join(BASE_DIR, 'web_app', 'posts.json')
DATA_JS_PATH = os.path.join(BASE_DIR, 'web_app', 'data.js')

# 1. Collections to drop completely
DROP_COLLECTIONS = [
    'Adds',      # Health supplements, gym, taurine, hair loss, protein
    'Mrktplcs',  # Amazon consumer finds (hair brush, defroster, cabinet hardware)
    'Tech',      # Hardware screwdrivers, LED strips, drones, cars
    'Technlgs',  # Pocket door mechanism
    'sklls',     # Soccer drills
    'Voice',     # Voice coach body tension
    'apps'       # Post 57 - empty teaser reel
]

# 2. Specific off-topic post IDs to drop
DROP_POST_IDS = [
    # Полезное (fitness, construction, art, food storage, kids brain, posture, vitamins)
    91,   # @d_cultus - painting art object
    428,  # @femalequotient - child brain development
    481,  # @thediyhack - grocery food storage
    513,  # @untitled_u.not.h1gh.enuff - grind motivation quote
    518,  # @domgazobeton - gas-concrete house
    520,  # @fabricfuture - apparel fabric
    521,  # @ohhdias - documentary films list
    523,  # @sethcrowell - shoulder joint instability
    526,  # @dr.caleb.burgess - shoulder blade knot
    527,  # @sethcrowell - back pain at 19
    529,  # @timeinvestors - empty copyright video credit
    530,  # @bykov.des - Valcucine kitchen review
    531,  # @bucks - Giannis NBA basketball quote
    532,  # @backpainacademy - back posture exercise
    533,  # @theolefirenko - blood checkups & vitamins

    # Ideas (biology, houses, lighting, fitness, embryos, furniture DIY, insoles)
    128,  # @artem.roshior - empty teaser
    433,  # @involta - biology 3rd state of organisms
    452,  # @zrobim_architects - single-story house
    460,  # @dsgninterior - home LED strip hardware
    462,  # @vladpritulyak - fitness in Almaty
    475,  # @reprobank.ru - embryo & egg freezing
    476,  # @bibik_alex - table vinyl film
    479,  # @biosferalab_aldevi - orthopedic insoles
    480,  # @albert.oaa - empty teaser

    # Рабочее (health scanner, fabric)
    423,  # @aleko.so - Neko health body scan
    517,  # @fabricfuture - fabric Scars

    # Mrktng (parametric wood wall, goldsmith)
    185,  # @alewooddesign - parametric wood art wall
    241,  # @goldschmiede_chbecker - goldsmith jewelry making

    # Temki (empty teasers, clinic, laundry chair, defrost tray)
    26,   # @aleksoulm - empty teaser
    43,   # @alex_agafonov__ - empty clinic teaser
    175,  # @kickstarter - Simone Giertz laundry chair
    197,  # @giftgenius.co - meat defrost tray on Amazon
    265,  # @mikhail_spektor_ - empty teaser with generic placeholder
    387,  # @chillnasty - empty teaser

    # Completely empty caption reels with no content and generic titles
    4, 17, 48, 56, 65, 106, 108, 116, 125, 145, 165, 167, 225, 230, 262, 280, 362, 455
]

def clean_database():
    print(f"Creating backup at {BACKUP_PATH}...")
    shutil.copy2(DB_PATH, BACKUP_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Initial count
    cur.execute('SELECT COUNT(*) FROM posts')
    initial_count = cur.fetchone()[0]
    print(f"Initial total posts: {initial_count}")

    # Delete off-topic collections
    c_placeholders = ','.join('?' * len(DROP_COLLECTIONS))
    cur.execute(f'DELETE FROM posts WHERE user_collection IN ({c_placeholders})', DROP_COLLECTIONS)
    deleted_cols = cur.rowcount
    print(f"Deleted from off-topic collections: {deleted_cols} posts")

    # Delete specific off-topic post IDs
    id_placeholders = ','.join('?' * len(DROP_POST_IDS))
    cur.execute(f'DELETE FROM posts WHERE id IN ({id_placeholders})', DROP_POST_IDS)
    deleted_ids = cur.rowcount
    print(f"Deleted specific off-topic post IDs: {deleted_ids} posts")

    # Clean orphaned favorites
    cur.execute('DELETE FROM favorites WHERE post_id NOT IN (SELECT id FROM posts)')

    # Remaining posts count
    cur.execute('SELECT COUNT(*) FROM posts')
    clean_count = cur.fetchone()[0]
    print(f"Clean remaining posts: {clean_count}")

    # Rebuild FTS5 table
    print("Rebuilding FTS5 table...")
    cur.execute('DELETE FROM posts_fts')
    cur.execute('''
        INSERT INTO posts_fts (id, caption, summary, author_username, author_name, card_title, core_idea, key_insight, user_collection, category_main, tools_mentioned)
        SELECT id, caption, summary, author_username, author_name, card_title, core_idea, key_insight, user_collection, category_main, tools_mentioned
        FROM posts
    ''')

    # Rebuild tools table
    print("Rebuilding tools table...")
    cur.execute('DELETE FROM tools')
    cur.execute('SELECT id, tools_mentioned FROM posts')
    tool_to_posts = {}
    for pid, tools_str in cur.fetchall():
        if not tools_str:
            continue
        try:
            tls = json.loads(tools_str)
            for t in tls:
                tool_to_posts.setdefault(t, []).append(pid)
        except Exception:
            pass

    for t_name, p_ids in sorted(tool_to_posts.items(), key=lambda x: -len(x[1])):
        cur.execute('INSERT INTO tools (name, mention_count, post_ids) VALUES (?, ?, ?)',
                    (t_name, len(p_ids), json.dumps(p_ids)))

    conn.commit()

    # Optimize DB
    print("Vacuuming database...")
    cur.execute('VACUUM')
    conn.commit()

    # Export to JSON and JS
    print("Exporting clean data to web_app/posts.json and web_app/data.js...")
    cur.execute('''
        SELECT id, url, author_username, author_name, date, user_collection, hub_name, 
               category_main, tools_mentioned, card_title, core_idea, action_steps, key_insight, tags
        FROM posts
        ORDER BY id ASC
    ''')
    rows = cur.fetchall()

    posts_for_export = []
    for r in rows:
        pid, url, auth_u, auth_n, dt, u_coll, hub, cat, tools_str, title, idea, steps_json, ins, tags_json = r
        tls = json.loads(tools_str) if tools_str else []
        steps = json.loads(steps_json) if steps_json else []
        tags = json.loads(tags_json) if tags_json else []

        posts_for_export.append({
            "id": pid,
            "url": url,
            "author_username": auth_u,
            "author_name": auth_n,
            "date": dt[:10] if dt else '',
            "user_collection": (u_coll or '').strip(),
            "hub_name": hub or 'business',
            "category_main": cat or '',
            "tools": tls,
            "card_title": title,
            "core_idea": idea,
            "action_steps": steps,
            "key_insight": ins,
            "tags": tags
        })

    with open(POSTS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(posts_for_export, f, ensure_ascii=False, indent=2)

    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write('// Auto-generated clean verified dataset for Telegram Mini App\n')
        f.write('window.POSTS_DATA = ')
        json.dump(posts_for_export, f, ensure_ascii=False)
        f.write(';\n')

    conn.close()

    print(f"\n🎉 База знаний очищена и пересобрана! Всего карточек: {len(posts_for_export)}")
    print(f"• Файл базы: {DB_PATH}")
    print(f"• Экспорт JSON: {POSTS_JSON_PATH}")
    print(f"• Экспорт JS: {DATA_JS_PATH}")

if __name__ == '__main__':
    clean_database()
