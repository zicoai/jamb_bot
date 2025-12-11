import os
import json
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import init_db, get_progress, update_progress

# ========================= CONFIG =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_TOKEN in environment variables!")

with open("questions.json", encoding="utf-8") as f:
    QUESTIONS = json.load(f)
    QUESTION_IDS = list(range(len(QUESTIONS)))

logging.basicConfig(format="%(asctime)s - %(name)s - %(level)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================= HANDLERS =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to JAMB CBT Quiz Bot!\nSend /quiz to begin")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    progress = get_progress(user_id)
    available = [i for i in QUESTION_IDS if str(i) not in progress["asked"]]
    if not available:
        await update.message.reply_text("All questions done! Starting new round…")
        progress = {"asked": set(), "correct": 0, "total": 0}
        update_progress(user_id, progress["asked"], 0, 0)
        available = QUESTION_IDS[:]
    q_id = random.choice(available)
    q = QUESTIONS[q_id]
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(opt, callback_data=f"{q_id}|{opt}")] for opt in q["options"]] +
        [[InlineKeyboardButton("Next Question", callback_data=f"NEXT|{q_id}")]]
    )
    await update.message.reply_text(f"Question {progress['total']+1}\n\n{q['question']}", reply_markup=keyboard)
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
    q = QUESTIONS[q_id]
    correct_answer = q["answer"]
    progress = get_progress(user_id)
    is_correct = chosen == correct_answer
    if is_correct:
        progress["correct"] += 1
        update_progress(user_id, progress["asked"], progress["correct"], progress["total"])
    emoji = "✅" if is_correct else "❌"
    text = f"{emoji} <b>{chosen}</b>\n\nCorrect Answer: <b>{correct_answer}</b>\n\n<i>{q['explanation']}</i>\n\nScore: {progress['correct']}/{progress['total']}"
    if progress["total"] % 50 == 0:
        percent = (progress["correct"] / progress["total"]) * 100
        text += f"\n({percent:.1f}%) 🔥 Keep going!"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Next Question ➡️", callback_data=f"NEXT|{q_id}")]])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")

# ========================= MAIN =========================
def main():
    logger.info("Initializing database...")
    init_db()

    logger.info("Building application...")
    app = Application.builder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Deleting any old webhook...")
    # Run async setup synchronously
    import asyncio
    asyncio.run(app.bot.delete_webhook(drop_pending_updates=True))

    logger.info("Starting polling...")
    # NO await here - run_polling is synchronous and blocks until shutdown
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()