from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import os

# Create the Application instance globally
token = os.getenv("TELEGRAM_TOKEN")
application = Application.builder().token(token).build()

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
        "Please provide the following information using /calculate command (in one message, separated by spaces):\n"
        "1. Your current savings (in your currency)\n"
        "2. Your monthly expenses (in your currency)\n"
        "3. Desired time to reach financial freedom (in years)\n\n"
        "Example: /calculate 10000 500 5"
    )
    await update.message.reply_text(message)

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 3:
            await update.message.reply_text("Please provide exactly 3 values: savings, expenses, and years. Example: /calculate 10000 500 5")
            return
        
        savings = float(args[0])
        expenses = float(args[1])
        years = float(args[2])

        if savings < 0 or expenses < 0 or years <= 0:
            await update.message.reply_text("Values must be positive (savings and expenses can be 0, but years must be greater than 0).")
            return

        # Simple calculation: How much passive income is needed annually
        annual_expenses = expenses * 12
        total_needed = annual_expenses * 25 # Based on 4% withdrawal rule
        additional_needed = total_needed - savings
        monthly_saving_needed = additional_needed / (years * 12)

        response = (
            f"Based on your input:\n"
            f"- Savings: {savings}\n"
            f"- Monthly Expenses: {expenses}\n"
            f"- Years to Freedom: {years}\n\n"
            f"You need {total_needed:.2f} in total to achieve financial freedom (assuming a 4% withdrawal rate).\n"
            f"With your current savings, you still need {additional_needed:.2f}.\n"
            f"To reach this in {years} years, you should save approximately {monthly_saving_needed:.2f} per month."
        )
        await update.message.reply_text(response)
    except ValueError:
        await update.message.reply_text("Please enter valid numbers. Example: /calculate 10000 500 5")

# Add handlers to the application
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("input", input_data))
application.add_handler(CommandHandler("calculate", calculate))

# Create aiohttp app
app = web.Application()

async def home(request):
    return web.Response(text="Bot is running!")

async def webhook(request):
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return web.Response(status=200)

# Add routes
app.router.add_get('/', home)
app.router.add_post('/webhook', webhook)

async def on_startup(_):
    # Initialize the application
    await application.initialize()
    
    # Set up Webhook for Render
    webhook_url = "https://freedomai-2025.onrender.com/webhook" # Your Render URL
    await application.bot.set_webhook(webhook_url)

if __name__ == "__main__":
    # Add startup hook
    app.on_startup.append(on_startup)
    
    # Run the app
    port = int(os.environ.get("PORT", 8080)) # Default port for Render
    web.run_app(app, host='0.0.0.0', port=port)
