import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, PreCheckoutQueryHandler, filters

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🔑 Ishonchli va to'g'ri bot tokeni
TOKEN = "8833579481:AAGF_mf71WM0AOD6VgngzEMfJiMXqvbyYzo"
ADMIN_USERNAME = "sots12"
BOT_USERNAME = "sots12_bot"

# O'yinchilar bazasi
survival_users = {}

# 3 Tildagi barcha matnlar va qoidalar
TEXTS = {
    "uz": {
        "reg_prompt": "📝 **Ro'yxatdan o'tish uchun iltimos o'z username'ingizni '@' belgisi bilan yuboring (masalan: @sots12):**",
        "reg_error": "❌ Username xato! Iltimos, boshiga '@' belgisini qo'yib qaytadan yuboring (masalan: @sots12):",
        "reg_success": "🎉 Tabriklaymiz, ro'yxatdan o'tdingiz!",
        "welcome": "🏆 **Survival Battle: So'nggi Omon Qolgan**\n\n📜 **O'yin qoidalari:**\n• O'yinga qo'shilish uchun 1 Stars to'lanadi.\n• Har kuni 1 marta '✅ Tirikman' tugmasini bosib o'zingizni tasdiqlang.\n• Agar 1 kun kirmasangiz, o'yindan chiqib ketasiz va qayta kirish uchun yana 1 Stars to'laysiz.\n• Oxirgi qolgan g'olib yig'ilgan fondning **85%** oladi, **15%** platforma komissiyasi!\n\n👥 Tirik o'yinchilar: **{total_players} ta**\n💰 Jami Sovrin Jamg'armasi: **{pool} Stars**\n\nKerakli bo'limni tanlang:",
        "join_title": "Survival O'yiniga Qo'shilish",
        "join_desc": "Omon qolish uchun 1 Stars badal to'lovi",
        "join_btn": "⭐ O'yinga qo'shilish (1 Stars)",
        "checkin_btn": "✅ Tirikman (Kunlik belgi)",
        "share_btn": "📢 Do'stlarga ulashish",
        "profile_btn": "👤 Mening holatim",
        "lang_btn": "🌐 Tilni o'zgartirish",
        "back": "🔙 Orqaga",
        "in_game": "🟢 O'yinda",
        "not_in_game": "🔴 O'yinda emas",
        "profile_lang": "Til: O'zbekcha",
        "checked_in": "🎉 Tabriklaymiz, siz o'yindasiz!",
        "already_checked": "⚠️ Siz bugun allaqachon 'Tirikman' deb belgi qo'ygansiz!",
        "not_in_game_alert": "❌ Siz o'yinda emassiz! O'yinga qo'shilish uchun 1 Stars to'lang."
    },
    "ru": {
        "reg_prompt": "📝 **Для регистрации пожалуйста отправьте свой username с символом '@' (например: @sots12):**",
        "reg_error": "❌ Неверный username! Пожалуйста, отправьте заново, начиная с символа '@' (например: @sots12):",
        "reg_success": "🎉 Поздравляем, вы успешно зарегистрировались!",
        "welcome": "🏆 **Survival Battle: Последний выживший**\n\n📜 **Правила игры:**\n• Для участия в игре оплачивается 1 Stars.\n• Подтверждайте свое участие кнопкой '✅ Я жив' каждый день.\n• Если пропустите 1 день, выбываете, и для повторного входа потребуется снова оплатить 1 Stars.\n• Победитель забирает **85%** призового фонда, **15%** — комиссия платформы!\n\n👥 Живых игроков: **{total_players}**\n💰 Общий призовой фонд: **{pool} Stars**\n\nВыберите действие:",
        "join_title": "Участие в Survival Battle",
        "join_desc": "Взнос 1 Stars для выживания в игре",
        "join_btn": "⭐ Участвовать (1 Stars)",
        "checkin_btn": "✅ Я жив (Ежедневно)",
        "share_btn": "📢 Поделиться с другом",
        "profile_btn": "👤 Мой статус",
        "lang_btn": "🌐 Сменить язык",
        "back": "🔙 Назад",
        "in_game": "🟢 В игре",
        "not_in_game": "🔴 Не в игре",
        "profile_lang": "Язык: Русский",
        "checked_in": "🎉 Поздравляем, вы в игре!",
        "already_checked": "⚠️ Вы уже отметились как 'Жив' сегодня!",
        "not_in_game_alert": "❌ Вы не в игре! Оплатите 1 Stars для участия."
    },
    "en": {
        "reg_prompt": "📝 **To register, please send your username starting with '@' (e.g., @sots12):**",
        "reg_error": "❌ Invalid username! Please send it again starting with '@' (e.g., @sots12):",
        "reg_success": "🎉 Congratulations, you have successfully registered!",
        "welcome": "🏆 **Survival Battle: Last Man Standing**\n\n📜 **Game Rules:**\n• Join the game by paying 1 Stars.\n• Click '✅ I am alive' every day to check in.\n• If you miss a day, you are eliminated and must pay 1 Stars again to rejoin.\n• The last winner takes **85%** of the prize pool, **15%** goes to platform commission!\n\n👥 Alive players: **{total_players}**\n💰 Total Prize Pool: **{pool} Stars**\n\nChoose an action:",
        "join_title": "Join Survival Battle",
        "join_desc": "1 Stars entry fee to survive",
        "join_btn": "⭐ Join Game (1 Stars)",
        "checkin_btn": "✅ I am alive (Daily check-in)",
        "share_btn": "📢 Share with friends",
        "profile_btn": "👤 My Status",
        "lang_btn": "🌐 Change Language",
        "back": "🔙 Back",
        "in_game": "🟢 In Game",
        "not_in_game": "🔴 Not in Game",
        "profile_lang": "Language: English",
        "checked_in": "🎉 Congratulations, you are in the game!",
        "already_checked": "⚠️ You have already checked in today!",
        "not_in_game_alert": "❌ You are not in the game! Pay 1 Stars to join."
    }
}

