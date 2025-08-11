
# pages/06_ScaleSignals_Backtest.py
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from data_manager import get_cbbi_history, get_coinbase_rank_history
import pytz

st.set_page_config(page_title="Scale In/Out Backtest", layout="wide")

st.title("📊 Scale In/Out Strategy Backtest")
st.markdown("Backtesting a multi-indicator strategy combining CBBI, Coinbase ranking, Pi Cycle, relative performance, and halving cycles.")

# --- Parameters (editable in UI) ---
st.subheader("Strategy Parameters")
colA, colB, colC, colD = st.columns(4)
with colA:
    strict_entry = st.toggle("Strict Entry (ALL true)", value=True)
with colB:
    strict_exit = st.toggle("Strict Exit (ALL true)", value=True)
with colC:
    mag7_window = st.number_input("MAG7 Lookback (days)", 60, 400, 180, 10)
with colD:
    pctl_in = st.slider("Underperf pctile (scale-in)", 0.0, 0.5, 0.15, 0.01)

# Add loading spinner
with st.spinner("Loading BTC and MAG7 data..."):
    # --- Data ---
    MAG7 = ["AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA"]
    
    try:
        btc = yf.download(["BTC-USD"], auto_adjust=False, progress=False)["Adj Close"].rename(columns={"BTC-USD":"BTC"}).dropna()
        mag7_prices = yf.download(MAG7, auto_adjust=False, progress=False)["Adj Close"].dropna(how="all")
        mag7_idx = (mag7_prices / mag7_prices.iloc[0]).mean(axis=1).rename("MAG7_EQW")
        
        # CBBI / Rank from DB
        cbbi = get_cbbi_history()  # date, cbbi
        rank = get_coinbase_rank_history()  # date, rank
        
        if not cbbi.empty:
            cbbi = cbbi.set_index("date").asfreq("D").interpolate(limit_direction="both")
        if not rank.empty:
            rank = rank.set_index("date").asfreq("D").bfill().ffill()
        
        # Align index
        df = pd.concat([btc["BTC"], mag7_idx], axis=1).dropna()
        
        st.success(f"Data loaded successfully! Dataset spans {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

# --- Indicators ---
with st.spinner("Computing indicators..."):
    PI_SHORT, PI_LONG = 111, 350
    sma_111 = df["BTC"].rolling(PI_SHORT).mean()
    sma_350 = df["BTC"].rolling(PI_LONG).mean()
    pitop = (sma_111.mul(2).shift(1) <= sma_350.shift(1)) & (sma_111.mul(2) > sma_350)
    
    btc_r = df["BTC"].pct_change(int(mag7_window))
    mag7_r = df["MAG7_EQW"].pct_change(int(mag7_window))
    rel = (btc_r - mag7_r).rename("RelPerf")
    rel_pctl = rel.expanding().apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])
    
    # Halving windows
    halvings = pd.to_datetime(["2012-11-28","2016-07-09","2020-05-11","2024-04-19"])
    def month_delta(ts, m):
        y = ts.year + (ts.month - 1 + m)//12
        mo = ((ts.month - 1 + m)%12)+1
        d = min(ts.day, [31,29 if y%4==0 and (y%100!=0 or y%400==0) else 28,31,30,31,30,31,31,30,31,30,31][mo-1])
        return pd.Timestamp(year=y, month=mo, day=d)
    
    hin = pd.Series(False, index=df.index)
    hout = pd.Series(False, index=df.index)
    for h in halvings:
        a, b = month_delta(h, -18), month_delta(h, -12)
        c, d2 = month_delta(h, 12), month_delta(h, 18)
        hin |= ((df.index >= a) & (df.index <= b))
        hout |= ((df.index >= c) & (df.index <= d2))
    
    # Join externals
    if not cbbi.empty:
        df = df.join(cbbi["cbbi"], how="left")
    else:
        df["cbbi"] = np.nan
        
    if not rank.empty:
        df = df.join(rank["rank"].rename("coinbase_rank"), how="left")
    else:
        df["coinbase_rank"] = np.nan
    
    df["RelPerfPctile"] = rel_pctl
    df["PiTop"] = pitop.fillna(False)
    df["Halving_IN"] = hin
    df["Halving_OUT"] = hout

