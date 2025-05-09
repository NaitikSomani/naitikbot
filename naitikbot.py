# The following code is tailored for Render.com with polling
import logging
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import io
import asyncio
import os
import matplotlib.dates as mdates

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Fallback indicators
def compute_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA100'] = df['Close'].ewm(span=100, adjust=False).mean()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    df['BB_Upper'] = df['BB_Middle'] + 2 * df['Close'].rolling(window=20).std()
    df['BB_Lower'] = df['BB_Middle'] - 2 * df['Close'].rolling(window=20).std()

    # Stochastic Oscillator
    low_min = df['Low'].rolling(window=14).min()
    high_max = df['High'].rolling(window=14).max()
    df['%K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    df['%D'] = df['%K'].rolling(window=3).mean()

    return df

# Fetch stock data
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    df = stock.history(period='6mo')
    if df.empty:
        raise ValueError("No data found for the symbol.")
    df = compute_indicators(df)
    return df

# Identify Support & Resistance
def get_support_resistance(df):
    recent_data = df[-20:]
    support = recent_data['Low'].min()
    resistance = recent_data['High'].max()
    support_date = df[df['Low'] == support].index[-1].strftime('%Y-%m-%d')
    return support, resistance, support_date

# Generate Candlestick Chart
def generate_chart(symbol, df):
    support, resistance, support_date = get_support_resistance(df)
    close = df['Close'].iloc[-1]
    mc = mpf.make_marketcolors(up='g', down='r', edge='black', wick='black', volume='gray')
    s = mpf.make_mpf_style(marketcolors=mc)
    fig, ax = mpf.plot(df[-100:], type='candle', style=s, volume=True, returnfig=True)

    ax[0].axhline(y=support, color='blue', linestyle='--', label='Support')
    ax[0].axhline(y=resistance, color='red', linestyle='--', label='Resistance')
    ax[0].axhline(y=close, color='green', linestyle='--', label='CMP')

    x_pos = mdates.date2num(df.index[0])
    ax[0].text(x_pos, support, f"{support_date} - ₹{support:.2f}", color='blue')
    ax[0].text(x_pos, close, f"CMP - ₹{close:.2f}", color='green')

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    return buf

# Create Stock Analysis Summary
def generate_analysis(symbol, df):
    close = df['Close'].iloc[-1]
    ema20 = df['EMA20'].iloc[-1]
    ema50 = df['EMA50'].iloc[-1]
    ema100 = df['EMA100'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    macd = df['MACD'].iloc[-1]
    macd_signal = df['MACD_Signal'].iloc[-1]
    bb_upper = df['BB_Upper'].iloc[-1]
    bb_lower = df['BB_Lower'].iloc[-1]
    k = df['%K'].iloc[-1]
    d = df['%D'].iloc[-1]
    support, resistance, support_date = get_support_resistance(df)

    trend = "Uptrend" if close > ema50 else "Downtrend"
    rsi_signal = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
    macd_signal_text = "Bullish Crossover" if macd > macd_signal else "Bearish Crossover"
    bb_signal = "Near Upper Band" if close >= bb_upper else "Near Lower Band" if close <= bb_lower else "Within Bands"
    stochastic_signal = "Bullish" if k > d and k < 80 else "Bearish" if k < d and k > 20 else "Neutral"
    sentiment = "Positive" if macd > macd_signal and rsi < 70 else "Negative" if macd < macd_signal and rsi > 30 else "Neutral"
    zone = "Super Strong Zone" if close < support else "Strong Zone" if close < ema100 else "Weak Zone"

    return (
        f"\U0001F4CA Stock Analysis for {symbol}\n"
        f"\n💰 CMP: ₹{close:.2f}"
        f"\n\U0001F7E2 Trend: {trend}"
        f"\n\U0001F4C9 RSI: {rsi:.2f} ({rsi_signal})"
        f"\n\U0001F4C8 MACD: {macd:.2f}, Signal: {macd_signal:.2f} ({macd_signal_text})"
        f"\n\U0001F4C3 Bollinger Band: {bb_signal}"
        f"\n\U0001F52C Stochastic: %K={k:.2f}, %D={d:.2f} ({stochastic_signal})"
        f"\n\U0001F535 Support: ₹{support:.2f} (from {support_date})"
        f"\n\U0001F534 Resistance: ₹{resistance:.2f}"
        f"\n\U0001F4AC Sentiment Score: {sentiment}"
        f"\n\n\U0001F4DD Conclusion: {zone}"
    )

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()
    print(f"📩 Received message: {symbol}")
    if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
        symbol += ".NS"
    try:
        df = get_stock_data(symbol)
        chart = generate_chart(symbol, df)
        analysis = generate_analysis(symbol, df)
        await update.message.reply_photo(photo=chart, caption=analysis)
    except Exception as e:
        logging.error(f"Error analyzing '{symbol}': {e}")
        await update.message.reply_text(f"⚠️ Error analyzing '{symbol}': {str(e)}")

# Main bot setup
async def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN is not loaded from environment.")
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment variables.")
    else:
        print("✅ TELEGRAM_BOT_TOKEN successfully loaded.")

    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot is starting with polling...")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    from telegram.ext import Application

    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN is not loaded from environment.")
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment variables.")
    else:
        print("✅ TELEGRAM_BOT_TOKEN successfully loaded.")

    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot is starting with polling...")
    application.run_polling()

