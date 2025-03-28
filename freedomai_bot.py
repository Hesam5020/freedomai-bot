import numpy as np
import yfinance as yf
import requests
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# وب‌سرور Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "FreedomAI Bot is running!"

# توابع دریافت داده (کوتاه شده برای سرعت)
def fetch_exchange_rate(base_currency, target_currency="USD"):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        r = requests.get(url)
        return r.json()["rates"][target_currency] if r.status_code == 200 else 1.0
    except:
        return 1.0

def fetch_country_data(country):
    return 0.03, 1000 # فرضی برای تست

def fetch_yfinance_data(symbol, period="5y", interval="1mo"):
    try:
        return yf.Ticker(symbol).history(period=period, interval=interval)["Close"].values
    except:
        return None

def fetch_coingecko_data(currency="usd"):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency={currency}&days=365"
        r = requests.get(url)
        return np.array([price[1] for price in r.json()["prices"]]) if r.status_code == 200 else None
    except:
        return None

def fetch_global_data_from_api(country, base_currency, nobitex_token=None):
    inflation, living_cost = fetch_country_data(country)
    exchange_rate = fetch_exchange_rate(base_currency)
    gold = fetch_yfinance_data("GC=F")
    btc = fetch_coingecko_data(base_currency)
    dollar = fetch_yfinance_data(f"USD{country.upper()}=X") or fetch_yfinance_data("USD")
    markets = {
        "safe": {"rate": 0.10, "risk": 0.1, "volatility": 0.03, "data": gold},
        "moderate": {"rate": 0.15, "risk": 0.2, "volatility": 0.05, "data": None},
        "risky": {"rate": 0.20, "risk": 0.5, "volatility": 0.10, "data": btc},
        "bank": {"rate": 0.03, "risk": 0.05, "volatility": 0.02, "data": None},
        "dollar": {"rate": 0.05, "risk": 0.3, "volatility": 0.08, "data": dollar}
    }
    for m, info in markets.items():
        if info["data"] is not None and len(info["data"]) > 1:
            returns = np.diff(info["data"]) / info["data"][:-1]
            markets[m]["rate"] = max(0, float(np.mean(returns) * 12))
            markets[m]["volatility"] = float(np.std(returns) * np.sqrt(12))
    return {"country": country, "inflation": inflation, "tax_rate": 0.0, "living_cost": living_cost, "exchange_rate": exchange_rate, "currency": base_currency, "markets": markets}

# توابع LSTM (کوتاه شده)
def prepare_lstm_data(data, look_back=12):
    if data is None or len(data) < look_back + 1: return None, None, None
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data.reshape(-1, 1))
    X, y = [], []
    for i in range(look_back, len(scaled)):
        X.append(scaled[i-look_back:i, 0])
        y.append(scaled[i, 0])
    return np.array(X), np.array(y), scaler

def train_lstm_model(data, look_back=12, epochs=10):
    X, y, scaler = prepare_lstm_data(data, look_back)
    if X is None: return None, None
    X = X.reshape((X.shape[0], X.shape[1], 1))
    model = Sequential([LSTM(50, input_shape=(look_back, 1), return_sequences=True), Dropout(0.2), LSTM(50), Dropout(0.2), Dense(1)])
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, epochs=epochs, batch_size=1, verbose=0)
    return model, scaler

def predict_next_rate(model, scaler, data, look_back=12):
    if model is None or len(data) < look_back: return 0
    last = scaler.transform(data[-look_back:].reshape(-1, 1))
    last = last.reshape((1, look_back, 1))
    pred = model.predict(last, verbose=0)
    return max(0, scaler.inverse_transform(pred)[0, 0])

def train_market_predictions(markets):
    predictions = {}
    for m, info in markets.items():
        if info["data"] is not None:
            model, scaler = train_lstm_model(info["data"])
            pred_rate = predict_next_rate(model, scaler, info["data"]) / info["data"][-1] - 1 if info["data"][-1] else info["rate"]
            predictions[m] = {"rate": pred_rate, "risk": info["risk"]}
        else:
            predictions[m] = {"rate": info["rate"], "risk": info["risk"]}
    return predictions

# Monte Carlo و بهینه‌سازی
def monte_carlo_simulation(savings, goal, rate, risk, volatility, months_max=240):
    sims = 100
    outcomes, success, stress_outcomes = [], 0, []
    for _ in range(sims):
        fv = 0
        for m in range(months_max):
            m_rate = (rate + random.uniform(-volatility, volatility) - random.uniform(0, risk)) / 12
            if m == 60 and random.random() < 0.1: fv *= 0.7
            fv = (fv + savings) * (1 + m_rate)
            if fv >= goal:
                success += 1
                outcomes.append(m / 12)
                break
        else:
            outcomes.append(months_max / 12)
        stress_outcomes.append(fv)
    return sum(outcomes) / len(outcomes), (success / sims) * 100, max(outcomes), min(stress_outcomes)

def optimize_portfolio(markets, savings_local, dynamic_goal, months_max=240, trials=50):
    best_portfolio, best_time = None, float('inf')
    for _ in range(trials):
        weights = np.random.dirichlet(np.ones(5))
        portfolio = {"safe": weights[0], "moderate": weights[1], "risky": weights[2], "bank": weights[3], "dollar": weights[4]}
        combined_rate = sum(markets[m]["rate"] * portfolio[m] for m in markets)
        fv, months = 0, 0
        m_rate = combined_rate / 12
        while fv < dynamic_goal and months < months_max:
            fv = (fv + savings_local) * (1 + m_rate)
            months += 1
        if months < best_time:
            best_time = months
            best_portfolio = portfolio
    return best_portfolio, best_time / 12

