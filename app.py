import streamlit as st
import yfinance as yf
from ta.trend import EMAIndicator
import datetime

st.set_page_config(page_title="Institutional Market Dashboard", layout="wide")

st.title("📊 Institutional Market Structure Dashboard")

@st.cache_data(ttl=300)
def get_data():
    nifty = yf.download("^NSEI", period="2y", interval="1d", progress=False)
    sp500 = yf.download("^GSPC", period="1y", interval="1d", progress=False)
    vix = yf.download("^INDIAVIX", period="6mo", interval="1d", progress=False)

    if hasattr(nifty.columns, "levels"):
        nifty.columns = nifty.columns.get_level_values(0)
        sp500.columns = sp500.columns.get_level_values(0)
        vix.columns = vix.columns.get_level_values(0)

    return nifty, sp500, vix

nifty, sp500, vix = get_data()

if not nifty.empty:

    nifty['EMA50'] = EMAIndicator(nifty['Close'], window=50).ema_indicator()
    nifty['EMA200'] = EMAIndicator(nifty['Close'], window=200).ema_indicator()

    close = nifty['Close'].iloc[-1]
    ema50 = nifty['EMA50'].iloc[-1]
    ema200 = nifty['EMA200'].iloc[-1]

    score = 0

    if close > ema200:
        score += 30

    sp500_ma50 = sp500['Close'].rolling(50).mean().iloc[-1]
    if sp500['Close'].iloc[-1] > sp500_ma50:
        score += 20

    vix_ma20 = vix['Close'].rolling(20).mean().iloc[-1]
    if vix['Close'].iloc[-1] < vix_ma20:
        score += 20

    if ema50 > ema200:
        score += 15

    if close > ema50:
        score += 15

    if score >= 75:
        regime = "Strong Bull Market"
        exposure = "80-100%"
    elif score >= 55:
        regime = "Moderate Bull"
        exposure = "60-80%"
    elif score >= 35:
        regime = "Neutral / Transition"
        exposure = "40-60%"
    elif score >= 20:
        regime = "Defensive"
        exposure = "20-40%"
    else:
        regime = "High Risk Bear Market"
        exposure = "0-20%"

    col1, col2, col3 = st.columns(3)

    col1.metric("NIFTY Close", round(close,2))
    col2.metric("Institutional Score", f"{score} / 100")
    col3.metric("Suggested Exposure", exposure)

    st.subheader("Market Regime")
    st.write(regime)

    st.write("Last Updated:", datetime.datetime.now())