# Compose signals
CBBI_IN_MAX, CBBI_OUT_MIN = 20, 90
CB_RANK_HOT_MAX, CB_RANK_COLD_MIN = 5, 100

entry_parts = [
    (df["cbbi"] <= CBBI_IN_MAX),
    (df["coinbase_rank"] >= CB_RANK_COLD_MIN),
    (df["RelPerfPctile"] <= pctl_in),
    (df["Halving_IN"])
]
exit_parts = [
    (df["PiTop"]),
    (df["cbbi"] >= CBBI_OUT_MIN),
    (df["coinbase_rank"] <= CB_RANK_HOT_MAX),
    (df["Halving_OUT"])
]

entry_true = sum([p.fillna(False) for p in entry_parts])
exit_true = sum([p.fillna(False) for p in exit_parts])

entry_need = len(entry_parts) if strict_entry else 2
exit_need  = len(exit_parts) if strict_exit else 2
df["EntrySignal"] = entry_true >= entry_need
df["ExitSignal"]  = exit_true  >= exit_need

# Backtest (next-day execution; long-only)
with st.spinner("Running backtest..."):
    bt = df[["BTC","EntrySignal","ExitSignal"]].copy()
    bt["Position"] = 0
    in_pos = False
    
    for i in range(1, len(bt)):
        y = bt.index[i-1]
        t = bt.index[i]
        if not in_pos and bt.loc[y,"EntrySignal"]:
            in_pos = True
            bt.loc[t,"Position"] = 1
        elif in_pos and bt.loc[y,"ExitSignal"]:
            in_pos = False
            bt.loc[t,"Position"] = 0
        else:
            bt.loc[t,"Position"] = bt.loc[y,"Position"]
    
    bt["Ret"] = bt["BTC"].pct_change()
    bt["StratRet"] = bt["Ret"] * bt["Position"].shift(1)
    bt["Equity"] = (1 + bt["StratRet"].fillna(0)).cumprod()
    bt["BH_Equity"] = (1 + bt["Ret"].fillna(0)).cumprod()

# Metrics
def max_dd(e):
    rm = e.cummax()
    return (e/rm - 1).min()

total_ret = bt["Equity"].iloc[-1] - 1
bh_ret = bt["BH_Equity"].iloc[-1] - 1
strat_dd = max_dd(bt["Equity"].fillna(1))
bh_dd = max_dd(bt["BH_Equity"].fillna(1))
sr = (bt["StratRet"].mean() / bt["StratRet"].std() * np.sqrt(252)) if bt["StratRet"].std() > 0 else np.nan
time_in_mkt = bt["Position"].mean()

# Display results
st.subheader("📈 Backtest Results")

mcol1, mcol2, mcol3, mcol4 = st.columns(4)
with mcol1:
    st.metric("Strategy Total Return", f"{total_ret:.1%}", f"{(total_ret - bh_ret):.1%}")
with mcol2:
    st.metric("Buy & Hold Total Return", f"{bh_ret:.1%}")
with mcol3:
    st.metric("Max Drawdown (Strategy)", f"{strat_dd:.1%}", f"{(strat_dd - bh_dd):.1%}")
with mcol4:
    st.metric("Sharpe Ratio (Annualized)", f"{sr:.2f}" if not np.isnan(sr) else "N/A")

# Additional metrics
col1, col2 = st.columns(2)
with col1:
    st.metric("Time in Market", f"{time_in_mkt:.1%}")
with col2:
    outperformance = total_ret - bh_ret
    st.metric("Strategy Outperformance", f"{outperformance:.1%}")

# Charts
import plotly.express as px
import plotly.graph_objects as go