# تحلیل و پیشنهاد
def sensitivity_analysis(savings_local, expenses_local, data, portfolio, combined_rate):
    base_goal = (expenses_local * 12) / (1 - data["tax_rate"]) / combined_rate * (1 + data["inflation"])**5
    scenarios = {"Inflation +5%": {"inflation": data["inflation"] + 0.05}, "Savings -20%": {"savings": savings_local * 0.8}, "Expenses +20%": {"expenses": expenses_local * 1.2}}
    results = {}
    for scenario, change in scenarios.items():
        temp_savings = change.get("savings", savings_local)
        temp_expenses = change.get("expenses", expenses_local)
        temp_inflation = change.get("inflation", data["inflation"])
        temp_goal = (temp_expenses * 12) / (1 - data["tax_rate"]) / combined_rate * (1 + temp_inflation)**5
        months, fv = 0, 0
        monthly_rate = (combined_rate - temp_inflation / 12) / 12
        while fv < temp_goal and months < 240:
            fv = (fv + temp_savings) * (1 + monthly_rate)
            months += 1
        results[scenario] = months / 12
    return results

def goal_solver(expenses_local, target_years, data, portfolio, combined_rate):
    monthly_rate = (combined_rate - data["inflation"] / 12) / 12
    dynamic_goal = (expenses_local * 12) / (1 - data["tax_rate"]) / combined_rate * (1 + data["inflation"])**5
    months = target_years * 12
    return dynamic_goal / ((1 + monthly_rate)**months - 1) * monthly_rate

# تابع اصلی
def final_financial_freedom(savings, expenses, country="Iran", age=54, risk_tolerance="moderate", months_passed=0, base_currency="IRR", target_years=10, nobitex_token=None):
    data = fetch_global_data_from_api(country, base_currency, nobitex_token)
    savings_local = savings * data["exchange_rate"]
    expenses_local = expenses * data["exchange_rate"]
    
    predicted_markets = train_market_predictions(data["markets"])
    portfolios = {
        "safe": {"safe": 1.0, "moderate": 0, "risky": 0, "bank": 0, "dollar": 0},
        "moderate": {"safe": 0.6, "moderate": 0.4, "risky": 0, "bank": 0, "dollar": 0},
        "risky": {"safe": 0.2, "moderate": 0.3, "risky": 0.5, "bank": 0, "dollar": 0}
    }
    portfolio = portfolios[risk_tolerance]
    combined_rate = sum(predicted_markets[m]["rate"] * portfolio[m] for m in predicted_markets)
    combined_risk = sum(predicted_markets[m]["risk"] * portfolio[m] for m in predicted_markets)
    volatility = sum(data["markets"][m]["volatility"] * portfolio[m] for m in data["markets"])
    dynamic_goal = (expenses_local * 12) / (1 - data["tax_rate"]) / combined_rate * (1 + data["inflation"])**5

    fv, months = 0, 0
    m_rate = (combined_rate - data["inflation"]/12) / 12
    while fv < dynamic_goal and months < 240:
        fv = (fv + savings_local) * (1 + m_rate)
        months += 1
    passive_income = fv * combined_rate / 12 * (1 - data["tax_rate"])
    avg_years, success_rate, worst_years, stress_worst = monte_carlo_simulation(savings_local, dynamic_goal, combined_rate, combined_risk, volatility)
    opt_portfolio, opt_years = optimize_portfolio(predicted_markets, savings_local, dynamic_goal)
    sensitivity = sensitivity_analysis(savings_local, expenses_local, data, portfolio, combined_rate)
    savings_needed = goal_solver(expenses_local, target_years, data, portfolio, combined_rate)

    output = (f"Goal: {dynamic_goal:,.2f} {data['currency']}\n"
              f"Portfolio ({risk_tolerance}): {months/12:.1f} years\n"
              f"Passive Income: {passive_income:,.2f} {data['currency']}/month (Need: {expenses_local:,.2f})\n"
              f"Monte Carlo: Avg {avg_years:.1f} years, Success {success_rate:.1f}%\n"
              f"Worst Case (Stress): {stress_worst:,.2f} {data['currency']}\n"
              f"Optimal Portfolio: {opt_portfolio}, Time: {opt_years:.1f} years\n"
              f"Sensitivity:\n" + "\n".join(f" {k}: {v:.1f} years" for k, v in sensitivity.items()) + "\n"
              f"Suggestion for {target_years} years: Save {savings_needed:,.2f} {data['currency']}\n"
              f"Retirement Age: {age + months/12:.1f}")
    return output

# دستورات بات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to FreedomAI Bot! Use /calculate <savings> <expenses> <country> <currency> <risk> <age> <target_years>\nExample: /calculate 150000000 150000000 Iran IRR moderate 54 10")

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 7:
            await update.message.reply_text("Please provide: <savings> <expenses> <country> <currency> <risk> <age> <target_years>")
            return
        savings, expenses, country, currency, risk, age, target_years = float(args[0]), float(args[1]), args[2], args[3], args[4], int(args[5]), int(args[6])
        result = final_financial_freedom(savings, expenses, country, age, risk, 0, currency, target_years)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    # توکن باتت رو اینجا بذار
    token = "7771779407:AAGI84IGAYPMfTvln-HXESafm-U2ZCKCy5I" # توکن خودت رو جایگزین کن
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("calculate", calculate))
    
    # polling تو thread جدا
    Thread(target=application.run_polling).start()
    
    # Flask مستقیم اجرا می‌شه
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
def main():
    token = "YOUR_TELEGRAM_BOT_TOKEN" # توکن خودت رو اینجا بذار
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("calculate", calculate))
    
    # مستقیم اجرا می‌کنیم
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    # Flask تو thread جدا
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
