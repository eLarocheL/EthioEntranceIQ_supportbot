import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import re
import threading
import time
import schedule
from flask import Flask

# ==========================================
# 1. CONFIGURATION & FLASK DUMMY SERVER
# ==========================================
BOT_TOKEN = os.environ.get('SUPPORT_BOT_TOKEN')
ADMIN_ID = 7365557461  # Replace with your Telegram ID
CHANNEL_ID = "@Ethio_Entrance_IQ" # Your Telegram Channel
bot = telebot.TeleBot(BOT_TOKEN)

# Dummy Flask App to keep Render service active
app = Flask(__name__)

@app.route('/')
def home():
    return "EthioEntranceIQ Support Bot is awake!"

# ==========================================
# 2. KEYBOARDS & CONSTANTS (Option 1 Aesthetic)
# ==========================================
def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎓 የግል አስጠኚ እፈልጋለሁ", callback_data="menu_tutor"))
    markup.row(InlineKeyboardButton("💬 አስጠኚ ለመሆን", callback_data="menu_human"))
    markup.row(
        InlineKeyboardButton("⚡ Quick FAQs", callback_data="menu_faq"),
        InlineKeyboardButton("🎧 Support Team", callback_data="menu_bug")
    )
    return markup

def get_restart_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("➕ Start New Chat", callback_data="menu_start"))
    return markup

MAIN_MENU_TEXT = (
    "⚡ <b>EthioEntranceIQ Support</b>\n\n"
    "Select an option below for immediate routing:"
)

# ==========================================
# 3. AUTOMATED SELF-SERVICE MENU
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        MAIN_MENU_TEXT, 
        reply_markup=get_main_keyboard(), 
        parse_mode="HTML"
    )

# ==========================================
# 4. HANDLE AUTOMATED BUTTON CLICKS
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu_clicks(call):
    # Acknowledge the button click to stop the loading animation on the user's screen
    bot.answer_callback_query(call.id)
    
    if call.data == "menu_start":
        bot.send_message(
            call.message.chat.id, 
            MAIN_MENU_TEXT, 
            reply_markup=get_main_keyboard(), 
            parse_mode="HTML"
        )
        
    elif call.data == "menu_faq":
        faq_text = (
            "⚡ <b>Quick FAQs</b>\n\n"
            "• <b>How to access Entrance Exam?</b> Use our main bot @EthioEntranceIQ_bot.\n"
            "• <b>Payment methods?</b> We accept telebirr and direct bank transfers."
        )
        bot.send_message(call.message.chat.id, faq_text, parse_mode="HTML", reply_markup=get_main_keyboard())
        
    elif call.data == "menu_tutor":
        tutor_text = (
            "🎓 <b>Tutor Matching</b>\n\n"
            "Please reply to this message with the following details so we can find your ideal tutor:\n\n"
            "🏫 <b>Grade Level:</b> \n"
            "📍 <b>Address:</b> "
        )
        bot.send_message(call.message.chat.id, tutor_text, parse_mode="HTML")
        
    elif call.data == "menu_bug":
        bot.send_message(call.message.chat.id, "🎧 <b>Support Team</b>\n\n How can we help you?", parse_mode="HTML")
        
    elif call.data == "menu_human":
        bot.send_message(call.message.chat.id, "💬 <b>Connecting to Support...</b>\n\nPlease type your message below. An admin will respond shortly.", parse_mode="HTML")

# ==========================================
# 5. ADMIN COMMAND: CLOSE TICKET
# ==========================================
@bot.message_handler(commands=['close'])
def close_ticket(message):
    # Only allow the admin to use this command
    if message.chat.id != ADMIN_ID:
        return
        
    try:
        # Extract the user ID from the command (e.g., /close 123456789)
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: `/close <user_chat_id>`", parse_mode="Markdown")
            return
            
        target_user_id = int(parts[1])
        
        close_text = (
            "✅ <b>Ticket Closed</b>\n\n"
            "Your request has been resolved. If you need anything else, feel free to start a new chat anytime."
        )
        
        # Send closing message to the user with the restart button
        bot.send_message(
            target_user_id, 
            close_text, 
            parse_mode="HTML", 
            reply_markup=get_restart_keyboard()
        )
        
        # Confirm action to the admin
        bot.reply_to(message, f"✅ Ticket for user `{target_user_id}` closed successfully.", parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Failed to close chat: {str(e)}")

# ==========================================
# 6. ZERO-FRICTION ADMIN REPLIES
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
# 7. AUTOMATED TICKET ROUTING (USER -> ADMIN)
# ==========================================
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID and not message.text.startswith('/'))
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
# 8. DAILY CHANNEL POST SCHEDULER (NEW)
# ==========================================
def send_daily_post():
    """The message that gets posted to the channel every day."""
    try:
        daily_message = (
            "🚀 <b>Need Help Passing the Entrance Exam?</b>\n\n"
            "Our Support Team is online and ready to assist you!\n\n"
            "✅ Request a Personal Tutor\n"
            "✅ Get Help with Quizzes\n"
            "✅ Talk to a Human Agent\n\n"
            "👇 Click below to start a chat with our Support Bot!"
        )
        
        # Adding a button that links directly to your support bot
        markup = InlineKeyboardMarkup()
        # REPLACE 'YourSupportBotUsername' with the actual username of your support bot!
        markup.add(InlineKeyboardButton("💬 Contact Support", url="https://t.me/YourSupportBotUsername?start=start"))
        
        bot.send_message(CHANNEL_ID, daily_message, parse_mode="HTML", reply_markup=markup)
        print("✅ Daily channel post sent successfully!")
    except Exception as e:
        print(f"⚠️ Failed to send daily post: {e}")

def run_scheduler():
    """Runs continuously in the background to check the time."""
    # 09:00 UTC is exactly 12:00 PM (Noon) EAT.
    schedule.every().day.at("09:00").do(send_daily_post) 
    
    while True:
        schedule.run_pending()
        time.sleep(60) # Check every minute

# ==========================================
# 9. THREADING EXECUTION (BOT + FLASK + SCHEDULER)
# ==========================================
def run_bot():
    print("Automated Support Bot is running...")
    bot.infinity_polling()

if __name__ == "__main__":
    # Start the Telegram bot loop in a background thread
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Start the Daily Scheduler loop
    threading.Thread(target=run_scheduler, daemon=True).start()
    
    # Start the Flask web server listening on the port provided by Render
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
