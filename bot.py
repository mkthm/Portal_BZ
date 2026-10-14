import asyncio
import logging
import os
import sys
import json
import html

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo
)
from dotenv import load_dotenv

import db_helper

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=ENV_FILE)
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

def get_webapp_url():
    url_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "current_tunnel_url.txt")
    if os.path.exists(url_file):
        try:
            with open(url_file, "r", encoding="utf-8") as f:
                u = f.read().strip()
                if u.startswith("https://"):
                    return u
        except Exception:
            pass
    load_dotenv(dotenv_path=ENV_FILE, override=True)
    return os.getenv("WEBAPP_URL", "https://887bc607e5945d.lhr.life")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

dp = Dispatcher()

@dp.update.outer_middleware()
async def log_update_middleware(handler, event, data):
    if event.message:
        logging.info(f"📨 Message from {event.message.from_user.id} (@{event.message.from_user.username}): '{event.message.text}'")
    elif event.callback_query:
        logging.info(f"🔘 Callback from {event.callback_query.from_user.id}: '{event.callback_query.data}'")
    return await handler(event, data)

def escape(text):
    if not text:
        return ""
    return html.escape(str(text))

# --- Main Menu Keyboard ---
def get_main_menu_keyboard():
    url = get_webapp_url()
    webapp_btn = KeyboardButton(text="🚀 Mini App (Каталог)")
    if url.startswith("https://"):
        webapp_btn = KeyboardButton(text="🚀 Mini App (Каталог)", web_app=WebAppInfo(url=url))

    counts = db_helper.get_hub_counts()
    ai_cnt = counts.get('ai', 0)
    mkt_cnt = counts.get('marketing', 0)
    biz_cnt = counts.get('business', 0)
    use_cnt = counts.get('useful', 0)

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"🤖 AI & Нейросети ({ai_cnt})"), KeyboardButton(text=f"📈 Маркетинг & E-com ({mkt_cnt})")],
            [KeyboardButton(text=f"🛠 Бизнес & Управление ({biz_cnt})"), KeyboardButton(text=f"📌 Полезный софт & IT ({use_cnt})")],
            [KeyboardButton(text="🧰 Каталог сервисов"), KeyboardButton(text="⭐ Мои закладки")],
            [webapp_btn, KeyboardButton(text="🎲 Случайная находка")],
            [KeyboardButton(text="🔍 Поиск по базе")]
        ],
        resize_keyboard=True
    )

# --- Category Hub View ---
def render_hub_view(hub_id):
    hub_info = db_helper.HUBS.get(hub_id, {})
    hub_title = hub_info.get('title', 'Разделы')
    categories = db_helper.get_categories_by_hub(hub_id)
    total_hub = sum(cnt for _, _, _, cnt in categories)

    text = (
        f"<b>{escape(hub_title)}</b> (Всего: {total_hub} материалов)\n\n"
        f"Выберите функциональный раздел:"
    )

    kb = []
    for cid, name, icon, cnt in categories:
        kb.append([InlineKeyboardButton(text=f"{icon} {name} ({cnt})", callback_data=f"cat_{cid}")])
    kb.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="hub_all")])

    return text, InlineKeyboardMarkup(inline_keyboard=kb)

# --- Subcategories View ---
def render_category_subcategories_view(cat_id):
    cat_info = db_helper.CATEGORIES.get(cat_id)
    if not cat_info:
        return "Раздел не найден.", InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 К разделам", callback_data="hub_all")]])

    cat_name = cat_info['name']
    cat_icon = cat_info['icon']
    hub_id = cat_info['hub']
    hub_info = db_helper.HUBS.get(hub_id, {})
    hub_title = hub_info.get('title', 'Хаб')

    subcats = db_helper.get_subcategories_by_cat(cat_id)
    total_cat = sum(cnt for _, _, _, cnt in subcats)

    text = (
        f"{cat_icon} <b>{escape(cat_name)}</b> ({total_cat} материалов)\n"
        f"<i>Хаб: {escape(hub_title)}</i>\n\n"
        f"Выберите специализацию / подраздел:"
    )

    kb = []
    for sid, name, icon, cnt in subcats:
        kb.append([InlineKeyboardButton(text=f"{icon} {name} ({cnt})", callback_data=f"p_sub_{sid}_1")])
    kb.append([InlineKeyboardButton(text=f"🔙 К разделам {hub_info.get('icon', '')}", callback_data=f"hub_{hub_id}")])

    return text, InlineKeyboardMarkup(inline_keyboard=kb)

