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

# Fixed for Python 3.13 (use levelname, not level)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
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
    q = QUESTIONS[q_id]

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(opt, callback_data=f"{q_id}|{opt}")] for opt in q["options"]] +
        [[InlineKeyboardButton("Next Question", callback_data=f"NEXT|{q_id}")]]
    )

    await update.message.reply_text(
        f"Question {progress['total'] + 1}\n\n{q['question']}",
        reply_markup=keyboard
    )

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
        await quiz(query, context)  # trigger next question
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

    emoji = "Correct" if is_correct else "Wrong"
    text = f"{emoji} <b>{chosen}</b>\n\n"
    text += f"Correct Answer: <b>{correct_answer}</b>\n\n"
    text += f"<i>{q['explanation']}</i>\n\n"
    text += f"Score: {progress['correct']}/{progress['total']}"

    if progress["total"] % 50 == 0:
        percent = (progress["correct"] / progress["total"]) * 100
        text += f" ({percent:.1f}%) Keep going!"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Next Question", callback_data=f"NEXT|{q_id}")]
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")

# ========================= MAIN =========================
def main():
    logger.info("Initializing database...")
    init_db()

    logger.info("Building bot application...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Removing any old webhook...")
    import asyncio
    asyncio.run(app.bot.delete_webhook(drop_pending_updates=True))

    logger.info("Bot is now LIVE – starting polling...")
    app.run_polling(drop_pending_updates=True)  # blocks forever, keeps bot alive

if __name__ == "__main__":
    main()