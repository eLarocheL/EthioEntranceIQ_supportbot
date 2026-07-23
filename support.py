import logging
import os
from threading import Thread
from flask import Flask

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---------------------------------------------------------------------------
# 1. FLASK DUMMY SERVER (For Render Background Worker Keep-Alive)
# ---------------------------------------------------------------------------
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "EthioEntranceIQ Support Bot is running smoothly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ---------------------------------------------------------------------------
# 2. LOGGING CONFIGURATION
# ---------------------------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "YOUR_ADMIN_CHAT_ID_HERE")

# ---------------------------------------------------------------------------
# 3. INTERFACE CONSTANTS (Option 1 Aesthetic)
# ---------------------------------------------------------------------------
MAIN_MENU_TEXT = (
    "⚡ <b>EthioEntranceIQ Support</b>\n\n"
    "Select an option below for immediate routing:"
)

TUTOR_PROMPT_TEXT = (
    "🎓 <b>Tutor Matching</b>\n\n"
    "Please reply to this message with the following details so we can find your ideal tutor:\n\n"
    "🏫 <b>Grade Level:</b> \n"
    "📍 <b>Address:</b> "
)

CHAT_CLOSED_TEXT = (
    "✅ <b>Ticket Closed</b>\n\n"
    "Your request has been resolved. If you need anything else, feel free to start a new chat anytime."
)

# Keyboards
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 Request Tutor", callback_data="req_tutor")],
        [InlineKeyboardButton("💬 Talk to Admin", callback_data="talk_admin")],
        [
            InlineKeyboardButton("⚡ Quick FAQs", callback_data="faqs"),
            InlineKeyboardButton("🐞 Report Bug", callback_data="report_bug")
        ]
    ])

def get_restart_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Start New Chat", callback_data="main_menu")]
    ])

# ---------------------------------------------------------------------------
# 4. BOT HANDLERS
# ---------------------------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the main sharp Option 1 menu."""
    if update.message:
        await update.message.reply_text(
            MAIN_MENU_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks."""
    query = update.callback_query
    await query.answer()

    if query.data == "main_menu":
        await query.message.reply_text(
            MAIN_MENU_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    elif query.data == "req_tutor":
        await query.message.reply_text(
            TUTOR_PROMPT_TEXT,
            parse_mode="HTML"
        )
    elif query.data == "talk_admin":
        await query.message.reply_text(
            "💬 <b>Connecting to Support...</b>\n\n"
            "Please type your message below. An admin will respond shortly.",
            parse_mode="HTML"
        )
    elif query.data == "faqs":
        await query.message.reply_text(
            "⚡ <b>Quick FAQs</b>\n\n"
            "• How to access quizzes? Use our main bot @EthioEntranceIQ_bot.\n"
            "• Payment methods? We accept telebirr and direct bank transfers.",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    elif query.data == "report_bug":
        await query.message.reply_text(
            "🐞 <b>Report Bug</b>\n\n"
            "Please describe the error or bug you encountered in detail.",
            parse_mode="HTML"
        )

async def close_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command to close a user's ticket: /close <user_chat_id>
    Sends the user the close message and a 'Start New Chat' button.
    """
    if str(update.effective_user.id) != str(ADMIN_CHAT_ID):
        return

    if not context.args:
        await update.message.reply_text("Usage: `/close <user_chat_id>`", parse_mode="Markdown")
        return

    target_user_id = context.args[0]
    
    try:
        # Send closing notice to user
        await context.bot.send_message(
            chat_id=target_user_id,
            text=CHAT_CLOSED_TEXT,
            parse_mode="HTML",
            reply_markup=get_restart_keyboard()
        )
        # Confirm to admin
        await update.message.reply_text(f"✅ Ticket for user `{target_user_id}` closed successfully.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to close chat: {str(e)}")

# ---------------------------------------------------------------------------
# 5. MAIN APPLICATION
# ---------------------------------------------------------------------------
def main():
    # Start Flask Web Server in a parallel thread
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Build Telegram Bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("close", close_chat_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Run Bot
    app.run_polling()

if __name__ == "__main__":
    main()