# --- Render Catalog List View (5 items per page) ---
def render_catalog_list(items, total, page, total_pages, ctx_type, ctx_val, title_header, subtitle=""):
    if not items:
        return "В этой подборке пока нет материалов.", InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 К разделам", callback_data="hub_all")]])

    text_lines = [f"<b>{escape(title_header)}</b>"]
    if subtitle:
        text_lines.append(f"<i>{escape(subtitle)}</i>")
    text_lines.append(f"<i>Страница {page} из {total_pages} (Всего: {total})</i>\n")

    num_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    num_buttons = []

    for i, itm in enumerate(items):
        pid, title, author, tools_json, date_str = itm
        tools = json.loads(tools_json) if tools_json else []
        tools_badge = f" `[{', '.join(tools[:2])}]`" if tools else ""
        emoji = num_emojis[i] if i < len(num_emojis) else f"{i+1}."

        clean_title = escape(title)
        author_badge = f"@{escape(author)}" if author else "Instagram"
        text_lines.append(f"{emoji} <b>{clean_title}</b>{tools_badge}\n     👤 {author_badge}\n")

        # Compact callback: o_pid_ctxType_ctxVal_page
        num_buttons.append(InlineKeyboardButton(text=emoji, callback_data=f"o_{pid}_{ctx_type}_{ctx_val}_{page}"))

    text = "\n".join(text_lines)

    keyboard = [num_buttons]

    # Page navigation row
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Стр", callback_data=f"p_{ctx_type}_{ctx_val}_{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page} / {total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Стр ➡️", callback_data=f"p_{ctx_type}_{ctx_val}_{page + 1}"))

    if nav_row:
        keyboard.append(nav_row)

    # Back row
    if ctx_type == "sub":
        sid = int(ctx_val)
        sub_info = db_helper.SUBCATEGORIES.get(sid, {})
        cat_id = sub_info.get('cat_id', 1)
        keyboard.append([InlineKeyboardButton(text="🔙 К списку подразделов", callback_data=f"cat_{cat_id}")])
    elif ctx_type == "t":
        keyboard.append([InlineKeyboardButton(text="🔙 К каталогу сервисов", callback_data="hub_tools")])
    elif ctx_type == "fav":
        keyboard.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="hub_all")])
    elif ctx_type == "s":
        keyboard.append([InlineKeyboardButton(text="🔍 Новый поиск", callback_data="prompt_search")])
    else:
        keyboard.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="hub_all")])

    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- Render Single Post Card View ---
def format_post_card(post, user_id=None):
    pid = post[0]
    auth_u = post[2]
    auth_n = post[3]
    date_str = post[4]
    tools_json = post[7]
    card_title = post[9] if len(post) > 9 and post[9] else f"Материал #{pid}"
    core_idea = post[10] if len(post) > 10 and post[10] else post[5]
    key_insight = post[12] if len(post) > 12 and post[12] else ""
    user_col = post[14].strip() if len(post) > 14 and post[14] else ""
    cat_name = post[18] if len(post) > 18 and post[18] else ""
    subcat_name = post[19] if len(post) > 19 and post[19] else ""

    tools = json.loads(tools_json) if tools_json else []
    author_display = f"@{escape(auth_u)}" if auth_u else "Instagram"
    if auth_n and auth_n != auth_u:
        author_display += f" ({escape(auth_n)})"

    tools_line = f"\n🛠 <b>Инструменты:</b> {', '.join(escape(t) for t in tools)}" if tools else ""
    date_line = f" • <i>{escape(date_str[:10])}</i>" if date_str else ""
    
    # Hierarchy breadcrumb
    nav_line = ""
    if cat_name and subcat_name:
        nav_line = f"🏷 <b>{escape(cat_name)}</b> ➔ <i>{escape(subcat_name)}</i>\n"
    elif cat_name:
        nav_line = f"🏷 <b>{escape(cat_name)}</b>\n"

    col_line = f"📁 <b>Instagram:</b> <i>{escape(user_col)}</i>\n" if user_col else ""
    insight_line = f"\n\n🎯 <b>Главный инсайт:</b>\n{escape(key_insight)}" if key_insight else ""

    text = (
        f"📌 <b>{escape(card_title)}</b>\n"
        f"👤 {author_display}{date_line}\n"
        f"{nav_line}"
        f"{col_line}"
        f"{tools_line}\n\n"
        f"💡 <b>В чём суть:</b>\n{escape(core_idea)}"
        f"{insight_line}\n"
    )
    return text

