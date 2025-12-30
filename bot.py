import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
REQUIRED_CHAT = os.getenv("REQUIRED_CHAT", "@HoneyBdisigne").strip()

def is_ok_status(status):
    return status in ("creator", "administrator", "member")

def subscribe_keyboard():
    if REQUIRED_CHAT.startswith("@"):
        url = "https://t.me/" + REQUIRED_CHAT[1:]
    else:
        url = REQUIRED_CHAT
    kb = [
        [InlineKeyboardButton("📌 Вступить в группу", url=url)],
        [InlineKeyboardButton("✅ Я вступил — проверить", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(kb)

async def safe_reply(update: Update, text: str, reply_markup=None):
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

async def ensure_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        await safe_reply(update, "⚠️ Не вижу пользователя. Напиши /start ещё раз.")
        return False

    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHAT, user_id=user.id)
        status = getattr(member, "status", "")
        if is_ok_status(status):
            return True
    except Exception:
        logging.exception("get_chat_member failed")
        await safe_reply(update,
            "⚠️ Не смог проверить вступление.\n"
            "Проверь: бот добавлен в группу и лучше сделан админом.\n"
            "И @username группы указан верно."
        )
        return False

    await safe_reply(update,
        "🔒 Доступ к боту только для участников группы.\n"
        "1) Вступи в группу\n"
        "2) Нажми «Проверить»",
        reply_markup=subscribe_keyboard()
    )
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok = await ensure_member(update, context)
    if not ok:
        return
    await update.message.reply_text("✅ Доступ открыт. Напиши любое сообщение.")

async def on_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ok = await ensure_member(update, context)
    if not ok:
        return
    await q.message.reply_text("✅ Проверка пройдена. Теперь бот открыт.")

async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok = await ensure_member(update, context)
    if not ok:
        return
    await update.message.reply_text("🔥 Бот работает. (Дальше добавим команды.)")

def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is empty")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_check, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.ALL, any_message))
    app.run_polling()

if __name__ == "__main__":
    main()

