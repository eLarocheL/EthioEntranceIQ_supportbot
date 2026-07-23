import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import re

# ==========================================
# 1. CONFIGURATION
# ==========================================
BOT_TOKEN = os.environ.get('SUPPORT_BOT_TOKEN')
ADMIN_ID = 123456789  # Replace with your Telegram ID
bot = telebot.TeleBot(BOT_TOKEN)

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
# This listens for YOU replying natively to a forwarded message in your Telegram app
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message is not None)
def automated_admin_reply(message):
    try:
        # The bot reads the original message you replied to and extracts the hidden User ID
        original_text = message.reply_to_message.text
        
        # We use a Regular Expression (re) to find the ID number we embedded earlier
        match = re.search(r'ID:\s*(\d+)', original_text)
        
        if match:
            user_id = int(match.group(1))
            admin_response = message.text
            
            # Bot automatically routes your text back to the student
            bot.send_message(user_id, f"👨‍💻 <b>Support Team:</b>\n\n{admin_response}", parse_mode="HTML")
            bot.reply_to(message, "✅ <i>Reply instantly routed to user.</i>", parse_mode="HTML")
        else:
            bot.reply_to(message, "⚠️ Could not detect User ID. Are you replying to a formatted support ticket?")
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error sending reply: {e}")

# ==========================================
# 5. AUTOMATED TICKET ROUTING (USER -> ADMIN)
# ==========================================
# Catches all text messages from users and formats them into a "Ticket" for you
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID)
def forward_to_admin(message):
    # This specific format embeds the "ID: 123456" so the bot can extract it later
    ticket_format = (
        f"🚨 <b>NEW SUPPORT TICKET</b>\n"
        f"<b>From:</b> {message.from_user.first_name}\n"
        f"<b>ID:</b> {message.chat.id}\n"
        f"<b>Username:</b> @{message.from_user.username}\n\n"
        f"<b>Message:</b>\n{message.text}"
    )
    
    # Sends the neat ticket to you
    bot.send_message(ADMIN_ID, ticket_format, parse_mode="HTML")
    
    # Sends an automated confirmation to the user
    bot.reply_to(message, "✅ Your message has been logged and sent to our team. We will notify you here when we reply.")

# ==========================================
if __name__ == "__main__":
    print("Automated Support Bot is running...")
    bot.infinity_polling()