def build_post_card_keyboard(post, ctx_type, ctx_val, page, user_id=None):
    pid, url = post[0], post[1]
    buttons = []

    # Row 1: Direct link & Bookmark
    first_row = []
    if url:
        first_row.append(InlineKeyboardButton(text="🔗 В Instagram", url=url))
    
    is_fav = db_helper.is_favorite(user_id, pid) if user_id else False
    fav_text = "⭐️ В закладках" if is_fav else "☆ В закладки"
    first_row.append(InlineKeyboardButton(text=fav_text, callback_data=f"fav_{pid}_{ctx_type}_{ctx_val}_{page}"))
    buttons.append(first_row)

    # Row 2: Action steps
    buttons.append([
        InlineKeyboardButton(text="📋 Пошаговый разбор (шаги/команды)", callback_data=f"stp_{pid}_{ctx_type}_{ctx_val}_{page}")
    ])

    # Row 3: Return to catalog list
    if ctx_type == "rnd":
        buttons.append([
            InlineKeyboardButton(text="🎲 Еще одну случайную", callback_data="rnd_next"),
            InlineKeyboardButton(text="🔙 В меню", callback_data="hub_all")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text=f"🔙 К списку (Стр. {page})", callback_data=f"p_{ctx_type}_{ctx_val}_{page}")
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def cmd_start(message: types.Message, bot: Bot):
    webapp_url = get_webapp_url()
    try:
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        if webapp_url.startswith("https://"):
            await bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(
                    text="🚀 База Знаний",
                    web_app=WebAppInfo(url=webapp_url)
                )
            )
    except Exception:
        pass

    start_inline = None
    if webapp_url and webapp_url.startswith("https://"):
        start_inline = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Открыть Mini App (Каталог)", web_app=WebAppInfo(url=webapp_url))],
            [InlineKeyboardButton(text="🌐 Открыть в браузере", url=webapp_url)]
        ])

    await message.answer(
        "👋 <b>Добро пожаловать в Базу Знаний!</b>\n\n"
        "Здесь систематизированы ваши <b>сохраненные посты и Reels из Instagram</b> "
        "(441 отборный материал по нейросетям, инструментам, маркетингу и бизнесу) — <b>без рекламного шума, кликбейта и призывов!</b>\n\n"
        "🌳 <b>Логическая иерархия каталога:</b>\n"
        "• <b>Уровень 1 (Хабы):</b> AI, Маркетинг, Бизнес, Полезный софт\n"
        "• <b>Уровень 2 (Разделы):</b> Вайб-кодинг, LLM, Reels, Маркетплейсы, Финансы...\n"
        "• <b>Уровень 3 (Подразделы):</b> Скиллы & MCP, Claude Code, Промпты, P&L, 1688...\n"
        "• 📁 <b>Источник:</b> в каждой карточке сохранена исходная папка Instagram.\n\n"
        "📱 <b>Доступен Telegram Mini App:</b> нажмите кнопку ниже для быстрого поиска, фильтров и просмотра всех карточек!",
        reply_markup=start_inline,
        parse_mode="HTML"
    )
    await message.answer("Выберите интересующий хаб в меню ниже:", reply_markup=get_main_menu_keyboard())

