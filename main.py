import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
import base64
import os

# IMPORT LOCAL MODULES
import market
import financials
import prediction
import verdict

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Retail Sector Analytics", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #e2e8f0; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #262626; }
    .stat-box { background-color: #111; border: 1px solid #333; border-radius: 4px; padding: 15px; margin-bottom: 10px; text-align: center; }
    .stat-label { color: #888; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .stat-value { color: #fff; font-size: 20px; font-weight: 700; font-family: 'Roboto Mono', monospace; }
    
    /* GLOW EFFECT FOR IMAGES */
    .glow-img {
        border-radius: 8px;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.4); 
        border: 1px solid #333;
        margin-bottom: 20px;
        width: 100%;
        transition: transform 0.3s ease;
    }
    .glow-img:hover {
        transform: scale(1.02);
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.6);
    }

    h4 { background: -webkit-linear-gradient(0deg, #10b981, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 16px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 30px; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 8px; }
    .ticker-wrap { position: fixed; bottom: 0; left: 0; width: 100%; height: 32px; background: #0a0a0a; border-top: 1px solid #333; z-index: 9999; display: flex; align-items: center; }
    .ticker { white-space: nowrap; animation: ticker 60s linear infinite; color: #fff; font-family: 'Roboto Mono', monospace; font-size: 12px; font-weight: 500; padding-left: 100%; }
    @keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
    div[data-testid="stDataFrame"] { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR ---
st.sidebar.markdown("<h3 style='color:#10b981; font-size:13px; font-weight:700; margin-bottom:20px; letter-spacing:1px;'>TRADING DESK</h3>", unsafe_allow_html=True)
cat = st.sidebar.radio("Market Segment", ["Large Cap", "Mid Cap", "Small Cap"])

if cat == "Large Cap":
    comp_map = {"DMart": {"ticker": "DMART.NS", "file": "Avenue Supermarts Ltd."}, "Titan": {"ticker": "TITAN.NS", "file": "Titan Company Ltd."}}
elif cat == "Mid Cap":
    comp_map = {"Kalyan Jewellers": {"ticker": "KALYANKJIL.NS", "file": "Kalyan Jewellers India Ltd."}, "Metro Brands": {"ticker": "METROBRAND.NS", "file": "Metro Brands Ltd."}}
else:
    comp_map = {"Ethos Ltd": {"ticker": "ETHOSLTD.NS", "file": "Ethos Ltd."}, "Arvind Fashions": {"ticker": "ARVINDFASN.NS", "file": "Arvind Fashions Ltd."}}

selected_label = st.sidebar.selectbox("Asset Class", list(comp_map.keys()))
ticker = comp_map[selected_label]["ticker"]
file_name = comp_map[selected_label]["file"]
days_pred = st.sidebar.slider("Projection Window", 1, 30, 14)

def get_img_with_glow(filename):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{encoded}" class="glow-img">'
    return ""

# --- 3. EXECUTION ---
with st.spinner('Fetching Data...'):
    df_market, info = market.fetch_history_data(ticker)
    news_headlines = market.fetch_latest_news(ticker)
    listing_price = market.get_listing_price(df_market)

    # Local Data
    local_data = financials.load_local_data(file_name)
    trend_df = financials.get_trend_data_local(local_data)
    bs_trend = financials.get_balance_sheet_trend(local_data)
    efficiency_vals = financials.get_ratios_latest(local_data)
    growth_data = financials.calculate_growth_metrics(local_data)
    
    curr_ratio = info.get('currentRatio', 0)
    if curr_ratio is None or curr_ratio == 0:
        curr_ratio = financials.get_current_ratio_fallback(local_data)

if not df_market.empty:
    target, f_line, f_dates, metrics, reality, perf, model_name = prediction.run_ensemble_forecast(df_market, days_pred)
    init_price = df_market['Close'].iloc[-1]
    
    memo = verdict.generate_verdict(info, df_market, growth_data, efficiency_vals)

    # --- 4. HEADER ---
    @st.fragment(run_every=5) 
    def show_live_header_fragment():
        live_price = market.fetch_realtime_price(ticker)
        if live_price == 0.0: live_price = init_price
        chg = live_price - df_market['Close'].iloc[-1]
        pct = (chg / df_market['Close'].iloc[-1]) * 100
        col = "#10b981" if chg >= 0 else "#ef4444"
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"<h1 style='margin:0; font-weight:800; font-size:2.5rem; color:#fff;'>{selected_label}</h1>", unsafe_allow_html=True)
            st.markdown(f"<div style='color:#666; font-family:monospace; margin-top:5px;'>NSE: {ticker} | FILE: {file_name}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stat-box" style="border-left: 4px solid {col}; padding: 15px; margin-bottom:0;">
                <div class="stat-label">LIVE MARKET PRICE</div>
                <div style="display:flex; align-items:baseline; gap:10px; justify-content:center;">
                    <div class="stat-value" style="color:{col}">₹{live_price:,.2f}</div>
                    <div style="color:{col}; font-weight:600; font-size:14px;">{chg:+.2f} ({pct:+.2f}%)</div>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown(f"<div class='ticker-wrap'><div class='ticker'>LIVE: {news_headlines}</div></div>", unsafe_allow_html=True)

    show_live_header_fragment()
    st.markdown("---")
    
    t1, t2, t3, t4 = st.tabs(["CHART", "FINANCIALS", "FORECAST", "VERDICT"])

    with t1:
        st.markdown("#### PRICE ACTION (6M)")
        chart_df = df_market.tail(180)
        fig = go.Figure(go.Candlestick(x=chart_df['Date'], open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'], increasing_line_color='#10b981', decreasing_line_color='#ef4444'))
        fig.update_layout(height=450, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='stat-box'><div class='stat-label'>P/E RATIO</div><div class='stat-value'>{info.get('trailingPE',0):.2f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='stat-box'><div class='stat-label'>EPS (TTM)</div><div class='stat-value'>₹{info.get('trailingEps',0):.2f}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='stat-box'><div class='stat-label'>IPO LISTING</div><div class='stat-value'>₹{listing_price:.2f}</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### HISTORICAL PERFORMANCE (10Y GROWTH)")
        
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**REVENUE GROWTH**")
            if not trend_df.empty and "Revenue" in trend_df.columns:
                fig_rev = px.area(trend_df, x=trend_df.index, y="Revenue", color_discrete_sequence=['#3b82f6'])
                fig_rev.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=220, margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                st.plotly_chart(fig_rev, use_container_width=True)
            else: st.info("No Revenue Data")

        with g2:
            st.markdown("**NET PROFIT GROWTH**")
            if not trend_df.empty and "Net Income" in trend_df.columns:
                fig_net = px.bar(trend_df, x=trend_df.index, y="Net Income", color_discrete_sequence=['#10b981'])
                fig_net.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=220, margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                st.plotly_chart(fig_net, use_container_width=True)
            else: st.info("No Net Profit Data")

        g3, g4 = st.columns(2)
        with g3:
            st.markdown("**TOTAL ASSETS**")
            if not bs_trend.empty and "Total Assets" in bs_trend.columns:
                fig_ast = px.line(bs_trend, x=bs_trend.index, y="Total Assets", markers=True, color_discrete_sequence=['#f59e0b'])
                fig_ast.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=220, margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                st.plotly_chart(fig_ast, use_container_width=True)
            else: st.info("No Assets Data")

        with g4:
            st.markdown("**TOTAL LIABILITIES**")
            if not bs_trend.empty and "Total Liabilities" in bs_trend.columns:
                fig_lia = px.bar(bs_trend, x=bs_trend.index, y="Total Liabilities", color_discrete_sequence=['#ef4444'])
                fig_lia.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=220, margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
                st.plotly_chart(fig_lia, use_container_width=True)
            else: st.info("No Liabilities Data")

        st.markdown("---")
        st.markdown("#### EFFICIENCY RATIOS (LATEST)")
        e1, e2, e3 = st.columns(3)
        e1.markdown(f"<div class='stat-box' style='border-left:3px solid #3b82f6'><div class='stat-label'>INVENTORY TURNOVER</div><div class='stat-value'>{efficiency_vals.get('Inventory Turnover', 0):.2f}x</div></div>", unsafe_allow_html=True)
        e2.markdown(f"<div class='stat-box' style='border-left:3px solid #3b82f6'><div class='stat-label'>A/P TURNOVER</div><div class='stat-value'>{efficiency_vals.get('AP Turnover', 0):.2f}x</div></div>", unsafe_allow_html=True)
        e3.markdown(f"<div class='stat-box' style='border-left:3px solid #f59e0b'><div class='stat-label'>CURRENT RATIO</div><div class='stat-value'>{efficiency_vals.get('Current Ratio', 0):.2f}</div></div>", unsafe_allow_html=True)

    with t3:
        st.markdown(f"#### SELECTED MODEL: <span style='color:#10b981'>{model_name.upper()}</span>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='stat-box'><div class='stat-label'>TARGET PRICE</div><div class='stat-value'>₹{target:,.0f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='stat-box'><div class='stat-label'>ACCURACY (R²)</div><div class='stat-value'>{metrics['R2']*100:.1f}%</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='stat-box'><div class='stat-label'>ERROR (RMSE)</div><div class='stat-value'>{metrics['RMSE']:.2f}</div></div>", unsafe_allow_html=True)
        
        hist = df_market.tail(90)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist['Date'], y=hist['Close'], name='History', line=dict(color='#666', width=2)))
        fig.add_trace(go.Scatter(x=f_dates, y=f_line, name='AI Forecast', line=dict(color='#10b981', width=3, dash='dot')))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=450)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### MODEL ERROR COMPARISON")
        if not perf.empty:
             fig_hm = px.imshow(perf[['RMSE', 'MAE', 'MAPE (%)']], text_auto=".2f", aspect="auto", color_continuous_scale="RdYlGn_r", height=200)
             fig_hm.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=0,b=0))
             st.plotly_chart(fig_hm, use_container_width=True)

        # --- RESTORED REALITY CHECK SECTION ---
        st.markdown("#### REALITY CHECK (PREDICTION VS ACTUAL)")
        if reality:
            rc_cols = st.columns(4)
            idx = 0
            for label in ["Today", "Yesterday", "Last Week", "Last Month"]:
                if label in reality:
                    data = reality[label]
                    diff = data['Predicted'] - data['Actual']
                    pct = (diff / data['Actual']) * 100
                    color = "#10b981" if abs(pct) < 2.0 else "#ef4444"
                    with rc_cols[idx]:
                        st.markdown(f"""
                        <div class="stat-box" style="border-top: 3px solid {color}; padding:15px; text-align:center;">
                            <div class="stat-label">{label.upper()}</div>
                            <div style="font-size:12px; color:#888;">ACT: <b style="color:#fff">₹{data['Actual']:,.0f}</b></div>
                            <div style="font-size:12px; color:#888;">PRED: <b style="color:{color}">₹{data['Predicted']:,.0f}</b></div>
                            <div style="font-size:14px; font-weight:bold; color:{color}; border-top:1px solid #333; padding-top:5px;">{diff:+.0f} ({pct:+.1f}%)</div>
                        </div>
                        """, unsafe_allow_html=True)
                    idx += 1

    with t4:
        v_col = memo['Color']
        st.markdown(f"""
        <div style="background:#0a0a0a; border:1px solid {v_col}; padding:25px; border-radius:8px; border-left:6px solid {v_col}; margin-bottom: 25px;">
            <div style="font-size:28px; font-weight:800; color:{v_col}; margin-bottom:15px; letter-spacing:1px;">
                {memo['Rating']}
            </div>
            <div style="color:#e2e8f0; font-size:16px; line-height:1.7; margin-bottom:20px;">
                {memo['Summary']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        i1, i2 = st.columns(2)
        with i1:
            st.markdown(get_img_with_glow("Market_Segment.png"), unsafe_allow_html=True)
        with i2:
            st.markdown(get_img_with_glow("Product_Category.png"), unsafe_allow_html=True)

else: st.error("Connection Error: Unable to fetch market data.")