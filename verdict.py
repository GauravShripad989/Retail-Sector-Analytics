import pandas as pd

def generate_verdict(info, df_price, growth_data, efficiency_data):
    """
    Generates a generalized investment thesis in a precise pointers paragraph format.
    """
    # --- DATA EXTRACTION ---
    curr_price = df_price['Close'].iloc[-1]
    ma_50 = df_price['Close'].rolling(50).mean().iloc[-1]
    pe = info.get('trailingPE', 0)
    rev_growth = growth_data.get('Revenue', {}).get('pct', 0)
    
    # --- RATING LOGIC ---
    score = 0
    if curr_price > ma_50: score += 1
    if rev_growth > 10: score += 1
    if 0 < pe < 60: score += 1
    
    if score >= 2:
        rating = "ACCUMULATE / BUY"
        color = "#10b981" # Green
        action_phrase = "considering accumulating positions on dips"
    elif score >= 0:
        rating = "HOLD"
        color = "#eab308" # Yellow
        action_phrase = "maintaining current exposure while awaiting clearer signals"
    else:
        rating = "REDUCE / SELL"
        color = "#ef4444" # Red
        action_phrase = "reducing exposure or waiting for a deeper correction"

    # --- TEXT GENERATION (NO INDENTATION TO FIX SCROLLING) ---
    tech_status = 'above' if curr_price > ma_50 else 'below'
    tech_signal = 'favorable short-term momentum' if curr_price > ma_50 else 'short-term technical weakness'
    
    fund_status = 'robust' if rev_growth > 0 else 'subdued'
    fund_signal = 'capture market share' if rev_growth > 0 else 'navigate demand headwinds'
    
    val_status = 'reasonably valued' if pe < 60 else 'trading at a premium'
    val_signal = 'balanced' if pe < 60 else 'already priced in'

    # Note: Strings are flush left to prevent Markdown code blocks
    summary = f"""**Detailed Investment Analysis:**

* **Technical Momentum:** The stock is currently trading {tech_status} its key 50-day moving average, indicating {tech_signal}.
* **Fundamental Trajectory:** Historical data shows a {fund_status} revenue trajectory with a growth of {rev_growth:.1f}%, reflecting the company's ability to {fund_signal}.
* **Valuation Context:** With a P/E ratio of {pe:.1f}, the stock appears to be {val_status}, implying that future growth expectations are {val_signal}.

**Strategic Conclusion:** Based on the confluence of these factors, the overall recommendation is **{rating}**. Investors are advised to proceed by {action_phrase}, keeping a close watch on the efficiency metrics and broader market sentiment."""

    return {
        "Rating": rating,
        "Color": color,
        "Summary": summary,
        "Signals": [] # Not used in new layout
    }