@dp.message(Command("app"))
@dp.message(F.text == "🚀 Mini App (Каталог)")
async def menu_mini_app(message: types.Message, bot: Bot):
    webapp_url = get_webapp_url()
    try:
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        if webapp_url.startswith("https://"):
            await bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(
                    text="🚀 База Знаний",
                    web_app=WebAppInfo(url=webapp_url)
                )
            )
    except Exception:
        pass

    kb = []
    if webapp_url.startswith("https://"):
        kb.append([InlineKeyboardButton(text="🚀 Запустить Mini App", web_app=WebAppInfo(url=webapp_url))])
        kb.append([InlineKeyboardButton(text="🌐 Открыть в браузере", url=webapp_url)])
    else:
        kb.append([InlineKeyboardButton(text="🌐 Открыть веб-каталог (Local)", url=webapp_url)])

    await message.answer(
        "📱 <b>Telegram Mini App (Интерактивный Каталог)</b>\n\n"
        "• Мгновенный живой поиск по всей базе (441 отборный материал)\n"
        "• Каскадные фильтры по хабам, разделам и подразделам\n"
        "• Теги инструментов (#claude-code, #mcp, #n8n, #prompts, #reels)\n"
        "• Выпадающие пошаговые разборы и команды\n"
        "• Темная тема под интерфейс Telegram",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# --- Category Hubs Menu Handlers ---
@dp.message(F.text.startswith("🤖 AI"))
async def menu_ai(message: types.Message):
    text, kb = render_hub_view("ai")
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.message(F.text.startswith("📈 Маркетинг"))
async def menu_marketing(message: types.Message):
    text, kb = render_hub_view("marketing")
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.message(F.text.startswith("🛠 Бизнес"))
async def menu_business(message: types.Message):
    text, kb = render_hub_view("business")
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.message(F.text.startswith("📌 Полезный"))
async def menu_useful(message: types.Message):
    text, kb = render_hub_view("useful")
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.message(F.text == "🧰 Каталог сервисов")
async def menu_tools(message: types.Message):
    tools = db_helper.get_tools_list(limit=24)
    rows = []
    for i in range(0, len(tools), 2):
        row = []
        for tid, t_name, count in tools[i:i+2]:
            row.append(InlineKeyboardButton(text=f"{t_name} ({count})", callback_data=f"p_t_{tid}_1"))
        rows.append(row)
    await message.answer("🧰 <b>Топ упоминаемых сервисов и нейросетей:</b>\nВыберите сервис для просмотра списка карточек:",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                         parse_mode="HTML")

@dp.message(F.text == "⭐ Мои закладки")
async def menu_favorites(message: types.Message):
    user_id = message.from_user.id
    items, total, total_pages = db_helper.get_favorites_page(user_id, page=1, per_page=5)
    if total == 0:
        await message.answer("⭐ У вас пока нет сохраненных закладок.\nНажимайте <b>«☆ В закладки»</b> на любой карточке, чтобы добавить пост сюда!",
                             parse_mode="HTML")
        return

    text, kb = render_catalog_list(items, total, 1, total_pages, "fav", "0", "⭐ Ваши избранные закладки")
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.message(F.text == "🎲 Случайная находка")
async def menu_random(message: types.Message):
    post = db_helper.get_random_post()
    if not post:
        await message.answer("База пока пуста.")
        return
    user_id = message.from_user.id
    text = "🎲 <b>Случайная находка из базы:</b>\n\n" + format_post_card(post, user_id)
    kb = build_post_card_keyboard(post, "rnd", "0", 1, user_id)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.message(F.text == "🔍 Поиск по базе")
async def menu_search_prompt(message: types.Message):
    await message.answer(
        "🔍 <b>Полнотекстовый поиск по базе</b>\n\n"
        "Отправьте ключевое слово или фразу в чат.\n\n"
        "💡 <i>Примеры для поиска:</i>\n"
        "• <code>Claude Code</code> — плагины, скиллы, вайб-кодинг\n"
        "• <code>n8n</code> — воркфлоу, сценарии, автоматизация\n"
        "• <code>воронка</code> — лидогенерация, direct-боты\n"
        "• <code>kling</code> или <code>wan</code> — генерация видео\n"
        "• <code>промпт</code> — готовые промпты для LLM\n"
        "• <code>mcp</code> — интеграции и протоколы агентов",
        parse_mode="HTML"
    )

# --- Callbacks ---
@dp.callback_query(F.data == "noop")
async def cb_noop(callback: types.CallbackQuery):
    await callback.answer()

@dp.callback_query(F.data == "prompt_search")
async def cb_prompt_search(callback: types.CallbackQuery):
    await callback.message.answer("🔍 Введите поисковый запрос в чат:")
    await callback.answer()

@dp.callback_query(F.data == "rnd_next")
async def cb_random_next(callback: types.CallbackQuery):
    post = db_helper.get_random_post()
    if not post:
        await callback.answer("База пока пуста.")
        return
    user_id = callback.from_user.id
    text = "🎲 <b>Случайная находка из базы:</b>\n\n" + format_post_card(post, user_id)
    kb = build_post_card_keyboard(post, "rnd", "0", 1, user_id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("hub_"))
async def cb_hub(callback: types.CallbackQuery):
    grp = callback.data.split("_")[1]
    if grp == "tools":
        tools = db_helper.get_tools_list(limit=24)
        rows = []
        for i in range(0, len(tools), 2):
            row = []
            for tid, t_name, count in tools[i:i+2]:
                row.append(InlineKeyboardButton(text=f"{t_name} ({count})", callback_data=f"p_t_{tid}_1"))
            rows.append(row)
        await callback.message.edit_text("🧰 <b>Каталог сервисов:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")
    elif grp == "all":
        await callback.message.edit_text("📂 Выберите интересующий хаб в основном меню бота ниже.", parse_mode="HTML")
    else:
        text, kb = render_hub_view(grp)
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# Level 2 Category selected -> show Level 3 Subcategories
@dp.callback_query(F.data.startswith("cat_"))
async def cb_category(callback: types.CallbackQuery):
    cid = int(callback.data.split("_")[1])
    text, kb = render_category_subcategories_view(cid)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# Page pagination in catalog list: p_ctxType_ctxVal_page
@dp.callback_query(F.data.startswith("p_"))
async def cb_catalog_page(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    ctx_type = parts[1]
    ctx_val = parts[2]
    page = int(parts[3])
    user_id = callback.from_user.id

    subtitle = ""
    if ctx_type == "sub":
        sid = int(ctx_val)
        sub_info = db_helper.SUBCATEGORIES.get(sid, {})
        cat_id = sub_info.get('cat_id', 1)
        cat_info = db_helper.CATEGORIES.get(cat_id, {})
        title_header = f"{sub_info.get('icon', '🏷')} {sub_info.get('name', 'Подраздел')}"
        subtitle = f"Раздел: {cat_info.get('icon', '')} {cat_info.get('name', '')}"
        items, total, total_pages = db_helper.get_subcat_posts_page(sid, page=page, per_page=5)
    elif ctx_type == "t":
        tid = int(ctx_val)
        items, total, total_pages, tool_name = db_helper.get_tool_posts_page(tid, page=page, per_page=5)
        title_header = f"🧰 Сервис: {tool_name}"
    elif ctx_type == "s":
        q = db_helper.get_search_query(ctx_val)
        items, total, total_pages = db_helper.get_search_posts_page(q, page=page, per_page=5)
        title_header = f"🔍 Результаты поиска «{q}»"
    elif ctx_type == "fav":
        items, total, total_pages = db_helper.get_favorites_page(user_id, page=page, per_page=5)
        title_header = "⭐ Ваши избранные закладки"
    else:
        await callback.answer()
        return

    text, kb = render_catalog_list(items, total, page, total_pages, ctx_type, ctx_val, title_header, subtitle)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# Open single post card from catalog list: o_pid_ctxType_ctxVal_page
@dp.callback_query(F.data.startswith("o_"))
async def cb_open_post_card(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    pid = int(parts[1])
    ctx_type = parts[2]
    ctx_val = parts[3]
    page = int(parts[4])
    user_id = callback.from_user.id

    post = db_helper.get_post_by_id(pid)
    if not post:
        await callback.answer("Пост не найден.")
        return

    text = format_post_card(post, user_id)
    kb = build_post_card_keyboard(post, ctx_type, ctx_val, page, user_id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# Toggle favorite
@dp.callback_query(F.data.startswith("fav_"))
async def cb_toggle_favorite(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    pid = int(parts[1])
    ctx_type = parts[2]
    ctx_val = parts[3]
    page = int(parts[4])
    user_id = callback.from_user.id

    is_now_fav = db_helper.toggle_favorite(user_id, pid)
    status_msg = "⭐️ Добавлено в закладки!" if is_now_fav else "Удалено из закладок."
    await callback.answer(status_msg)

    post = db_helper.get_post_by_id(pid)
    if post:
        kb = build_post_card_keyboard(post, ctx_type, ctx_val, page, user_id)
        await callback.message.edit_reply_markup(reply_markup=kb)

# View Action Steps Breakdown
@dp.callback_query(F.data.startswith("stp_"))
async def cb_steps_breakdown(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    pid = int(parts[1])
    ctx_type = parts[2]
    ctx_val = parts[3]
    page = int(parts[4])

    post = db_helper.get_post_by_id(pid)
    if not post:
        await callback.answer("Пост не найден.")
        return

    card_title = post[9] if len(post) > 9 and post[9] else f"Материал #{pid}"
    steps_json = post[11] if len(post) > 11 else ""
    steps = json.loads(steps_json) if steps_json else []

    formatted_steps = []
    for idx, s in enumerate(steps, 1):
        formatted_steps.append(f"<b>{idx}.</b> {escape(s)}")
    steps_text = "\n\n".join(formatted_steps) if formatted_steps else "<i>Шаги описаны в видео.</i>"

    text = (
        f"📋 <b>Пошаговый разбор</b>\n"
        f"<i>«{escape(card_title)}»</i>\n\n"
        f"{steps_text}"
    )

    if len(text) > 3800:
        text = text[:3800] + "...\n<i>(сокращено)</i>"

    back_callback = f"o_{pid}_{ctx_type}_{ctx_val}_{page}"
    if ctx_type == "rnd":
        back_callback = "rnd_next"

    kb = [
        [InlineKeyboardButton(text="⬅️ Назад к карточке", callback_data=back_callback)],
        [InlineKeyboardButton(text="🔗 В Instagram", url=post[1])]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    await callback.answer()

# Free-form search query
@dp.message(F.text)
async def text_search_handler(message: types.Message):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Слишком короткий поисковый запрос.")
        return

    items, total, total_pages = db_helper.get_search_posts_page(query, page=1, per_page=5)
    if total == 0:
        await message.answer(
            f"🔍 По запросу <b>«{escape(query)}»</b> ничего не найдено.\nПопробуйте другое слово или воспользуйтесь каталогом подборок.",
            parse_mode="HTML"
        )
        return

    sid = db_helper.create_search_session(query)
    text, kb = render_catalog_list(items, total, 1, total_pages, "s", sid, f"🔍 Результаты поиска «{query}»")
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

async def main():
    if not TOKEN:
        print("\n" + "="*60)
        print("ОШИБКА: Не задан токен бота (BOT_TOKEN)!")
        print("Создайте .env файл со строкой: BOT_TOKEN=ваш_токен")
        print("="*60 + "\n")
        sys.exit(1)

    bot = Bot(token=TOKEN)
    webapp_url = get_webapp_url()
    if webapp_url and webapp_url.startswith("https://"):
        try:
            from aiogram.types import MenuButtonWebApp, WebAppInfo
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="🚀 База Знаний",
                    web_app=WebAppInfo(url=webapp_url)
                )
            )
            print(f"✅ Telegram Menu Button установлен: {webapp_url}")
        except Exception as e:
            print(f"⚠️ Ошибка настройки Menu Button: {e}")

    print("🤖 Бот с глубокой функциональной иерархией и чистыми карточками запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
