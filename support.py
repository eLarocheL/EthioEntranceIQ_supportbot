import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import re
import threading
from flask import Flask

# ==========================================
# 1. CONFIGURATION & FLASK DUMMY SERVER
# ==========================================
BOT_TOKEN = os.environ.get('SUPPORT_BOT_TOKEN')
ADMIN_ID = 7365557461  # Replace with your Telegram ID
bot = telebot.TeleBot(BOT_TOKEN)

# Dummy Flask App to keep Render service active
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is awake!"

# ==========================================
# 2. AUTOMATED SELF-SERVICE MENU
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Build an interactive Inline Keyboard menu
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("👨‍🏫 Request Personal Tutor", callback_data="menu_tutor"))
    markup.row(
        InlineKeyboardButton("🐛 Report Bug", callback_data="menu_bug"),
        InlineKeyboardButton("❓ FAQs", callback_data="menu_faq")
    )
    markup.row(InlineKeyboardButton("💬 Talk to a Human", callback_data="menu_human"))
    
    welcome_text = (
        "👋 <b>Welcome to EthioEntranceIQ Support!</b>\n\n"
        "I am your automated assistant. Please choose an option below so I can route your request instantly:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="HTML")

# ==========================================
# 3. HANDLE AUTOMATED BUTTON CLICKS
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu_clicks(call):
    # Acknowledge the button click to stop the loading animation on the user's screen
    bot.answer_callback_query(call.id)
    
    if call.data == "menu_faq":
        faq_text = (
            "❓ <b>Frequently Asked Questions</b>\n\n"
            "<b>Q: How do I take a quiz?</b>\n"
            "A: Go to our main bot and send /start.\n\n"
            "<b>Q: Is the bot free?</b>\n"
            "A: Yes, all standard quizzes are currently free!"
        )
        bot.send_message(call.message.chat.id, faq_text, parse_mode="HTML")
        
    elif call.data == "menu_tutor":
        tutor_text = (
            "👨‍🏫 <b>Tutor Request</b>\n\n"
            "Please type your Grade, Subject, and what you need help with. "
            "I will automatically forward it to our tutor matching team!"
        )
        bot.send_message(call.message.chat.id, tutor_text, parse_mode="HTML")
        
    elif call.data == "menu_bug":
        bot.send_message(call.message.chat.id, "🐛 Please describe the bug you found, and I will create an automated ticket for the developers.")
        
    elif call.data == "menu_human":
        bot.send_message(call.message.chat.id, "💬 Please type your message below. An admin will reply to you shortly.")

# ==========================================
# 4. ZERO-FRICTION ADMIN REPLIES
# ==========================================
# Listening for admin replies natively in Telegram
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message is not None)
def automated_admin_reply(message):
    try:
        # Extract the hidden User ID from the original message text
        original_text = message.reply_to_message.text
        
        # Regex to match the embedded ID
        match = re.search(r'ID:\s*(\d+)', original_text)
        
        if match:
            user_id = int(match.group(1))
            admin_response = message.text
            
            # Route text back to user
            bot.send_message(user_id, f"👨‍💻 <b>Support Team:</b>\n\n{admin_response}", parse_mode="HTML")
            bot.reply_to(message, "✅ <i>Reply instantly routed to user.</i>", parse_mode="HTML")
        else:
            bot.reply_to(message, "⚠️ Could not detect User ID. Are you replying to a formatted support ticket?")
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error sending reply: {e}")

# ==========================================
# 5. AUTOMATED TICKET ROUTING (USER -> ADMIN)
# ==========================================
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID)
def forward_to_admin(message):
    ticket_format = (
        f"🚨 <b>NEW SUPPORT TICKET</b>\n"
        f"<b>From:</b> {message.from_user.first_name}\n"
        f"<b>ID:</b> {message.chat.id}\n"
        f"<b>Username:</b> @{message.from_user.username}\n\n"
        f"<b>Message:</b>\n{message.text}"
    )
    
    # Send ticket to admin
    bot.send_message(ADMIN_ID, ticket_format, parse_mode="HTML")
    
    # Confirmation to user
    bot.reply_to(message, "✅ Your message has been logged and sent to our team. We will notify you here when we reply.")

# ==========================================
# 6. THREADING EXECUTION (BOT + FLASK)
# ==========================================
def run_bot():
    print("Automated Support Bot is running...")
    bot.infinity_polling()

if __name__ == "__main__":
    # Start the Telegram bot loop in a background thread
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Start the Flask web server listening on the port provided by Render
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
