import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, PreCheckoutQueryHandler, filters

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🔑 Yangi tokeningiz va admin sozlamalari
TOKEN = "8833579481:AAGF_mf71WM0AOD6VgngzEMfJiMXqvbyYzo"
ADMIN_USERNAME = "sots12"
BOT_USERNAME = "sots12_bot"
ADMIN_CHAT_ID = None  # Admin ID avtomatik aniqlanadi yoki birinchi yozgan admin bo'ladi

# --- BAZANI YARATISH (SQLITE - Xatosiz va ishonchli) ---
def init_db():
    conn = sqlite3.connect("survival_bot.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT,
            registered INTEGER,
            in_game INTEGER,
            checked_today INTEGER,
            lang TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("survival_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, name, registered, in_game, checked_today, lang FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute('''
            INSERT INTO users (user_id, username, name, registered, in_game, checked_today, lang)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, "", None, 0, 0, 0, None))
        conn.commit()
        u_data = {
            "user_id": user_id, "username": "", "name": None,
            "registered": 0, "in_game": 0, "checked_today": 0, "lang": None
        }
    else:
        u_data = {
            "user_id": row[0], "username": row[1], "name": row[2],
            "registered": row[3], "in_game": row[4], "checked_today": row[5], "lang": row[6]
        }
    cursor.close()
    conn.close()
    return u_data

def update_user(user_id, **kwargs):
    conn = sqlite3.connect("survival_bot.db")
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("survival_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, name, registered, in_game, checked_today, lang FROM users")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    users = {}
    for row in rows:
        users[row[0]] = {
            "user_id": row[0], "username": row[1], "name": row[2],
            "registered": row[3], "in_game": row[4], "checked_today": row[5], "lang": row[6]
        }
    return users

# Sahifalash uchun funksiya
def get_paginated_players(page=0, per_page=10):
    conn = sqlite3.connect("survival_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE in_game = 1")
    total_count = cursor.fetchone()[0]
    
    offset = page * per_page
    cursor.execute("SELECT name, username FROM users WHERE in_game = 1 ORDER BY user_id DESC LIMIT ? OFFSET ?", (per_page, offset))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows, total_count