def get_user(user_id):
    if user_id not in survival_users:
        survival_users[user_id] = {
            "name": None,
            "registered": False,
            "in_game": False,
            "checked_today": False,
            "lang": None
        }
    return survival_users[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_data = get_user(user.id)
    
    if user.username:
        u_data["username"] = user.username

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
        t = TEXTS[lang]
        text = t["reg_prompt"]
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown")
        return

    lang = u_data["lang"]
    t = TEXTS[lang]

    total_players = sum(1 for u in survival_users.values() if u["in_game"])
    prize_pool = total_players * 1

    keyboard = [
        [InlineKeyboardButton(t["join_btn"], callback_data="join_game")],
        [InlineKeyboardButton(t["checkin_btn"], callback_data="check_in")],
        [InlineKeyboardButton(t["share_btn"], url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=Survival+o'yiniga+qo'shiling+va+Stars+yutib+oling!")],
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
    if user.username:
        u_data["username"] = user.username
        
    data = query.data

    if data.startswith("set_"):
        u_data["lang"] = data.split("_")[1]
        await start(update, context)
        return

    if not u_data["lang"] or not u_data["registered"]:
        await start(update, context)
        return

    lang = u_data["lang"]
    t = TEXTS[lang]

    if data == "lang_menu":
        u_data["lang"] = None
        u_data["registered"] = False
        await start(update, context)

    elif data == "join_game":
        if u_data["in_game"]:
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
        if not u_data["in_game"]:
            await query.message.reply_text(t["not_in_game_alert"])
            return
        if u_data["checked_today"]:
            await query.message.reply_text(t["already_checked"])
            return
        
        u_data["checked_today"] = True
        await query.message.reply_text(t["checked_in"])
        await start(update, context)

    elif data == "my_profile":
        status = t["in_game"] if u_data["in_game"] else t["not_in_game"]
        text = f"👤 Username: {u_data['name']}\n📊 Status: {status}\n🌐 {t['profile_lang']}"
        kb = [[InlineKeyboardButton(t["back"], callback_data="back_home")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif data == "back_home":
        await start(update, context)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_data = get_user(user.id)
    if user.username:
        u_data["username"] = user.username

    if u_data["lang"] and not u_data["registered"]:
        text_input = update.message.text.strip()
        lang = u_data["lang"]
        t = TEXTS[lang]

        if not text_input.startswith("@"):
            await update.message.reply_text(t["reg_error"])
            return

        u_data["name"] = text_input
        u_data["registered"] = True

        await update.message.reply_text(t["reg_success"])

        # Ro'yxatdan o'tganini adminga yuborish
        for uid, udat in survival_users.items():
            if udat.get("username", "").lower() == ADMIN_USERNAME.lower():
                try:
                    await context.bot.send_message(
                        chat_id=uid,
                        text=f"🚨 **Yangi o'yinchi ro'yxatdan o'tdi!**\n\n👤 Username: {text_input}\n🆔 ID: {user.id}",
                        parse_mode="Markdown"
                    )
                except:
                    pass

        await start(update, context)

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload == "join_survival_game":
        await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_data = get_user(user.id)
    u_data["in_game"] = True
    u_data["checked_today"] = True

    for uid, udat in survival_users.items():
        if udat.get("username", "").lower() == ADMIN_USERNAME.lower():
            try:
                total_active = sum(1 for u in survival_users.values() if u["in_game"])
                await context.bot.send_message(
                    chat_id=uid,
                    text=f"🎮 **O'yinga qo'shilish (1 Stars to'landi):**\n\n👤 Username: {u_data['name']}\n👥 Jami tirik o'yinchilar: {total_active} ta",
                    parse_mode="Markdown"
                )
            except:
                pass

    await update.message.reply_text("🎉 **Tabriklaymiz!** Siz o'yinga muvaffaqiyatli qo'shildingiz va asosiy kurashga kirdingiz!")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    print("Survival Game Bot to'liq tayyor va ishga tushdi!")
    application.run_polling()
