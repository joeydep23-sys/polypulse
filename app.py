import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import urllib3
urllib3.disable_warnings()

st.set_page_config(page_title="PolyPulse - Market Heatmap", page_icon="📊", layout="wide")

st.markdown("# 📊 PolyPulse - Polymarket Market Heatmap")
st.markdown("**Real-time market intelligence • 200+ markets • Updates every 10s**")

@st.cache_data(ttl=10)
def fetch_markets():
    try:
        response = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"closed": "false", "_limit": 200, "archived": "false"},
            timeout=15,
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else data.get("data", [])
        return []
    except:
        return []

def process_markets(markets):
    processed = []
    now = datetime.utcnow()
    
    for market in markets:
        try:
            question = market.get("question", "")
            
            # Skip sports
            skip = ["nba", "nfl", "nhl", "ncaa", "game", "vs.", "match", "score"]
            if any(w in question.lower() for w in skip):
                continue
            
            tokens = market.get("tokens", [])
            if len(tokens) < 2:
                continue
            
            # Core data
            volume_24h = float(market.get("volume", 0))
            volume_7d = float(market.get("volume7d", 0))
            yes_price = float(tokens[0].get("price", 0))
            no_price = float(tokens[1].get("price", 0))
            liquidity = float(market.get("liquidity", 0))
            
            # Skip tiny markets
            if volume_24h < 100:
                continue
            
            # Growth calculation
            volume_growth = (volume_24h / max(volume_7d/7, 1)) - 1 if volume_7d > 0 else 0
            
            # Parse created date
            created_str = market.get("createdAt", "")
            try:
                if created_str:
                    created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                    hours_old = (now - created_date).total_seconds() / 3600
                else:
                    hours_old = 999
            except:
                hours_old = 999
            
            # Price movement (using volume as proxy since we don't have historical prices)
            price_momentum = volume_growth * abs(yes_price - 0.5) * 100
            
            processed.append({
                "Question": question[:55] + "...",
                "YES": yes_price,
                "NO": no_price,
                "Vol 24h": volume_24h,
                "Vol 7d": volume_7d,
                "Liquidity": liquidity,
                "Growth": volume_growth,
                "Momentum": price_momentum,
                "Hours Old": hours_old,
                "Slug": market.get("slug", "")
            })
        except:
            continue
    
    return processed

markets = fetch_markets()
data = process_markets(markets)
df = pd.DataFrame(data)

# Stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 Markets", len(df))
with col2:
    total_vol = df["Vol 24h"].sum() if not df.empty else 0
    st.metric("💰 24h Volume", f"${total_vol/1e6:.1f}M")
with col3:
    new_count = len(df[df["Hours Old"] < 24]) if not df.empty else 0
    st.metric("🆕 New (24h)", new_count)
with col4:
    st.metric("⏱️ Updated", datetime.now().strftime("%H:%M:%S"))

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔥 Top Volume", 
    "📈 Price Movers", 
    "🆕 New Markets",
    "⚡ Fastest Growing",
    "💎 High Liquidity"
])

with tab1:
    st.markdown("### 🔥 Highest Volume Markets (24h)")
    if not df.empty:
        top = df.nlargest(30, "Vol 24h").copy()
        top["YES"] = top["YES"].apply(lambda x: f"{x:.1%}")
        top["Vol 24h"] = top["Vol 24h"].apply(lambda x: f"${x:,.0f}")
        top["Liquidity"] = top["Liquidity"].apply(lambda x: f"${x:,.0f}")
        display = top[["Question", "YES", "Vol 24h", "Liquidity"]].reset_index(drop=True)
        st.dataframe(display, use_container_width=True, hide_index=True)

with tab2:
    st.markdown("### 📈 Biggest Price Movers (Volume × Price Movement)")
    st.caption("Markets with high volume AND significant price positioning")
    if not df.empty:
        movers = df.nlargest(30, "Momentum").copy()
        movers["YES"] = movers["YES"].apply(lambda x: f"{x:.1%}")
        movers["Vol 24h"] = movers["Vol 24h"].apply(lambda x: f"${x:,.0f}")
        movers["Signal"] = movers["Momentum"].apply(lambda x: f"🔥 {x:.0f}")
        display = movers[["Question", "YES", "Vol 24h", "Signal"]].reset_index(drop=True)
        st.dataframe(display, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("### 🆕 Recently Launched Markets (<24 hours)")
    if not df.empty:
        new_markets = df[df["Hours Old"] < 24].copy()
        if len(new_markets) > 0:
            new_markets = new_markets.nlargest(30, "Vol 24h")
            new_markets["YES"] = new_markets["YES"].apply(lambda x: f"{x:.1%}")
            new_markets["Vol 24h"] = new_markets["Vol 24h"].apply(lambda x: f"${x:,.0f}")
            new_markets["Age"] = new_markets["Hours Old"].apply(lambda x: f"{x:.0f}h ago")
            display = new_markets[["Question", "YES", "Vol 24h", "Age"]].reset_index(drop=True)
            st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            st.info("No markets launched in the last 24 hours")

with tab4:
    st.markdown("### ⚡ Fastest Growing Markets (Volume Growth)")
    if not df.empty:
        growing = df[df["Growth"] > 0.5].nlargest(30, "Growth").copy()
        growing["YES"] = growing["YES"].apply(lambda x: f"{x:.1%}")
        growing["Vol 24h"] = growing["Vol 24h"].apply(lambda x: f"${x:,.0f}")
        growing["Growth"] = growing["Growth"].apply(lambda x: f"+{x:.0%}")
        display = growing[["Question", "YES", "Vol 24h", "Growth"]].reset_index(drop=True)
        st.dataframe(display, use_container_width=True, hide_index=True)

with tab5:
    st.markdown("### 💎 Highest Liquidity Markets")
    if not df.empty:
        liquid = df.nlargest(30, "Liquidity").copy()
        liquid["YES"] = liquid["YES"].apply(lambda x: f"{x:.1%}")
        liquid["Vol 24h"] = liquid["Vol 24h"].apply(lambda x: f"${x:,.0f}")
        liquid["Liquidity"] = liquid["Liquidity"].apply(lambda x: f"${x:,.0f}")
        display = liquid[["Question", "YES", "Vol 24h", "Liquidity"]].reset_index(drop=True)
        st.dataframe(display, use_container_width=True, hide_index=True)

st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**Built by @joeydep23sys** • Free forever • Data from Polymarket Gamma API")
with col2:
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

time.sleep(10)
st.rerun()
