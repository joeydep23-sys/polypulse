import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import urllib3
urllib3.disable_warnings()

st.set_page_config(page_title="PolyPulse - Market Heatmap", page_icon="📊", layout="wide")

st.markdown("# 📊 PolyPulse - Polymarket Market Heatmap")
st.markdown("**Real-time market intelligence • Updates every 10s**")

@st.cache_data(ttl=10)
def fetch_markets():
    try:
        response = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"closed": "false", "_limit": 100},
            timeout=15,
            verify=False
        )
        st.sidebar.write(f"API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            markets = data if isinstance(data, list) else data.get("data", [])
            st.sidebar.write(f"Raw markets fetched: {len(markets)}")
            return markets
        return []
    except Exception as e:
        st.sidebar.error(f"Error: {str(e)}")
        return []

def process_markets(markets):
    processed = []
    skipped_sports = 0
    skipped_low_vol = 0
    
    for market in markets:
        try:
            question = market.get("question", "")
            
            # Count sports skips
            skip = ["nba", "nfl", "nhl", "ncaa", "game", "vs.", "match"]
            if any(w in question.lower() for w in skip):
                skipped_sports += 1
                continue
            
            tokens = market.get("tokens", [])
            if len(tokens) < 2:
                continue
            
            volume_24h = float(market.get("volume", 0))
            
            # Lower threshold for testing
            if volume_24h < 10:  # Very low threshold
                skipped_low_vol += 1
                continue
            
            yes_price = float(tokens[0].get("price", 0))
            liquidity = float(market.get("liquidity", 0))
            
            processed.append({
                "Question": question[:70],
                "YES Price": f"{yes_price:.1%}",
                "Volume 24h": f"${volume_24h:,.0f}",
                "Liquidity": f"${liquidity:,.0f}",
            })
        except Exception as e:
            continue
    
    st.sidebar.write(f"Skipped (sports): {skipped_sports}")
    st.sidebar.write(f"Skipped (low vol): {skipped_low_vol}")
    st.sidebar.write(f"Final markets: {len(processed)}")
    
    return processed

markets = fetch_markets()
data = process_markets(markets)
df = pd.DataFrame(data)

# Stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 Markets", len(df))
with col2:
    st.metric("🔄 Raw Fetched", len(markets))
with col3:
    st.metric("📡 API Status", "✅" if markets else "❌")
with col4:
    st.metric("⏱️ Updated", datetime.now().strftime("%H:%M:%S"))

# Show markets
if not df.empty:
    st.markdown("### 🔥 Active Markets")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.error("❌ No markets found! Check sidebar for debug info.")
    
    # Show raw sample
    if markets:
        st.markdown("### 🔍 Sample Raw Market Data")
        st.json(markets[0])

st.markdown("---")
st.markdown("**Built by @joeydep23sys** • Free forever")

time.sleep(10)
st.rerun()
