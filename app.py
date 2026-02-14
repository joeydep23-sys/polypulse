import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import urllib3
urllib3.disable_warnings()

st.set_page_config(page_title="PolyPulse", page_icon="📊", layout="wide")

st.markdown("# 📊 PolyPulse - Polymarket Intelligence")
st.markdown("**Real-time market data • Search & filter 200+ markets**")

@st.cache_data(ttl=10)
def fetch_markets():
    try:
        response = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"closed": "false", "_limit": 200},
            timeout=15,
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else data.get("data", [])
        return []
    except:
        return []

def categorize_market(question):
    """Auto-categorize markets"""
    q = question.lower()
    if any(w in q for w in ["trump", "biden", "election", "president", "senate", "congress"]):
        return "Politics"
    if any(w in q for w in ["bitcoin", "eth", "crypto", "btc", "ethereum"]):
        return "Crypto"
    if any(w in q for w in ["fed", "inflation", "recession", "gdp", "unemployment"]):
        return "Economics"
    if any(w in q for w in ["ai", "openai", "gpt", "chatgpt", "google", "apple", "meta"]):
        return "Tech"
    if any(w in q for w in ["climate", "weather", "temperature", "co2"]):
        return "Climate"
    return "Other"

def process_markets(markets, search_query="", category_filter="All"):
    processed = []
    
    for market in markets:
        try:
            question = market.get("question", "")
            
            # Skip sports
            if any(w in question.lower() for w in ["nba", "nfl", "nhl", "ncaa", " vs ", "game", "match"]):
                continue
            
            # Search filter
            if search_query and search_query.lower() not in question.lower():
                continue
            
            # Category filter
            category = categorize_market(question)
            if category_filter != "All" and category != category_filter:
                continue
            
            tokens = market.get("tokens", [])
            if len(tokens) < 2:
                continue
            
            volume_24h = float(market.get("volume", 0))
            if volume_24h < 10:
                continue
            
            yes_price = float(tokens[0].get("price", 0))
            liquidity = float(market.get("liquidity", 0))
            
            processed.append({
                "Category": category,
                "Question": question[:65] + "...",
                "YES": yes_price,
                "Volume 24h": volume_24h,
                "Liquidity": liquidity,
            })
        except:
            continue
    
    return processed

# Fetch data
markets = fetch_markets()

# Search & Filter UI
col1, col2 = st.columns([3, 1])
with col1:
    search = st.text_input("🔍 Search markets", placeholder="e.g. Trump, Bitcoin, AI, Fed...")
with col2:
    category = st.selectbox("📁 Category", ["All", "Politics", "Crypto", "Economics", "Tech", "Climate", "Other"])

data = process_markets(markets, search, category)
df = pd.DataFrame(data)

# Stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 Markets Shown", len(df))
with col2:
    total_vol = df["Volume 24h"].sum() if not df.empty else 0
    st.metric("💰 Total Volume", f"${total_vol/1e6:.2f}M")
with col3:
    st.metric("🌐 Total Available", len(markets))
with col4:
    st.metric("⏱️ Updated", datetime.now().strftime("%H:%M:%S"))

# Tabs
tab1, tab2, tab3 = st.tabs(["🔥 By Volume", "💎 By Liquidity", "📊 All Markets"])

with tab1:
    if not df.empty:
        top = df.nlargest(30, "Volume 24h").copy()
        top["YES"] = top["YES"].apply(lambda x: f"{x:.1%}")
        top["Volume 24h"] = top["Volume 24h"].apply(lambda x: f"${x:,.0f}")
        top["Liquidity"] = top["Liquidity"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(top[["Category", "Question", "YES", "Volume 24h"]], use_container_width=True, hide_index=True)

with tab2:
    if not df.empty:
        liquid = df.nlargest(30, "Liquidity").copy()
        liquid["YES"] = liquid["YES"].apply(lambda x: f"{x:.1%}")
        liquid["Volume 24h"] = liquid["Volume 24h"].apply(lambda x: f"${x:,.0f}")
        liquid["Liquidity"] = liquid["Liquidity"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(liquid[["Category", "Question", "YES", "Liquidity"]], use_container_width=True, hide_index=True)

with tab3:
    if not df.empty:
        display = df.copy()
        display["YES"] = display["YES"].apply(lambda x: f"{x:.1%}")
        display["Volume 24h"] = display["Volume 24h"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(display[["Category", "Question", "YES", "Volume 24h"]], use_container_width=True, hide_index=True)
    else:
        st.info("No markets match your search. Try different keywords or 'All' category.")

st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**Built by [@joeydep23sys](https://x.com/joeydep23sys)** • Free forever • Data: Polymarket Gamma API")
with col2:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

time.sleep(10)
st.rerun()
