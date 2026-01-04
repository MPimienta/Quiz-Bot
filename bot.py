import pandas as pd
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN
from db import *
import pytz
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# Load questions from CSV file
questions_df = pd.read_csv('questions.csv')


# Function to start the bot and send a welcome message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['active_questions'] = {}
    await update.message.reply_text(f"Welcome to the Quiz Bot, {update.effective_user.first_name}!\nType /question to start the quiz.")

# Function to send a random question
async def question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    random_question = questions_df.sample(1).iloc[0]

    # Get the question text and answer
    question_text = random_question['question']
    correct_answer = random_question['answer']

    options = [
        correct_answer,
        random_question['fake_answer_1'],
        random_question['fake_answer_2'],
        random_question['fake_answer_3']
    ]
    random.shuffle(options)

    keyboard = [
        [InlineKeyboardButton(option, callback_data=option)] for option in options
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await update.message.reply_text(f"❓ {question_text}", reply_markup=reply_markup)

    message_id = message.message_id
    user_questions = context.user_data.setdefault("active_questions", {})
    user_questions[message_id] = {
        "question": question_text,
        "correct_answer": correct_answer,
    }

async def answer_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    message_id = query.message.message_id
    user_questions = context.user_data.get("active_questions", {})

    question_data = user_questions.get(message_id)
    if not question_data:
        await query.edit_message_text("⚠️ This question has already been answered or is invalid.")
        return
    
    user_answer = query.data
    correct_answer = question_data["correct_answer"]
    user_id = update.effective_user.id

    score_actual = await get_user_score(user_id)

    if user_answer == correct_answer:
        score_actual += 1
        result_text = f"✅ Correct!\n\nQuestion: {question_data['question']}\nAnswer: {correct_answer}"
    else:
        score_actual = max(0, score_actual - 1)
        result_text = f"❌ Wrong!\n\nQuestion: {question_data['question']}\nAnswer: {correct_answer}"

    await update_user_score(user_id, score_actual)

    user_questions.pop(message_id, None)

    await query.edit_message_text(text=result_text)
        
async def view_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    score_actual = await get_user_score(user_id)
    await update.message.reply_text(f"🎯 Your current score is: {score_actual}")

# --- Servidor Web "Dummy" para Render ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Responder con estado 200 (OK) a cualquier petición
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def start_dummy_server():
    # Render nos asignará un puerto en la variable de entorno 'PORT'
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"🌍 Servidor dummy escuchando en el puerto {port}")
    server.serve_forever()

def main():

    # Iniciar el servidor web en un hilo separado (daemon=True para que cierre al salir)
    Thread(target=start_dummy_server, daemon=True).start()

    # Load db
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("question", question))
    app.add_handler(CommandHandler("stats", view_score))
    app.add_handler(CallbackQueryHandler(answer_button))

    print("🤖 Bot Working. Ctrl+C to stop")
    app.run_polling()

if __name__ == '__main__':
    main()

