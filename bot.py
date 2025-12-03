import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Load questions from JSON
with open("questions.json", "r") as f:
    question_bank = json.load(f)

# Track user progress
user_state = {}  # user_id: current_question_index

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = 0
    await send_question(update, context, user_id)

# Send question
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    index = user_state.get(user_id, 0)
    
    if index >= len(question_bank):
        await context.bot.send_message(chat_id=user_id, text="🎉 You've finished all questions!")
        return

    q = question_bank[index]
    options = q["options"]
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=opt)] for opt in options
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # If this is a callback query, edit the message
    if update.callback_query:
        await update.callback_query.message.edit_text(q["question"], reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=user_id, text=q["question"], reply_markup=reply_markup)

# Handle answer selection
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    index = user_state.get(user_id, 0)
    correct_answer = question_bank[index]["answer"]

    if query.data == correct_answer:
        await query.answer("✅ Correct!")
    else:
        await query.answer(f"❌ Wrong! Correct answer: {correct_answer}")

    # Move to next question
    user_state[user_id] = index + 1
    await send_question(update, context, user_id)

# Main function
if __name__ == "__main__":
    TOKEN = "8432955575:AAE8o88yd9ndR2aCgwezWz_Vy9iJkZWtW9E"  # replace with your bot token

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot is running...")
    app.run_polling()
