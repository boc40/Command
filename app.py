import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Smith Maneuver Command Center", page_icon="🛡️", layout="wide")

st.title("🛡️ Smith Maneuver Command Center")

# --- INITIALIZE DATA ---
# This ensures the app doesn't crash on the first run
if 'portfolio' not in st.session_state:
    # Feel free to change these default Canadian tickers
    st.session_state.portfolio = {
        "RY.TO": {"shares": 10, "cost": 120.00},
        "TD.TO": {"shares": 15, "cost": 85.00},
        "XIC.TO": {"shares": 50, "cost": 32.00}
    }

# --- FUNCTIONS ---
@st.cache_data(ttl=3600)  # Refresh prices every hour
def get_live_prices(tickers):
    prices = {}
    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(period="1d")
            if not data.empty:
                prices[ticker] = data['Close'].iloc[-1]
            else:
                prices[ticker] = 0.0
        except Exception:
            prices[ticker] = 0.0
    return prices

# --- SIDEBAR: MANAGE PORTFOLIO ---
st.sidebar.header("Manage Portfolio")
new_ticker = st.sidebar.text_input("Add Ticker (e.g., VDY.TO)").upper()
new_shares = st.sidebar.number_input("Shares", min_value=0.0, step=1.0)
new_cost = st.sidebar.number_input("Avg Cost ($)", min_value=0.0, step=0.01)

if st.sidebar.button("Add/Update Stock"):
    if new_ticker:
        st.session_state.portfolio[new_ticker] = {"shares": new_shares, "cost": new_cost}
        st.success(f"Updated {new_ticker}")
        st.rerun()

# --- MAIN DASHBOARD ---
tickers = list(st.session_state.portfolio.keys())
current_prices = get_live_prices(tickers)

# Build Dataframe for display
table_data = []
total_market_value = 0.0
total_cost = 0.0

for t in tickers:
    shares = st.session_state.portfolio[t]['shares']
    avg_cost = st.session_state.portfolio[t]['cost']
    current_price = current_prices.get(t, 0.0)
    
    mkt_val = shares * current_price
    cost_basis = shares * avg_cost
    gain_loss = mkt_val - cost_basis
    
    total_market_value += mkt_val
    total_cost += cost_basis
    
    table_data.append({
        "Ticker": t,
        "Shares": shares,
        "Avg Cost": f"${avg_cost:.2f}",
        "Current Price": f"${current_price:.2f}",
        "Market Value": f"${mkt_val:.2f}",
        "Gain/Loss": f"${gain_loss:.2f}"
    })

df = pd.DataFrame(table_data)

# Display Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Market Value", f"${total_market_value:,.2f}")
col2.metric("Total Cost Basis", f"${total_cost:,.2f}")
total_gain = total_market_value - total_cost
col3.metric("Total Profit/Loss", f"${total_gain:,.2f}", delta=f"{total_gain:,.2f}")

st.divider()

# Show the Table
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.write("Your portfolio is currently empty. Add a ticker in the sidebar!")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
