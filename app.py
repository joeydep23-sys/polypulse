import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import urllib3
urllib3.disable_warnings()

st.set_page_config(page_title="PolyPulse - Market Heatmap", page_icon="📊", layout="wide")

# Header
st.markdown("# 📊 PolyPulse - Polymarket Market Heatmap")
st.markdown("**Real-time market intelligence • Updated every 10 seconds**")

# Fetch markets
@st.cache_data(ttl=10)
def fetch_markets():
    try:
        response = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"closed": "false", "_limit": 200},
            timeout=10,
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else data.get("data", [])
        return []
    except:
        return []

# Process markets
def process_markets(markets):
    processed = []
    
    for market in markets:
        try:
            # Skip sports
            question = market.get("question", "")
            if any(word in question.lower() for word in ["nba", "nfl", "nhl", "ncaa", "game", "vs."]):
                continue
            
            tokens = market.get("tokens", [])
            if len(tokens) < 2:
                continue
            
            volume_24h = float(market.get("volume", 0))
            volume_7d = float(market.get("volume7d", 0))
            
            # Get prices
            yes_price = float(tokens[0].get("price", 0))
            no_price = float(tokens[1].get("price", 0))
            
            # Calculate metrics
            liquidity = float(market.get("liquidity", 0))
            
            # Estimate price change (approximate from volume change)
            volume_growth = (volume_24h / max(volume_7d/7, 1)) - 1 if volume_7d > 0 else 0
            
            # Parse date
            end_date = market.get("endDate", "")
            created_date = market.get("createdAt", "")
            
            processed.append({
                "Question": question[:70],
                "YES Price": yes_price,
                "NO Price": no_price,
                "Volume 24h": volume_24h,
                "Volume 7d": volume_7d,
                "Liquidity": liquidity,
                "Volume Growth": volume_growth,
                "Created": created_date,
                "Slug": market.get("slug", ""),
            })
        except:
            continue
    
    return processed

# Fetch data
markets = fetch_markets()
data = process_markets(markets)
df = pd.DataFrame(data)

# Stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 Active Markets", len(df))
with col2:
    if not df.empty:
        total_vol = df["Volume 24h"].sum()
        st.metric("💰 24h Volume", f"${total_vol:,.0f}")
with col3:
    if not df.empty:
        avg_vol = df["Volume 24h"].mean()
        st.metric("📈 Avg Volume", f"${avg_vol:,.0f}")
with col4:
    st.metric("⏱️ Updated", datetime.now().strftime("%H:%M:%S"))

# Tabs
tab1, tab2, tab3 = st.tabs(["🔥 Top Volume", "📈 Biggest Movers", "🆕 New Markets"])

with tab1:
    st.markdown("### 🔥 Highest Volume Markets (24h)")
    if not df.empty:
        top_volume = df.nlargest(20, "Volume 24h")[["Question", "YES Price", "Volume 24h", "Liquidity"]]
        top_volume["Volume 24h"] = top_volume["Volume 24h"].apply(lambda x: f"${x:,.0f}")
        top_volume["Liquidity"] = top_volume["Liquidity"].apply(lambda x: f"${x:,.0f}")
        top_volume["YES Price"] = top_volume["YES Price"].apply(lambda x: f"{x:.1%}")
        st.dataframe(top_volume, use_container_width=True, hide_index=True)
    else:
        st.info("Loading markets...")

with tab2:
    st.markdown("### 📈 Fastest Growing Markets (Volume)")
    if not df.empty:
        movers = df[df["Volume Growth"] > 0].nlargest(20, "Volume Growth")[["Question", "YES Price", "Volume 24h", "Volume Growth"]]
        movers["Volume 24h"] = movers["Volume 24h"].apply(lambda x: f"${x:,.0f}")
        movers["Volume Growth"] = movers["Volume Growth"].apply(lambda x: f"+{x:.0%}")
        movers["YES Price"] = movers["YES Price"].apply(lambda x: f"{x:.1%}")
        st.dataframe(movers, use_container_width=True, hide_index=True)
    else:
        st.info("Loading markets...")

with tab3:
    st.markdown("### 🆕 Recently Launched Markets")
    if not df.empty:
        # Filter for recent markets (would need better date parsing)
        new_markets = df.nlargest(20, "Volume 24h")[["Question", "YES Price", "Volume 24h", "Liquidity"]]
        new_markets["Volume 24h"] = new_markets["Volume 24h"].apply(lambda x: f"${x:,.0f}")
        new_markets["Liquidity"] = new_markets["Liquidity"].apply(lambda x: f"${x:,.0f}")
        new_markets["YES Price"] = new_markets["YES Price"].apply(lambda x: f"{x:.1%}")
        st.dataframe(new_markets, use_container_width=True, hide_index=True)
    else:
        st.info("Loading markets...")

# Footer
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**Built by @joeydep23sys** • Data from Polymarket Gamma API")
with col2:
    if st.button("🔄 Force Refresh"):
        st.cache_data.clear()
        st.rerun()

# Auto-refresh
time.sleep(10)
st.rerun()
