import os
import random
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ----------------------------
# BOT TOKEN (from environment variable)
# ----------------------------
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

# ----------------------------
# LOAD QUESTIONS
# ----------------------------
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# ----------------------------
# TRACK LAST QUESTION FOR EACH USER
# ----------------------------
user_last_question = {}

# ----------------------------
# COMMAND HANDLERS
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm your JAMB quiz bot.\nSend /quiz to get a question."
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = random.choice(questions)
    user_last_question[update.effective_chat.id] = q
    await update.message.reply_text(f"Q: {q['question']}\n\nSend /answer to see the answer.")

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_q = user_last_question.get(update.effective_chat.id)
    if not last_q:
        await update.message.reply_text("You haven't asked a question yet. Send /quiz first.")
    else:
        await update.message.reply_text(f"A: {last_q['answer']}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /quiz to get a question or /answer to see the answer.")

# ----------------------------
# BUILD APP
# ----------------------------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("quiz", quiz))
app.add_handler(CommandHandler("answer", answer))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

# ----------------------------
# RUN WEBHOOK (RENDER)
# ----------------------------
PORT = int(os.environ.get("PORT", 5000))
URL = f"https://jamb-bot.onrender.com/{TOKEN}"  # Your Render service URL

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=URL
)
