import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- FILE PATHS FOR SYNOLOGY PERSISTENCE ---
# These files will stay on your NAS drive even if the app restarts
PORTFOLIO_FILE = "moore_portfolio.csv"
LEDGER_FILE = "moore_tax_ledger.csv"

# --- DEFAULT STATE ---
DEFAULT_PORTFOLIO = {'PEY.TO': 1814, 'RS.TO': 2218, 'DFN.TO': 2703, 'HHIC.TO': 1510}
LOAN_AMOUNT = 102582.18
HELOC_RATE = 0.0445  # 4.45%

# --- PERSISTENCE LOGIC: LOADING DATA ---
def load_data():
    if os.path.exists(PORTFOLIO_FILE):
        return pd.read_csv(PORTFOLIO_FILE).set_index('Asset')['Shares'].to_dict()
    return DEFAULT_PORTFOLIO

def load_ledger():
    if os.path.exists(LEDGER_FILE):
        return pd.read_csv(LEDGER_FILE).to_dict('records')
    return []

# Initialize state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = load_data()
if 'tax_ledger' not in st.session_state:
    st.session_state.tax_ledger = load_ledger()

st.set_page_config(page_title="Moore Command Center", layout="wide")

# --- SIDEBAR: MANAGE ASSETS & LOG TAXES ---
with st.sidebar:
    st.header("🛒 Manage Holdings")
    ticker = st.selectbox("Asset", list(st.session_state.portfolio.keys()))
    new_shares = st.number_input("Shares", value=st.session_state.portfolio[ticker])
    
    if st.button("Update and Save to NAS"):
        st.session_state.portfolio[ticker] = new_shares
        # Save to CSV on Synology
        pd.DataFrame(list(st.session_state.portfolio.items()), columns=['Asset', 'Shares']).to_csv(PORTFOLIO_FILE, index=False)
        st.success("Saved to Disk!")

    st.divider()
    st.header("📝 Log Mortgage Payment")
    pay_date = st.date_input("Date", datetime.now())
    pay_amt = st.number_input("Amount ($)", value=998.0)
    
    if st.button("Log & Secure Trail"):
        new_entry = {"Date": pay_date, "Amount": pay_amt, "Type": "Dividend Payment"}
        st.session_state.tax_ledger.append(new_entry)
        # Append to Ledger CSV on Synology
        pd.DataFrame(st.session_state.tax_ledger).to_csv(LEDGER_FILE, index=False)
        st.toast("CRA Trail Updated!")

# --- MAIN DASHBOARD: REAL-TIME RISK ---
st.title("🛡️ Smith Maneuver Command Center")

@st.cache_data(ttl=300) # Refresh data every 5 mins
def fetch_prices(tickers):
    return {t: yf.Ticker(t).history(period="1d")['Close'].iloc[-1] for t in tickers}

prices = fetch_prices(list(st.session_state.portfolio.keys()))
total_val = sum(prices[t] * st.session_state.portfolio[t] for t in st.session_state.portfolio)

# Top Level Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Portfolio Value", f"${total_val:,.2f}")
m2.metric("Net Equity", f"${total_val - LOAN_AMOUNT:,.2f}")
m3.metric("Annual Tax Deduction", f"${(LOAN_AMOUNT * HELOC_RATE):,.2f}")

# --- SELL SIGNALS ---
st.subheader("⚠️ Smart Signals")
s1, s2 = st.columns(2)

with s1:
    st.write("**Price Cues**")
    if prices['PEY.TO'] > 26.00:
        st.success(f"PEY Target Hit! Price: ${prices['PEY.TO']:.2f}. Consider harvesting gains.")
    if prices['DFN.TO'] < 7.40:
        st.error(f"DFN Risk! Price: ${prices['DFN.TO']:.2f}. NAV threshold danger.")

with s2:
    st.write("**Strategy Health**")
    est_income = total_val * 0.11 # 11% average
    if est_income < (LOAN_AMOUNT * HELOC_RATE):
        st.error("DANGER: Interest cost is outrunning dividends.")
    else:
        st.info(f"Healthy: Income exceeds interest by approx. ${est_income/12 - (LOAN_AMOUNT*HELOC_RATE/12):.2f}/mo")

# --- HISTORICAL TAX LEDGER ---
st.divider()
st.subheader("📅 Tax Ledger & Audit Trail")
if st.session_state.tax_ledger:
    st.dataframe(pd.DataFrame(st.session_state.tax_ledger), use_container_width=True)
else:
    st.info("No payments logged. Your ledger will appear here once you log your first mortgage prepayment.")
