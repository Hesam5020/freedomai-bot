from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import os
import random

app = Flask(__name__)

token = os.getenv("TELEGRAM_TOKEN")
application = Application.builder().token(token).build()

@app.route('/')
def home():
    return "Bot is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "سلام! من بات آزادی مالی برای ایرانی‌ها هستم!\n\n"
        "هدفم اینه که بهت کمک کنم با شرایط ایران به آزادی مالی برسی—جایی که درآمد غیرفعالت هزینه‌هات رو پوشش بده. "
        "پلن در دو مرحله‌ست:\n"
        "۱. افزایش پس‌انداز تا سرمایه‌ای که هزینه‌های تعدیل‌شده با تورم رو پوشش بده\n"
        "۲. ایجاد درآمد غیرفعال با خرید و اجاره ملک\n\n"
        "توجه: من مشاور مالی نیستم—برای تصمیم‌های دقیق، با یه مشاور مشورت کن.\n\n"
        "برای شروع، از /input استفاده کن!"
    )
    await update.message.reply_text(message)

async def input_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "لطفاً این اطلاعات رو تو یه پیام (با فاصله) بفرست:\n"
        "۱. پس‌انداز ماهانه (مقدار سرمایه‌گذاری ماهانه به تومان)\n"
        "۲. هزینه ماهانه (درآمد غیرفعال هدف به تومان)\n"
        "۳. ریسک‌پذیری (ریسک‌پذیرم / ریسک‌پذیر نیستم)\n\n"
        "مثال: /input 5000000 10000000 ریسک‌پذیرم"
    )
    await update.message.reply_text(message)

async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 3:
            await update.message.reply_text("لطفاً دقیقاً ۳ مقدار بفرست: پس‌انداز ماهانه، هزینه ماهانه، و ریسک‌پذیری. مثال: /input 5000000 10000000 ریسک‌پذیرم")
            return
        
        monthly_savings = float(args[0])
        monthly_expenses = float(args[1])
        risk_level = args[2].strip()

        if monthly_savings <= 0 or monthly_expenses <= 0:
            await update.message.reply_text("مقادیر مالی باید مثبت باشن (بیشتر از ۰).")
            return
        
        valid_risks = ["ریسک‌پذیرم", "ریسک‌پذیر نیستم"]
        if risk_level not in valid_risks:
            await update.message.reply_text("ریسک‌پذیری باید یکی از اینا باشه: ریسک‌پذیرم، ریسک‌پذیر نیستم")
            return

        # مرحله ۱: افزایش پس‌انداز با در نظر گرفتن تورم
        inflation_rate = 0.5 # تورم ۵۰٪ سالانه
        annual_expenses = monthly_expenses * 12
        adjusted_annual_expenses = annual_expenses * (1 + inflation_rate) ** 10 # تعدیل برای ۱۰ سال
        target_capital = adjusted_annual_expenses * 25 # قانون ۴٪
        years_to_target = target_capital / (monthly_savings * 12)

        # سبد سرمایه‌گذاری برای مرحله ۱
        if risk_level == "ریسک‌پذیرم":
            investment_suggestion = (
                "مرحله ۱ - سبد سرمایه‌گذاری برای افزایش پس‌انداز:\n"
                "- بیت‌کوین: ۵۰٪\n"
                "- سهام بورسی: ۳۰٪\n"
                "- طلا: ۲۰٪"
            )
        else: # ریسک‌پذیر نیستم
            investment_suggestion = (
                "مرحله ۱ - سبد سرمایه‌گذاری برای افزایش پس‌انداز:\n"
                "- طلا: ۵۰٪\n"
                "- صندوق‌های درآمد ثابت: ۳۰٪\n"
                "- بیت‌کوین: ۲۰٪"
            )

        # مرحله ۲: درآمد غیرفعال با اجاره
        adjusted_monthly_expenses = adjusted_annual_expenses / 12 # هزینه ماهانه تعدیل‌شده
        rental_income = adjusted_monthly_expenses # فرض: اجاره برابر هدف تعدیل‌شده
        passive_income_message = (
            f"مرحله ۲ - ایجاد درآمد غیرفعال:\n"
            f"با سرمایه {target_capital:,.0f} تومان، می‌تونی ملکی بخری که ماهی {rental_income:,.0f} تومان اجاره بده.\n"
            f"این هدف درآمد غیرفعالت رو با تورم ۵۰٪ برای ۱۰ سال آینده کامل پوشش می‌ده."
        )

        # جمله انگیزشی تصادفی
        motivational_quotes = [
            "قدم‌های کوچک ولی مکرر، تو را به اهداف بزرگ می‌رساند.",
            "با قدرت شروع کن، با انگیزه ادامه بده و با لذت تمام کن."
        ]
        motivational_message = random.choice(motivational_quotes)

        response = (
            f"با این ورودی‌ها:\n"
            f"- پس‌انداز ماهانه: {monthly_savings:,} تومان\n"
            f"- هزینه ماهانه (درآمد غیرفعال هدف): {monthly_expenses:,} تومان\n"
            f"- ریسک‌پذیری: {risk_level}\n\n"
            f"{investment_suggestion}\n"
            f"با تورم ۵۰٪ سالانه، تو {years_to_target:.1f} سال به سرمایه هدف {target_capital:,.0f} تومان می‌رسی.\n\n"
            f"{passive_income_message}\n\n"
            f"{motivational_message}"
        )
        await update.message.reply_text(response)
    except ValueError:
        await update.message.reply_text("لطفاً اعداد معتبر برای پس‌انداز و هزینه وارد کن. مثال: /input 5000000 10000000 ریسک‌پذیرم")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("input", input_data))
application.add_handler(CommandHandler("input", process_input))

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return '', 200

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.initialize())
    port = int(os.environ.get("PORT", 8080))
    webhook_url = "https://freedomai-2025.onrender.com/webhook"
    loop.run_until_complete(application.bot.set_webhook(webhook_url))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()
