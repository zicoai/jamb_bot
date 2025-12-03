from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# 10 JAMB questions
questions = [
    {"question": "1. Which of the following is NOT a primary color?", 
     "options": ["A", "B", "C", "D"], 
     "text": ["A) Red", "B) Blue", "C) Green", "D) Yellow"],
     "answer": "C"},

    {"question": "2. What is the chemical symbol for Sodium?", 
     "options": ["A", "B", "C", "D"], 
     "text": ["A) Na", "B) S", "C) So", "D) N"],
     "answer": "A"},

    {"question": "3. Who wrote 'Things Fall Apart'?", 
     "options": ["A", "B", "C", "D"], 
     "text": ["A) Chinua Achebe", "B) Wole Soyinka", "C) Ngugi wa Thiong'o", "D) Chimamanda Adichie"],
     "answer": "A"},

    {"question": "4. What is the value of π (Pi) approximately?", 
     "options": ["A", "B", "C", "D"], 
     "text": ["A) 2.14", "B) 3.14", "C) 3.41", "D) 2.41"],
     "answer": "B"},

    {"question": "5. Which gas do humans inhale for respiration?", 
     "options": ["A", "B", "C", "D"], 
     "text": ["A) Carbon dioxide", "B) Oxygen", "C) Nitrogen", "D) Hydrogen"],
     "answer": "B"},

    {"question": "6. Who discovered penicillin?", 
     "options": ["A", "B", "C", "D"], 
     "text": ["A) Louis Pasteur", "B) Alexander Fleming", "C) Marie Curie", "D) Gregor Mendel"],
     "answer": "B"},

    {"question": "7. What is the largest planet in our solar system?", 
     "options": ["A", "B", "C", "D"], 
     "text": ["A) Earth", "B) Saturn", "C) Jupiter", "D) Mars"],
     "answer": "C"},

    {"question": "8. Which process converts glucose into energy in cells?", 
     "options": ["A", "B", "C", "D"], 
     "text": ["A) Photosynthesis", "B) Respiration", "C) Fermentation", "D) Digestion"],
     "answer": "B"},

    {"question": "9. Which organ produces insulin?", 
     "options": ["A", "B", "C", "D"], 
     "text": ["A) Liver", "B) Pancreas", "C) Kidney", "D) Heart"],
     "answer": "B"},

    {"question": "10. What is the boiling point of water at sea level?", 
     "options": ["A", "B", "C", "D"], 
     "text": ["A) 90°C", "B) 95°C", "C) 100°C", "D) 105°C"],
     "answer": "C"},
]

# Track user progress
user_state = {}

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_state[user_id] = 0
    await send_question(update, context, user_id)

# Send a question
async def send_question(update, context, user_id):
    index = user_state[user_id]

    if index >= len(questions):
        await context.bot.send_message(chat_id=user_id, text="🎉 You have completed all the questions!")
        return

    q = questions[index]

    # Build option buttons
    keyboard = [[InlineKeyboardButton(q["text"][i], callback_data=f"answer_{q['options'][i]}")] 
                for i in range(4)]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send question + buttons
    await context.bot.send_message(
        chat_id=user_id, 
        text=f"{q['question']}\n\n" + "\n".join(q["text"]),
        reply_markup=reply_markup
    )

# Handle button clicks
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.message.chat_id
    data = query.data  # e.g. answer_A

    index = user_state[user_id]
    correct_answer = questions[index]["answer"]

    if data.startswith("answer_"):
        selected = data.split("_")[1]

        # Check answer
        if selected == correct_answer:
            response = "✅ Correct!"
        else:
            response = f"❌ Wrong! Correct answer is {correct_answer}"

        # Send feedback + Next button
        keyboard = [[InlineKeyboardButton("Next Question ▶️", callback_data="next")]]
        await query.edit_message_text(
            text=query.message.text + f"\n\n{response}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Next question
    elif data == "next":
        user_state[user_id] += 1
        await send_question(update, context, user_id)


# Run the bot
if __name__ == "__main__":
    TOKEN = "8432955575:AAE8o88yd9ndR2aCgwezWz_Vy9iJkZWtW9E"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot is running...")
    app.run_polling()
