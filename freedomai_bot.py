import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from threading import Thread
from flask import Flask
import financial_calculations as fc  # فرض می‌کنم این ماژول رو داری

# تنظیمات لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# تنظیم Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "FreedomAI Bot is running!"

# تابع شروع بات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm FreedomAI Bot. Use /calculate to plan your financial freedom."
    )

# تابع محاسبه
async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # گرفتن آرگومان‌ها از دستور کاربر
        args = context.args
        if len(args) != 7:
            await update.message.reply_text(
                "Please provide all required inputs in this format:\n"
                "/calculate <savings> <expenses> <country> <currency> <risk_tolerance> <age> <years>\n"
                "Example: /calculate 150000000 150000000 Iran IRR moderate 54 10"
            )
            return

        # تبدیل آرگومان‌ها به متغیرها
        savings = float(args[0])
        expenses = float(args[1])
        country = args[2]
        currency = args[3]
        risk_tolerance = args[4].lower()
        age = int(args[5])
        years = int(args[6])

        # فراخوانی تابع محاسبه از ماژول financial_calculations
        result = fc.calculate_financial_freedom(savings, expenses, country, currency, risk_tolerance, age, years)

        # ارسال نتیجه به کاربر
        await update.message.reply_text(result)

    except (ValueError, IndexError) as e:
        await update.message.reply_text(f"Error: {str(e)}. Please check your inputs and try again.")
    except Exception as e:
        await update.message.reply_text(f"An unexpected error occurred: {str(e)}")

# تابع اصلی برای اجرای بات
def main():
    # توکن بات تلگرام (اینو با توکن خودت جایگزین کن)
    token = "7771779407:AAGI84IGAYPMfTvln-HXESafm-U2ZCKCy5I"  # توکنی که از BotFather گرفتی رو اینجا بذار

    # ساخت اپلیکیشن تلگرام
    application = Application.builder().token(token).build()

    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("calculate", calculate))

    # اجرای بات با polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    # اجرای Flask تو یه thread جدا (برای Render)
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# اجرای برنامه
if __name__ == "__main__":
    main()
