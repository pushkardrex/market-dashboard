import streamlit as st
import yfinance as yf
from ta.trend import EMAIndicator
import pandas as pd
import datetime

st.set_page_config(page_title="Institutional Market Dashboard", layout="wide")

st.title("📊 Institutional Market Structure Dashboard")

@st.cache_data(ttl=300)
def get_data():
    nifty = yf.download("^NSEI", period="2y", interval="1d", progress=False)
    sp500 = yf.download("^GSPC", period="1y", interval="1d", progress=False)
    vix = yf.download("^INDIAVIX", period="1y", interval="1d", progress=False)

    if hasattr(nifty.columns, "levels"):
        nifty.columns = nifty.columns.get_level_values(0)
        sp500.columns = sp500.columns.get_level_values(0)
        vix.columns = vix.columns.get_level_values(0)

    return nifty, sp500, vix

nifty, sp500, vix = get_data()

if not nifty.empty:

    nifty['EMA50'] = EMAIndicator(nifty['Close'], window=50).ema_indicator()
    nifty['EMA200'] = EMAIndicator(nifty['Close'], window=200).ema_indicator()

    # ---- SCORE CALCULATION FUNCTION ----
    def calculate_score(i):
        score = 0
        close = nifty['Close'].iloc[i]
        ema50 = nifty['EMA50'].iloc[i]
        ema200 = nifty['EMA200'].iloc[i]

        if close > ema200:
            score += 30

        sp500_ma50 = sp500['Close'].rolling(50).mean().iloc[i]
        if sp500['Close'].iloc[i] > sp500_ma50:
            score += 20

        vix_ma20 = vix['Close'].rolling(20).mean().iloc[i]
        if vix['Close'].iloc[i] < vix_ma20:
            score += 20

        if ema50 > ema200:
            score += 15

        if close > ema50:
            score += 15

        return score

    # ---- Current Score ----
    latest_score = calculate_score(-1)
    close = nifty['Close'].iloc[-1]

    # ---- Regime Logic ----
    def regime_model(score):
        if score >= 75:
            return "Strong Bull Market", (0.8, 1.0)
        elif score >= 55:
            return "Moderate Bull", (0.6, 0.8)
        elif score >= 35:
            return "Neutral / Transition", (0.4, 0.6)
        elif score >= 20:
            return "Defensive", (0.2, 0.4)
        else:
            return "High Risk Bear Market", (0.0, 0.2)

    regime, exposure_range = regime_model(latest_score)

    col1, col2, col3 = st.columns(3)
    col1.metric("NIFTY Close", round(close,2))
    col2.metric("Institutional Score", f"{latest_score} / 100")
    col3.metric("Suggested Exposure", f"{int(exposure_range[0]*100)}-{int(exposure_range[1]*100)}%")

    st.subheader("Market Regime")
    st.write(regime)

    # =========================
    # 📈 SCORE HISTORY CHART
    # =========================
    st.subheader("Institutional Score - Last 1 Year")

    scores = []
    for i in range(-252, 0):
        try:
            scores.append(calculate_score(i))
        except:
            scores.append(None)

    score_df = pd.DataFrame({
        "Date": nifty.index[-252:],
        "Score": scores
    })

    score_df.set_index("Date", inplace=True)
    st.line_chart(score_df)

    # =========================
    # 💰 CAPITAL ALLOCATION
    # =========================
    st.subheader("Capital Allocation Calculator")

    capital = st.number_input("Enter Total Capital (₹)", value=2000000)

    min_alloc = capital * exposure_range[0]
    max_alloc = capital * exposure_range[1]

    st.write(f"Recommended Equity Allocation: ₹{int(min_alloc):,} to ₹{int(max_alloc):,}")
    st.write(f"Cash / Defensive Allocation: ₹{int(capital - max_alloc):,} to ₹{int(capital - min_alloc):,}")

    st.write("Last Updated:", datetime.datetime.now())
