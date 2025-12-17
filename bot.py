import os
import json
import random
import logging
import nest_asyncio
import threading  # Added for running polling in a thread
from flask import Flask  # Added for dummy web server
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import init_db, get_progress, update_progress

# Apply the patch for nested event loops
nest_asyncio.apply()

# ========================= CONFIG =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_TOKEN in environment variables!")

with open("questions.json", encoding="utf-8") as f:
    QUESTIONS = json.load(f)
    # Assume keys are strings like "0", "1", etc. Convert to ints for QUESTION_IDS
    QUESTION_IDS = [int(k) for k in sorted(QUESTIONS.keys(), key=int)]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ========================= HANDLERS =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to JAMB CBT Quiz Bot!\n\n"
        "Send /quiz to start practicing real past questions.\n"
        "No repeats • Full explanations • Proper scoring"
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    progress = get_progress(user_id)
    available = [i for i in QUESTION_IDS if str(i) not in progress["asked"]]
    if not available:
        await update.message.reply_text("You've finished all questions! Starting new round…")
        progress = {"asked": set(), "correct": 0, "total": 0}
        update_progress(user_id, progress["asked"], 0, 0)
        available = QUESTION_IDS[:]
    q_id = random.choice(available)
    # Access with str(q_id) to match potential string keys in QUESTIONS
    q = QUESTIONS[str(q_id)]
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(opt, callback_data=f"{q_id}|{opt}")] for opt in q["options"]] +
        [[InlineKeyboardButton("Next Question", callback_data=f"NEXT|{q_id}")]]
    )
    await update.message.reply_text(f"Question {progress['total'] + 1}\n\n{q['question']}", reply_markup=keyboard)
    progress["asked"].add(str(q_id))
    progress["total"] += 1
    update_progress(user_id, progress["asked"], progress["correct"], progress["total"])

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if data.startswith("NEXT|"):
        await query.edit_message_reply_markup(reply_markup=None)
        await quiz(query, context)
        return
    q_id_str, chosen = data.split("|", 1)
    q_id = int(q_id_str)
    # Access with str(q_id) to match potential string keys
    q = QUESTIONS[str(q_id)]
    progress = get_progress(user_id)
    is_correct = chosen == q["answer"]
    if is_correct:
        progress["correct"] += 1
        update_progress(user_id, progress["asked"], progress["correct"], progress["total"])
    emoji = "Correct" if is_correct else "Wrong"
    text = f"{emoji} <b>{chosen}</b>\n\nCorrect Answer: <b>{q['answer']}</b>\n\n<i>{q['explanation']}</i>\n\nScore: {progress['correct']}/{progress['total']}"
    if progress["total"] % 50 == 0:
        percent = (progress["correct"] / progress["total"]) * 100
        text += f" ({percent:.1f}%) Keep going!"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Next Question", callback_data=f"NEXT|{q_id_str}")]])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")

# Global error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}")
    if update and hasattr(update, 'effective_chat'):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="An error occurred. Please try again."
        )

# ========================= DUMMY WEB SERVER =========================
# This binds to $PORT so Render doesn't timeout the deployment
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

# ========================= MAIN =========================
def run_bot():
    logger.info("Initializing database...")
    init_db()
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("quiz", quiz))
    bot_app.add_handler(CallbackQueryHandler(button_handler))
    bot_app.add_error_handler(error_handler)
    logger.info("Bot starting polling...")
    bot_app.run_polling(drop_pending_updates=True)

def main():
    # Run bot polling in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Run the dummy Flask server on the main thread (binds to port)
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting dummy web server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()