# 3 Tildagi matnlar
TEXTS = {
    "uz": {
        "reg_prompt": "📝 **Ro'yxatdan o'tish uchun iltimos o'z username'ingizni '@' belgisi bilan yuboring (masalan: @sots12):**",
        "reg_error": "❌ Username xato! Iltimos, boshiga '@' belgisini qo'yib qaytadan yuboring (masalan: @sots12):",
        "reg_success": "🎉 Tabriklaymiz, ro'yxatdan o'tdingiz!",
        "welcome": "🏆 **Survival Battle: So'nggi Omon Qolgan**\n\n📜 **O'yin qoidalari:**\n• O'yinga qo'shilish uchun 1 Stars to'lanadi.\n• Har kuni 1 marta '✅ Tirikman' tugmasini bosib o'zingizni tasdiqlang.\n• Oxirgi qolgan g'olib yig'ilgan fondning **85%** oladi, **15%** komissiya!\n\n👥 Tirik o'yinchilar: **{total_players} ta**\n💰 Jami Sovrin: **{pool} Stars**\n\nKerakli bo'limni tanlang:",
        "join_title": "Survival O'yiniga Qo'shilish",
        "join_desc": "Omon qolish uchun 1 Stars badal to'lovi",
        "join_btn": "⭐ O'yinga qo'shilish (1 Stars)",
        "checkin_btn": "✅ Tirikman (Kunlik belgi)",
        "players_btn": "👥 O'yinchilar ro'yxati",
        "share_btn": "📢 Do'stlarga ulashish",
        "profile_btn": "👤 Mening holatim",
        "lang_btn": "🌐 Tilni o'zgartirish",
        "back": "🔙 Orqaga",
        "in_game": "🟢 O'yinda",
        "not_in_game": "🔴 O'yinda emas",
        "profile_lang": "Til: O'zbekcha",
        "checked_in": "🎉 Tabriklaymiz, siz o'yindasiz!",
        "already_checked": "⚠️ Siz bugun allaqachon belgi qo'ygansiz!",
        "not_in_game_alert": "❌ Siz o'yinda emassiz! 1 Stars to'lang."
    },
    "ru": {
        "reg_prompt": "📝 **Для регистрации отправьте ваш username с '@' (например: @sots12):**",
        "reg_error": "❌ Неверный username! Отправьте заново с '@':",
        "reg_success": "🎉 Поздравляем, вы зарегистрированы!",
        "welcome": "🏆 **Survival Battle: Последний выживший**\n\n👥 Живых игроков: **{total_players}**\n💰 Призовой фонд: **{pool} Stars**\n\nВыберите действие:",
        "join_title": "Участие в Survival Battle",
        "join_desc": "Взнос 1 Stars",
        "join_btn": "⭐ Участвовать (1 Stars)",
        "checkin_btn": "✅ Я жив",
        "players_btn": "👥 Список игроков",
        "share_btn": "📢 Поделиться",
        "profile_btn": "👤 Мой статус",
        "lang_btn": "🌐 Язык",
        "back": "🔙 Назад",
        "in_game": "🟢 В игре",
        "not_in_game": "🔴 Не в игре",
        "profile_lang": "Язык: Русский",
        "checked_in": "🎉 Вы отметились!",
        "already_checked": "⚠️ Вы уже отметились сегодня!",
        "not_in_game_alert": "❌ Вы не в игре!"
    },
    "en": {
        "reg_prompt": "📝 **To register, send your username with '@':**",
        "reg_error": "❌ Invalid username! Send again with '@':",
        "reg_success": "🎉 Successfully registered!",
        "welcome": "🏆 **Survival Battle: Last Man Standing**\n\n👥 Alive players: **{total_players}**\n💰 Prize Pool: **{pool} Stars**\n\nChoose an action:",
        "join_title": "Join Survival Battle",
        "join_desc": "1 Stars entry fee",
        "join_btn": "⭐ Join Game (1 Stars)",
        "checkin_btn": "✅ I am alive",
        "players_btn": "👥 Players list",
        "share_btn": "📢 Share",
        "profile_btn": "👤 My Status",
        "lang_btn": "🌐 Language",
        "back": "🔙 Back",
        "in_game": "🟢 In Game",
        "not_in_game": "🔴 Not in Game",
        "profile_lang": "Language: English",
        "checked_in": "🎉 Checked in!",
        "already_checked": "⚠️ Already checked in today!",
        "not_in_game_alert": "❌ Not in game!"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_data = get_user(user.id)
    
    if user.username and u_data["username"] != user.username:
        update_user(user.id, username=user.username)

    if not u_data["lang"]:
        kb = [
            [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_uz"),
             InlineKeyboardButton("🇷🇺 Русский", callback_data="set_ru"),
             InlineKeyboardButton("🇬🇧 English", callback_data="set_en")]
        ]
        text = "🌐 Tilni tanlang / Выберите язык / Choose language:"
        if update.message:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        elif update.callback_query:
            await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))
        return

    if not u_data["registered"]:
        lang = u_data["lang"]
        text = TEXTS[lang]["reg_prompt"]
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown")
        return

    lang = u_data["lang"]
    t = TEXTS[lang]

    all_users = get_all_users()
    total_players = sum(1 for u in all_users.values() if u["in_game"] == 1)
    prize_pool = total_players * 1

    keyboard = [
        [InlineKeyboardButton(t["join_btn"], callback_data="join_game")],
        [InlineKeyboardButton(t["checkin_btn"], callback_data="check_in")],
        [InlineKeyboardButton(t["players_btn"], callback_data="players_page_0")],
        [InlineKeyboardButton(t["share_btn"], url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=Survival+o'yiniga+qo'shiling!")],
        [InlineKeyboardButton(t["profile_btn"], callback_data="my_profile"), InlineKeyboardButton(t["lang_btn"], callback_data="lang_menu")]
    ]

    text = t["welcome"].format(total_players=total_players, pool=prize_pool)

    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    u_data = get_user(user.id)
    data = query.data

    if data.startswith("set_"):
        update_user(user.id, lang=data.split("_")[1])
        await start(update, context)
        return

    if not u_data["lang"] or not u_data["registered"]:
        await start(update, context)
        return

    lang = u_data["lang"]
    t = TEXTS[lang]

    if data == "lang_menu":
        update_user(user.id, lang=None, registered=0)
        await start(update, context)

    elif data.startswith("players_page_"):
        page = int(data.split("_")[2])
        per_page = 10
        rows, total_count = get_paginated_players(page, per_page)
        
        max_page = (total_count - 1) // per_page if total_count > 0 else 0
        
        text = f"👥 **O'yinchilar ro'yxati** (Jami: {total_count} ta):\n\n"
        if not rows:
            text += "Hozircha o'yinchilar yo'q."
        else:
            for idx, (name, username) in enumerate(rows, start=page * per_page + 1):
                display_name = name if name else username
                text += f"{idx}. {display_name}\n"
        
        kb_buttons = []
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ Oldingi", callback_data=f"players_page_{page-1}"))
        nav_buttons.append(InlineKeyboardButton(f"📄 {page+1}/{max_page+1}", callback_data="noop"))
        if page < max_page:
            nav_buttons.append(InlineKeyboardButton("Keyingi ▶️", callback_data=f"players_page_{page+1}"))
        
        if nav_buttons:
            kb_buttons.append(nav_buttons)
        kb_buttons.append([InlineKeyboardButton(t["back"], callback_data="back_home")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb_buttons), parse_mode="Markdown")

    elif data == "join_game":
        if u_data["in_game"] == 1:
            await query.message.reply_text("⚠️ Siz allaqachon o'yindasiz!")
            return
        
        await context.bot.send_invoice(
            chat_id=user.id,
            title=t["join_title"],
            description=t["join_desc"],
            payload="join_survival_game",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Badal", 1)]
        )

    elif data == "check_in":
        if u_data["in_game"] == 0:
            await query.message.reply_text(t["not_in_game_alert"])
            return
        if u_data["checked_today"] == 1:
            await query.message.reply_text(t["already_checked"])
            return
        
        update_user(user.id, checked_today=1)
        await query.message.reply_text(t["checked_in"])
        await start(update, context)

    elif data == "my_profile":
        status = t["in_game"] if u_data["in_game"] == 1 else t["not_in_game"]
        text = f"👤 Username: {u_data['name']}\n📊 Status: {status}\n🌐 {t['profile_lang']}"
        kb = [[InlineKeyboardButton(t["back"], callback_data="back_home")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif data == "back_home":
        await start(update, context)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_data = get_user(user.id)

    if u_data["lang"] and u_data["registered"] == 0:
        text_input = update.message.text.strip()
        lang = u_data["lang"]
        t = TEXTS[lang]

        if not text_input.startswith("@"):
            await update.message.reply_text(t["reg_error"])
            return

        update_user(user.id, name=text_input, registered=1)
        await update.message.reply_text(t["reg_success"])
        
        # 🔔 Yangi foydalanuvchi ro'yxatdan o'tganda adminga xabar yuborish
        admin_msg = (
            f"🔔 **Yangi foydalanuvchi ro'yxatdan o'tdi!**\n\n"
            f"👤 Ismi: {user.full_name}\n"
            f"🔗 Username: {text_input}\n"
            f"🆔 ID: `{user.id}`"
        )
        try:
            # Agar admin o'zi botga oldin /start bosgan bo'lsa, unga xabar boradi
            # Siz o'zingizning Telegram ID raqamingizni ham shu yerga yozishingiz mumkin (masalan: 123456789)
            await context.bot.send_message(chat_id=user.id, text=admin_msg, parse_mode="Markdown") # O'ziga ham yoki adminga
        except Exception:
            pass

        # Adminga to'g'ridan-to'g'ri jo'natish uchun (agar user.username 'sots12' bo'lsa yoki admin ID ni bilsak)
        # Hozircha botni ishlatayotgan foydalanuvchining o'ziga yoki umumiy logga tushadi.

        await start(update, context)

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload == "join_survival_game":
        await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_user(user.id, in_game=1, checked_today=1)
    await update.message.reply_text("🎉 **Tabriklaymiz!** Siz o'yinga muvaffaqiyatli qo'shildingiz!")

if __name__ == '__main__':
    init_db()
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    print("Survival Game Bot SQLite baza bilan xavfsiz ishga tushdi!")
    application.run_polling()
