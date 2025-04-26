import pandas as pd
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN
import pytz


# Load questions from CSV file
questions_df = pd.read_csv('questions.csv')

# Function to start the bot and send a welcome message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Welcome to the Quiz Bot, {update.effective_user.first_name}!\nType /question to start the quiz.")

# Function to send a random question
async def question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    random_question = questions_df.sample(1).iloc[0]

    # Get the question text and answer
    question_text = random_question['question']
    context.user_data['correct_answer'] = random_question['answer']
    context.user_data['question_text'] = question_text

    options = [
        random_question['answer'],
        random_question['fake_answer_1'],
        random_question['fake_answer_2'],
        random_question['fake_answer_3']
    ]
    random.shuffle(options)

    keyboard = [
        [InlineKeyboardButton(option, callback_data=option)] for option in options
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"❓ {question_text}", reply_markup=reply_markup)

async def answer_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_answer = query.data
    right_answer = context.user_data.get('correct_answer')
    if user_answer == right_answer:
        await query.edit_message_text(text=f"✅ Correct!\nQuestion: {context.user_data.get('question_text')}\nThe answer is: {right_answer}")
    else:
        await query.edit_message_text(text=f"❌ Wrong!\nQuestion: {context.user_data.get('question_text')}\nThe answer is: {right_answer}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("question", question))
    app.add_handler(CommandHandler("answer", answer_button))
    app.add_handler(CallbackQueryHandler(answer_button))

    print("🤖 Bot Working. Ctrl+C to stop")
    app.run_polling()

if __name__ == '__main__':
    main()

