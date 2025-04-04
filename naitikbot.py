# The following code requires 'python-telegram-bot'. Make sure it is installed via pip.
import logging
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import io
import asyncio

try:
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters, ContextTypes
except ModuleNotFoundError as e:
    raise ImportError("The 'python-telegram-bot' package is not installed. Please install it using 'pip install python-telegram-bot' and try again.") from e

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Fallback EMA, MACD, RSI implementations

def compute_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA100'] = df['Close'].ewm(span=100, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
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
    support_series = df['Low'].rolling(window=20).min()
    resistance_series = df['High'].rolling(window=20).max()
    support = support_series.iloc[-1]
    resistance = resistance_series.iloc[-1]
    support_timeframe = support_series[support_series == support].index[-1].strftime('%Y-%m-%d')
    return support, resistance, support_timeframe

# Generate Candlestick Chart

def generate_chart(symbol, df):
    support, resistance, support_timeframe = get_support_resistance(df)
    mc = mpf.make_marketcolors(up='g', down='r', edge='black', wick='black', volume='gray')
    s = mpf.make_mpf_style(marketcolors=mc)
    fig, ax = mpf.plot(df[-100:], type='candle', style=s, volume=True, returnfig=True)
    ax[0].axhline(y=support, color='blue', linestyle='--', label='Support')
    ax[0].text(df.index[-100], support + 1, f"Support\n({support_timeframe})", color='blue', verticalalignment='bottom')
    ax[0].axhline(y=resistance, color='red', linestyle='--', label='Resistance')
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
    support, resistance, support_timeframe = get_support_resistance(df)

    trend = "Uptrend" if close > ema50 else "Downtrend"
    rsi_signal = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
    macd_signal_text = "Bullish Crossover" if macd > macd_signal else "Bearish Crossover"

    analysis = f"\U0001F4CA Stock Analysis for {symbol}\n"
    analysis += f"\n\U0001F7E2 Trend: {trend}"
    analysis += f"\n\U0001F4C9 RSI: {rsi:.2f} ({rsi_signal})"
    analysis += f"\n\U0001F4C8 MACD Signal: {macd_signal_text}"
    analysis += f"\n\U0001F535 Support: ₹{support:.2f} (as of {support_timeframe})"
    analysis += f"\n\U0001F534 Resistance: ₹{resistance:.2f}"
    return analysis

# Handle Text Message (stock symbol)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().upper()
    if not (user_input.endswith(".NS") or user_input.endswith(".BO")):
        symbol = f"{user_input}.NS"
    else:
        symbol = user_input

    try:
        df = get_stock_data(symbol)
        img = generate_chart(symbol, df)
        summary = generate_analysis(symbol, df)
        await update.message.reply_photo(photo=img, caption=summary)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error analyzing '{symbol}': {str(e)}")

# Main Function

async def main():
    TOKEN = "7663257272:AAHR20ai1-4WQme-GYzazQ9QjhVr4biOb3c"
    application = Application.builder().token(TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await application.run_polling()

if __name__ == "__main__":
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ModuleNotFoundError:
        pass

    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e).startswith("This event loop is already running"):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise
