import http.server
import socketserver
import json
import sqlite3
import urllib.parse
import os
import sys

PORT = int(os.getenv("PORT", "8080"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "knowledge_base.db")
WEB_APP_DIR = os.path.join(BASE_DIR, "web_app")

def get_db():
    return sqlite3.connect(DB_PATH)

class KnowledgeBaseHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_APP_DIR, **kwargs)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/posts":
            self.handle_api_posts(query)
        elif path == "/api/categories":
            self.handle_api_categories()
        elif path == "/api/tags":
            self.handle_api_tags()
        elif path.startswith("/api/posts/"):
            try:
                pid = int(path.split("/")[-1])
                self.handle_api_post_detail(pid)
            except ValueError:
                self._send_json({"error": "Invalid ID"}, status=400)
        else:
            # Serve static files from web_app directory
            super().do_GET()

    def handle_api_categories(self):
        with get_db() as conn:
            cur = conn.cursor()
            # Hubs counts
            cur.execute("""
                SELECT level1_hub, level1_hub_title, COUNT(*) 
                FROM posts 
                GROUP BY level1_hub, level1_hub_title
                ORDER BY COUNT(*) DESC
            """)
            hubs = [{"id": r[0], "title": r[1], "count": r[2]} for r in cur.fetchall()]

            # Level 2 Categories
            cur.execute("""
                SELECT level1_hub, level2_category, COUNT(*) 
                FROM posts 
                GROUP BY level1_hub, level2_category 
                ORDER BY COUNT(*) DESC
            """)
            categories = [{"hub": r[0], "name": r[1], "count": r[2]} for r in cur.fetchall()]

            # Level 3 Subcategories
            cur.execute("""
                SELECT level2_category, level3_subcategory, COUNT(*) 
                FROM posts 
                GROUP BY level2_category, level3_subcategory 
                ORDER BY COUNT(*) DESC
            """)
            subcategories = [{"category": r[0], "name": r[1], "count": r[2]} for r in cur.fetchall()]

            # Original Instagram collections
            cur.execute("""
                SELECT user_collection, COUNT(*) 
                FROM posts 
                GROUP BY user_collection 
                ORDER BY COUNT(*) DESC
            """)
            collections = [{"collection": (r[0] or "").strip(), "count": r[1]} for r in cur.fetchall()]

            self._send_json({
                "hubs": hubs,
                "categories": categories,
                "subcategories": subcategories,
                "collections": collections
            })

    def handle_api_tags(self):
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT tags FROM posts WHERE tags IS NOT NULL")
            from collections import Counter
            cnt = Counter()
            for r in cur.fetchall():
                try:
                    for t in json.loads(r[0]):
                        cnt[t] += 1
                except:
                    pass
            items = [{"tag": k, "count": v} for k, v in cnt.most_common(20)]
            self._send_json({"tags": items})

    def handle_api_post_detail(self, pid):
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, url, author_username, author_name, date, summary, caption, 
                       tools_mentioned, card_title, core_idea, action_steps, key_insight, tags,
                       user_collection, level1_hub, level1_hub_title, level2_category, level3_subcategory
                FROM posts
                WHERE id = ?
            """, (pid,))
            r = cur.fetchone()
            if not r:
                self._send_json({"error": "Not found"}, status=404)
                return
            post = {
                "id": r[0],
                "url": r[1],
                "author_username": r[2],
                "author_name": r[3],
                "date": r[4],
                "summary": r[5],
                "tools": json.loads(r[7]) if r[7] else [],
                "card_title": r[8],
                "core_idea": r[9],
                "action_steps": json.loads(r[10]) if r[10] else [],
                "key_insight": r[11],
                "tags": json.loads(r[12]) if r[12] else [],
                "user_collection": r[13].strip() if r[13] else "",
                "level1_hub": r[14],
                "level1_hub_title": r[15],
                "level2_category": r[16],
                "level3_subcategory": r[17]
            }
            self._send_json(post)

    def handle_api_posts(self, query):
        page = max(1, int(query.get("page", ["1"])[0]))
        limit = min(50, max(1, int(query.get("limit", ["10"])[0])))
        offset = (page - 1) * limit

        hub = query.get("hub", [""])[0].strip()
        category = query.get("category", [""])[0].strip()
        subcategory = query.get("subcategory", [""])[0].strip()
        collection = query.get("collection", [""])[0].strip()
        tag = query.get("tag", [""])[0].strip()
        q = query.get("q", [""])[0].strip()
        favs_str = query.get("favs", [""])[0].strip()

        conditions = []
        params = []

        if favs_str:
            fav_ids = [int(x) for x in favs_str.split(",") if x.isdigit()]
            if fav_ids:
                placeholders = ",".join("?" for _ in fav_ids)
                conditions.append(f"p.id IN ({placeholders})")
                params.extend(fav_ids)
            else:
                self._send_json({"items": [], "total": 0, "page": page, "limit": limit})
                return

        if hub:
            conditions.append("p.level1_hub = ?")
            params.append(hub)

        if category:
            conditions.append("p.level2_category = ?")
            params.append(category)

        if subcategory:
            conditions.append("p.level3_subcategory = ?")
            params.append(subcategory)

        if collection:
            conditions.append("(p.user_collection = ? OR p.user_collection = ?)")
            params.extend([collection, collection + " "])

        if tag:
            conditions.append("p.tags LIKE ?")
            params.append(f"%\"{tag}\"%")

        with get_db() as conn:
            cur = conn.cursor()

            if q:
                clean_q = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in q).strip()
                words = [w for w in clean_q.split() if len(w) >= 2]
                if words:
                    fts_query = ' OR '.join(f'"{w}"*' for w in words)
                    where_clause = " AND ".join(conditions) if conditions else "1=1"
                    
                    sql = f"""
                        SELECT p.id, p.url, p.author_username, p.author_name, p.date, p.summary, 
                               p.tools_mentioned, p.card_title, p.core_idea, p.action_steps, p.key_insight, p.tags,
                               p.user_collection, p.level1_hub, p.level1_hub_title, p.level2_category, p.level3_subcategory
                        FROM posts_fts f
                        JOIN posts p ON p.id = f.id
                        WHERE posts_fts MATCH ? AND {where_clause}
                        ORDER BY rank
                        LIMIT ? OFFSET ?
                    """
                    sql_params = [fts_query] + params + [limit, offset]
                    cur.execute(sql, sql_params)
                    rows = cur.fetchall()

                    count_sql = f"""
                        SELECT COUNT(*)
                        FROM posts_fts f
                        JOIN posts p ON p.id = f.id
                        WHERE posts_fts MATCH ? AND {where_clause}
                    """
                    cur.execute(count_sql, [fts_query] + params)
                    total = cur.fetchone()[0]
                else:
                    rows = []
                    total = 0
            else:
                where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
                sql = f"""
                    SELECT p.id, p.url, p.author_username, p.author_name, p.date, p.summary, 
                           p.tools_mentioned, p.card_title, p.core_idea, p.action_steps, p.key_insight, p.tags,
                           p.user_collection, p.level1_hub, p.level1_hub_title, p.level2_category, p.level3_subcategory
                    FROM posts p
                    {where_clause}
                    ORDER BY p.id ASC
                    LIMIT ? OFFSET ?
                """
                cur.execute(sql, params + [limit, offset])
                rows = cur.fetchall()

                count_sql = f"SELECT COUNT(*) FROM posts p {where_clause}"
                cur.execute(count_sql, params)
                total = cur.fetchone()[0]

            items = []
            for r in rows:
                items.append({
                    "id": r[0],
                    "url": r[1],
                    "author_username": r[2],
                    "author_name": r[3],
                    "date": r[4],
                    "summary": r[5],
                    "tools": json.loads(r[6]) if r[6] else [],
                    "card_title": r[7],
                    "core_idea": r[8],
                    "action_steps": json.loads(r[9]) if r[9] else [],
                    "key_insight": r[10],
                    "tags": json.loads(r[11]) if r[11] else [],
                    "user_collection": r[12].strip() if r[12] else "",
                    "level1_hub": r[13],
                    "level1_hub_title": r[14],
                    "level2_category": r[15],
                    "level3_subcategory": r[16]
                })

            self._send_json({
                "items": items,
                "total": total,
                "page": page,
                "limit": limit
            })

def run_server():
    print(f"🚀 Telegram Mini App Server starting on http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), KnowledgeBaseHandler) as httpd:
        httpd.allow_reuse_address = True
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    run_server()