st.subheader("📊 Performance Analysis")

# Equity curve
fig_equity = go.Figure()
fig_equity.add_trace(go.Scatter(x=bt.index, y=bt["Equity"], name="Strategy", line=dict(color='blue')))
fig_equity.add_trace(go.Scatter(x=bt.index, y=bt["BH_Equity"], name="Buy & Hold", line=dict(color='orange')))
fig_equity.update_layout(title="Equity Curve: Strategy vs Buy & Hold", yaxis_title="Cumulative Return")
st.plotly_chart(fig_equity, use_container_width=True)

# BTC with signals
sig_plot = bt.copy()
sig_plot["Entry"] = np.where(sig_plot["EntrySignal"], sig_plot["BTC"], np.nan)
sig_plot["Exit"] = np.where(sig_plot["ExitSignal"], sig_plot["BTC"], np.nan)

fig_signals = go.Figure()
fig_signals.add_trace(go.Scatter(x=sig_plot.index, y=sig_plot["BTC"], name="BTC Price", line=dict(color='gray')))
fig_signals.add_trace(go.Scatter(x=sig_plot.index, y=sig_plot["Entry"], mode='markers', name="Entry Signal", 
                                marker=dict(color='green', size=8, symbol='triangle-up')))
fig_signals.add_trace(go.Scatter(x=sig_plot.index, y=sig_plot["Exit"], mode='markers', name="Exit Signal", 
                                marker=dict(color='red', size=8, symbol='triangle-down')))
fig_signals.update_layout(title="BTC Price with Entry/Exit Signals", yaxis_title="BTC Price (USD)")
st.plotly_chart(fig_signals, use_container_width=True)

# Strategy explanation
st.subheader("📋 Strategy Rules")

entry_col, exit_col = st.columns(2)

with entry_col:
    st.markdown("**Entry Conditions:**")
    st.markdown(f"- CBBI ≤ {CBBI_IN_MAX}")
    st.markdown(f"- Coinbase Rank ≥ {CB_RANK_COLD_MIN}")
    st.markdown(f"- BTC underperforming MAG7 (≤ {pctl_in:.0%} percentile)")
    st.markdown("- Within halving accumulation window (18-12 months before)")
    if strict_entry:
        st.markdown("✅ **ALL conditions must be true**")
    else:
        st.markdown("⚠️ **At least 2 conditions must be true**")

with exit_col:
    st.markdown("**Exit Conditions:**")
    st.markdown("- Pi Cycle Top signal triggered")
    st.markdown(f"- CBBI ≥ {CBBI_OUT_MIN}")
    st.markdown(f"- Coinbase Rank ≤ {CB_RANK_HOT_MAX}")
    st.markdown("- Within halving distribution window (12-18 months after)")
    if strict_exit:
        st.markdown("✅ **ALL conditions must be true**")
    else:
        st.markdown("⚠️ **At least 2 conditions must be true**")

# Signal frequency analysis
st.subheader("🔍 Signal Analysis")

signal_stats = pd.DataFrame({
    'Entry Signals': [bt["EntrySignal"].sum()],
    'Exit Signals': [bt["ExitSignal"].sum()],
    'Days in Position': [bt["Position"].sum()],
    'Total Days': [len(bt)]
})

st.dataframe(signal_stats, use_container_width=True)

# Recent signals
st.subheader("📅 Recent Signals (Last 30 days)")
recent_signals = bt.tail(30)[["EntrySignal", "ExitSignal", "Position"]].copy()
recent_signals.index = recent_signals.index.strftime('%Y-%m-%d')
recent_signals.columns = ["Entry Signal", "Exit Signal", "Position"]
st.dataframe(recent_signals, use_container_width=True)

# Disclaimer
st.markdown("---")
st.warning("⚠️ **Disclaimer:** This backtest is for educational purposes only. Past performance does not guarantee future results. Always do your own research and consider your risk tolerance before making investment decisions.")
