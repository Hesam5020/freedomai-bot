from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Hello! I’m your new bot, ready to assist you!\n\n"
        "Our goal is to help you achieve financial freedom through smart saving and investing. "
        "Financial freedom means having enough passive income to cover your living expenses "
        "without relying on active work, giving you the freedom to live life on your terms. "
        "Suggestions are provided based on the current state of gold, real estate, stock markets, "
        "cryptocurrency, inflation rates of various countries, and future predictions for these markets.\n\n"
        "Disclaimer: Please note that I am not a financial advisor. "
        "The information and calculations provided by this bot are for general guidance only "
        "and should not be considered professional financial advice. "
        "For personalized and accurate financial decisions, I strongly recommend consulting "
        "with a qualified financial advisor to ensure your specific needs and circumstances are addressed.\n\n"
        "To get started, please use /input to provide your details."
    )
    await update.message.reply_text(message)

async def input_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Please provide the following information (in one message, separated by spaces):\n"
        "1. Your current savings\n"
        "2. Your monthly expenses\n"
        "3. Desired time to reach financial freedom (in years)\n"
        "4. Your currency (e.g., USD, EUR, IRR)\n"
        "5. Expected annual return on investment (ROI) in % (e.g., 5 for 5%)\n"
        "6. Annual inflation rate in % (e.g., 3 for 3%)\n"
        "7. Your current monthly income\n\n"
        "Example: /input 10000 500 5 USD 5 3 2000"
    )
    await update.message.reply_text(message)

async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 7:
            await update.message.reply_text("Please provide exactly 7 values: savings, expenses, years, currency, ROI, inflation, income.\nExample: /input 10000 500 5 USD 5 3 2000")
            return
        
        savings = float(args[0])
        expenses = float(args[1])
        years = float(args[2])
        currency = args[3].upper()
        roi = float(args[4]) / 100 # Convert percentage to decimal
        inflation = float(args[5]) / 100 # Convert percentage to decimal
        income = float(args[6])

        if savings < 0 or expenses < 0 or years <= 0 or roi <= 0 or inflation < 0 or income < 0:
            await update.message.reply_text("Values must be positive (savings, expenses, inflation, and income can be 0, but years and ROI must be greater than 0).")
            return

        # Adjust expenses for inflation over the years
        adjusted_expenses = expenses * ((1 + inflation) ** years)
        annual_expenses = adjusted_expenses * 12
        total_needed = annual_expenses / roi # Total needed based on ROI
        additional_needed = total_needed - savings
        monthly_saving_needed = additional_needed / (years * 12)
        savings_percentage = (monthly_saving_needed / income) * 100 if income > 0 else float('inf')

        response = (
            f"Based on your input:\n"
            f"- Savings: {savings:.2f} {currency}\n"
            f"- Monthly Expenses: {expenses:.2f} {currency}\n"
            f"- Years to Freedom: {years}\n"
            f"- Currency: {currency}\n"
            f"- Expected ROI: {roi*100:.1f}%\n"
            f"- Inflation Rate: {inflation*100:.1f}%\n"
            f"- Monthly Income: {income:.2f} {currency}\n\n"
            f"Adjusted for {inflation*100:.1f}% annual inflation, your expenses in {years} years will be {adjusted_expenses:.2f} {currency} per month.\n"
            f"You need {total_needed:.2f} {currency} in total to achieve financial freedom (based on {roi*100:.1f}% ROI).\n"
            f"With your current savings, you still need {additional_needed:.2f} {currency}.\n"
            f"To reach this in {years} years, you should save approximately {monthly_saving_needed:.2f} {currency} per month.\n"
            f"This is {savings_percentage:.1f}% of your current income."
        )
        await update.message.reply_text(response)
    except ValueError:
        await update.message.reply_text("Please enter valid numbers for all values except currency.\nExample: /input 10000 500 5 USD 5 3 2000")

def main():
    token = os.getenv("TELEGRAM_TOKEN") # Get token from environment variable
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("input", input_data))
    application.add_handler(CommandHandler("input", process_input))
    
    # Set up Webhook
    port = int(os.environ.get("PORT", 5000)) # Default Heroku port
    webhook_url = f"https://{os.environ['HEROKU_APP_NAME']}.herokuapp.com/webhook"
    asyncio.run(application.bot.set_webhook(webhook_url))
    
    @app.route('/webhook', methods=['POST'])
    def webhook():
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))
        return '', 200
    
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()
