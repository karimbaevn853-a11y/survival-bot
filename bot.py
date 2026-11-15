import logging
import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, PreCheckoutQueryHandler, filters

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8833579481:AAGF_mf71WM0AOD6VgngzEMfJiMXqvbyYzo"
ADMIN_USERNAME = "sots12"
BOT_USERNAME = "sots12_bot"

# 📌 3 ta alohida skript kanallarining havolalari:
CHANNEL_KONTUR = "https://t.me/+n2EbLYIGHNU3OGJi"  # Konturlar kanali
CHANNEL_2V1 = "https://t.me/+Z1bsmitl4LxjN2Yy"        # 2v1 kanali
CHANNEL_OPR = "https://t.me/+mSYBb2V9VP02YzAy"        # OPR PRICE kanali

vip_users = {}

# --- RENDER PORT UCHUN FLASK SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()
# -------------------------------------

def get_user(user_id):
    if user_id not in vip_users:
        vip_users[user_id] = {
            "name": None,
            "username": "",
            "registered": False,
            "purchased_scripts": []
        }
    return vip_users[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_data = get_user(user.id)
    
    if user.username:
        u_data["username"] = user.username

    if not u_data["registered"]:
        text = "📝 **Для покупки скрипта отправьте свой юзернейм с символом '@' (например: @sots12):**"
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown")
        return

    keyboard = [
        [InlineKeyboardButton("🎯 Контуры — 200 Stars", callback_data="script_kontur")],
        [InlineKeyboardButton("⚡ 2v1 — 200 Stars", callback_data="script_2v1")],
        [InlineKeyboardButton("🔥 Опр прайс — 100 Stars", callback_data="script_opr")],
        [InlineKeyboardButton("👤 Мои скрипты", callback_data="my_profile")]
    ]

    text = "спасибо за подписку! Выберите скрипт, который вам нужен:"

    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    u_data = get_user(user.id)
    if user.username:
        u_data["username"] = user.username
        
    data = query.data

    if not u_data["registered"]:
        await start(update, context)
        return

    if data == "script_kontur":
        await context.bot.send_invoice(
            chat_id=user.id,
            title="Контуры (200 Stars)",
            description="Канал скрипта Контуры для Standoff 2",
            payload="pay_script_kontur",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Контуры", 200)]
        )

    elif data == "script_2v1":
        await context.bot.send_invoice(
            chat_id=user.id,
            title="2v1 (200 Stars)",
            description="Канал скрипта 2v1 для Standoff 2",
            payload="pay_script_2v1",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("2v1", 200)]
        )

    elif data == "script_opr":
        await context.bot.send_invoice(
            chat_id=user.id,
            title="Опр прайс (100 Stars)",
            description="Канал скрипта Опр прайс для Standoff 2",
            payload="pay_script_opr",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Опр прайс", 100)]
        )

    elif data == "my_profile":
        text = f"👤 Юзернейм: {u_data['name']}\n\n📦 **Купленные каналы скриптов:**\n"
        kb = [[InlineKeyboardButton("🔙 Назад", callback_data="back_home")]]
        
        if not u_data["purchased_scripts"]:
            text += "Вы еще не купили ни одного скрипта."
        else:
            for s in u_data["purchased_scripts"]:
                if "Контуры" in s:
                    kb.insert(0, [InlineKeyboardButton("🎯 Перейти в канал Контуры", url=CHANNEL_KONTUR)])
                elif "2v1" in s:
                    kb.insert(0, [InlineKeyboardButton("⚡ Перейти в канал 2v1", url=CHANNEL_2V1)])
                elif "Опр" in s:
                    kb.insert(0, [InlineKeyboardButton("🔥 Перейти в канал Опр прайс", url=CHANNEL_OPR)])

        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "back_home":
        await start(update, context)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_data = get_user(user.id)
    if user.username:
        u_data["username"] = user.username

    if not u_data["registered"]:
        text_input = update.message.text.strip()

        if not text_input.startswith("@"):
            await update.message.reply_text("❌ Неверный юзернейм! Пожалуйста, отправьте заново, начиная с '@' (например: @sots12):")
            return

        u_data["name"] = text_input
        u_data["registered"] = True

        await update.message.reply_text("🎉 Поздравляем, вы успешно зарегистрировались!")

        for uid, udat in vip_users.items():
            if udat.get("username", "").lower() == ADMIN_USERNAME.lower():
                try:
                    await context.bot.send_message(
                        chat_id=uid,
                        text=f"🚨 **Новый пользователь зарегистрировался!**\n\n👤 Юзернейм: {text_input}\n🆔 ID: {user.id}",
                        parse_mode="Markdown"
                    )
                except:
                    pass

        await start(update, context)

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload in ["pay_script_kontur", "pay_script_2v1", "pay_script_opr"]:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="❌ Оплата не прошла!")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_data = get_user(user.id)
    
    payload = update.message.successful_payment.invoice_payload
    script_name = ""
    channel_url = ""
    
    if payload == "pay_script_kontur":
        script_name = "Контуры (200 Stars)"
        channel_url = CHANNEL_KONTUR
    elif payload == "pay_script_2v1":
        script_name = "2v1 (200 Stars)"
        channel_url = CHANNEL_2V1
    elif payload == "pay_script_opr":
        script_name = "Опр прайс (100 Stars)"
        channel_url = CHANNEL_OPR

    if script_name not in u_data["purchased_scripts"]:
        u_data["purchased_scripts"].append(script_name)

    for uid, udat in vip_users.items():
        if udat.get("username", "").lower() == ADMIN_USERNAME.lower():
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=f"💰 **Куплен скрипт:**\n\n👤 Юзернейм: {u_data['name']}\n📦 Скрипт: {script_name}",
                    parse_mode="Markdown"
                )
            except:
                pass

    kb = [[InlineKeyboardButton(f"🚀 Перейти в канал {script_name}", url=channel_url)]]
    await update.message.reply_text(
        f"🎉 **Поздравляем! Оплата прошла успешно.**\n\n"
        f"Вы оплатили '{script_name}'.\n"
        f"Пожалуйста, перейдите в специальный канал по кнопке ниже:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    # Flask serverini fonda ishga tushiramiz (Render port talabini qondirish uchun)
    keep_alive()

    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    print("Standoff 2 Skript Shop Bot ishga tushdi!")
    application.run_polling()
