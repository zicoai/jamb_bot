import logging
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import init_db, get_progress, update_progress

# Load questions
with open("questions.json", encoding="utf-8") as f:
    QUESTIONS = json.load(f)
    QUESTION_IDS = list(range(len(QUESTIONS)))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to JAMB CBT Quiz Bot! 🚀\n\n"
        "Send /quiz to start practicing with real past questions.\n"
        "No repeats • Full explanations • Proper scoring"
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    progress = get_progress(user_id)
    
    available = [i for i in QUESTION_IDS if str(i) not in progress["asked"]]
    if not available:
        await update.message.reply_text("You've finished all questions! Respect 🔥\nStart again with /quiz")
        progress = {"asked": set(), "correct": 0, "total": 0}
        update_progress(user_id, progress["asked"], 0, 0)
        available = QUESTION_IDS[:]

    q_id = random.choice(available)
    question = QUESTIONS[q_id]

    buttons = []
    for opt in question["options"]:
        buttons.append([InlineKeyboardButton(opt, callback_data=f"{q_id}|{opt}")])
    buttons.append([InlineKeyboardButton("Next Question ➡️", callback_data=f"NEXT|{q_id}")])

    keyboard = InlineKeyboardMarkup(buttons)
    
    await update.message.reply_text(
        f"Question {progress['total'] + 1}\n\n{question['question']}",
        reply_markup=keyboard
    )
    
    # Update asked list immediately
    progress["asked"].add(str(q_id))
    progress["total"] += 1
    update_progress(user_id, progress["asked"], progress["correct"], progress["total"])

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id

    if data.startswith("NEXT|"):
        # Just send new question
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("Loading next question...")
        await quiz(query, context)
        return

    q_id_str, chosen = data.split("|", 1)
    q_id = int(q_id_str)
    question = QUESTIONS[q_id]
    correct_answer = question["answer"]

    progress = get_progress(user_id)
    is_correct = chosen == correct_answer
    if is_correct:
        progress["correct"] += 1
        update_progress(user_id, progress["asked"], progress["correct"], progress["total"])

    # Feedback
    emoji = "✅" if is_correct else "❌"
    text = f"{emoji} <b>{chosen}</b>\n\n"
    text += f"Correct Answer: <b>{correct_answer}</b>\n\n"
    text += f"<i>{question['explanation']}</i>\n\n"
    text += f"Score: {progress['correct']}/{progress['total']} "

    if progress['total'] % 50 == 0:
        percent = (progress['correct']/progress['total'])*100
        text += f"({percent:.1f}%) 🔥\n\n<i>Keep going! Send /quiz for the next one</i>"

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Next Question ➡️", callback_data=f"NEXT|{q_id}")]])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

def main():
    init_db()
    app = Application.builder().token("8432955575:AAE8o88yd9ndR2aCgwezWz_Vy9iJkZWtW9E").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()

if name == 'main':
    main()
