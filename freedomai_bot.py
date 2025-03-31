import telegram
from telegram.ext import Updater, CommandHandler
import math

# توکن بات رو اینجا بذارید
TOKEN = "7771779407:AAGI84IGAYPMfTvln-HXESafm-U2ZCKCy5I"

# تابع خوش‌آمدگویی
def start(update, context):
    welcome_message = (
        "سلام! من بات جدیدت هستم. هدفم رساندن تو به آزادی مالی است.\n"
        "یعنی تامین هزینه‌های زندگی با درآمد غیرفعال (بدون نیاز به کار کردن) با سرمایه‌گذاری هوشمندانه.\n\n"
        "⚠️ قبل از انجام هر سرمایه‌گذاری، با مشاور مالی خودتان مشورت کنید و مطالب بات را با شرایط خودتان تنظیم کنید."
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)

# تابع محاسبه هدف با تورم
def calculate_target(monthly_expense, years):
    annual_expense = monthly_expense * 12
    future_expense = annual_expense * (1 + 0.3) ** years  # تورم 30%
    target = future_expense / 0.04  # نرخ برداشت 4%
    return target

# تابع محاسبه زمان
def calculate_years(monthly_saving, target, risk_profile):
    if risk_profile == "none":
        rate = 0.19  # میانگین بازدهی (50% مسکن 15% + اجاره، 30% طلا 20%、20% بیت‌کوین 30%)
    elif risk_profile == "low":
        rate = 0.20  # میانگین (40% مسکن، 40% طلا، 20% بیت‌کوین)
    else:  # high
        rate = 0.22  # میانگین (30% مسکن، 30% طلا، 40% بیت‌کوین)

    total_saving = 0
    years = 0
    while total_saving < target:
        total_saving = monthly_saving * 12 * ((1 + rate) ** years - 1) / rate
        years += 1
    return years - 1

# تابع اصلی بات
def calculate(update, context):
    try:
        args = context.args
        monthly_saving = int(args[0])  # پس‌انداز ماهانه
        monthly_expense = int(args[1])  # هزینه ماهانه
        risk_profile = args[3] if len(args) > 3 else "low"  # سطح ریسک (پیش‌فرض: کم‌ریسک)

        # محاسبه هدف با فرض حداکثر زمان
        target = calculate_target(monthly_expense, 20)
        years = calculate_years(monthly_saving, target, risk_profile)

        # سبد سرمایه‌گذاری
        if risk_profile == "none":
            portfolio = "۵۰٪ مسکن، ۳۰٪ طلا، ۲۰٪ بیت‌کوین"
        elif risk_profile == "low":
            portfolio = "۴۰٪ مسکن، ۴۰٪ طلا، ۲۰٪ بیت‌کوین"
        else:  # high
            portfolio = "۳۰٪ مسکن، ۳۰٪ طلا، ۴۰٪ بیت‌کوین"

        # خروجی
        response = f"زمان رسیدن به آزادی مالی: {years} سال\n"
        response += f"سبد سرمایه‌گذاری: {portfolio}\n"
        response += f"هدف: {int(target):,} تومان"

        context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    except (IndexError, ValueError):
        context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً ورودی رو درست وارد کنید: /Calculate <پس‌انداز> <هزینه> --invest --risk-profile <none/low/high>")

# راه‌اندازی بات
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))  # اضافه کردن دستور start
dp.add_handler(CommandHandler("calculate", calculate))
updater.start_polling()
updater.idle()
