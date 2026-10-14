import os
import re
import sys
import time
import json
import subprocess
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
TUNNEL_URL_FILE = BASE_DIR / "current_tunnel_url.txt"

def load_bot_token():
    if not ENV_PATH.exists():
        return None
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("BOT_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def update_env_file(url):
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    
    new_lines = []
    found = False
    for line in lines:
        if line.startswith("WEBAPP_URL="):
            new_lines.append(f"WEBAPP_URL={url}\n")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.insert(0, f"WEBAPP_URL={url}\n")
    
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    with open(TUNNEL_URL_FILE, "w", encoding="utf-8") as f:
        f.write(url)
    print(f"[Supervisor] 📝 Updated .env and current_tunnel_url.txt with {url}")

def notify_telegram(token, url):
    if not token:
        print("[Supervisor] ⚠️ BOT_TOKEN not found, skipping Telegram MenuButton update")
        return
    api_url = f"https://api.telegram.org/bot{token}/setChatMenuButton"
    payload = {
        "menu_button": {
            "type": "web_app",
            "text": "🚀 База Знаний",
            "web_app": {"url": url}
        }
    }
    try:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get("ok"):
                print(f"[Supervisor] ✅ Telegram MenuButton successfully updated: {url}")
            else:
                print(f"[Supervisor] ⚠️ Telegram API returned: {data}")
    except Exception as e:
        print(f"[Supervisor] ⚠️ Error updating Telegram MenuButton: {e}")

def run():
    print("[Supervisor] 🚀 Starting Tunnel Supervisor...")
    cmd = [
        "ssh",
        "-R", "80:localhost:8080",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=3",
        "nokey@localhost.run"
    ]

    while True:
        token = load_bot_token()
        print(f"[Supervisor] 🌐 Launching SSH tunnel: {' '.join(cmd)}")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        current_url = None
        try:
            for line in proc.stdout:
                line_str = line.strip()
                if line_str:
                    print(f"[Tunnel] {line_str}")
                match = re.search(r"https://[a-zA-Z0-9-]+\.lhr\.life", line_str)
                if match:
                    detected_url = match.group(0)
                    if detected_url != current_url:
                        current_url = detected_url
                        print(f"[Supervisor] 🌟 NEW TUNNEL URL DETECTED: {current_url}")
                        update_env_file(current_url)
                        notify_telegram(token, current_url)
        except Exception as e:
            print(f"[Supervisor] ⚠️ Stream read error: {e}")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except:
                proc.kill()
        
        print("[Supervisor] 🔄 SSH tunnel disconnected. Reconnecting in 3 seconds...")
        time.sleep(3)

if __name__ == "__main__":
    run()
