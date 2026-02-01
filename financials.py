import pandas as pd
import numpy as np
import os

def load_local_data(company_name):
    datasets = {}
    base_files = {
        "PL": f"Statement of Profit & Loss_{company_name}",
        "BS": f"Assets & Liabilities_{company_name}",
        "Ratios": f"Financial Ratios_{company_name}"
    }
    
    for key, base_name in base_files.items():
        possible_names = [f"{base_name}.csv", f"{base_name}..csv"]
        found_file = None
        for fname in possible_names:
            if os.path.exists(fname):
                found_file = fname
                break
        
        if found_file:
            try:
                df = pd.read_csv(found_file, header=2)
                df.rename(columns={df.columns[0]: 'Metric'}, inplace=True)
                df = df[~df['Metric'].astype(str).str.contains('12 mths|^-|^\s*$', regex=True, na=False)]
                df.set_index('Metric', inplace=True)
                df.index = df.index.astype(str).str.strip()
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
                datasets[key] = df
            except:
                datasets[key] = pd.DataFrame()
        else:
            datasets[key] = pd.DataFrame()
    return datasets

def get_latest_value(df, keywords):
    if df.empty: return 0.0
    for idx in df.index:
        if any(k.lower() in str(idx).lower() for k in keywords):
            row = df.loc[idx]
            for val in row.values[::-1]:
                if pd.notna(val) and val != 0: return val
    return 0.0

def get_current_ratio_fallback(datasets):
    bs = datasets.get("BS", pd.DataFrame())
    if bs.empty: return 0.0
    ca = get_latest_value(bs, ["Current Assets", "Total Current Assets"])
    cl = get_latest_value(bs, ["Current Liabilities", "Total Current Liabilities"])
    if cl > 0: return ca / cl
    return 0.0

def get_ratios_latest(datasets):
    df = datasets.get("Ratios", pd.DataFrame())
    ratios = {}
    target_map = {
        "Inventory Turnover": ["Inventory Turnover"],
        "Current Ratio": ["Current Ratio"],
        "Quick Ratio": ["Quick Ratio"],
        "AP Turnover": ["Trade Payables Turnover", "Creditors Turnover"]
    }
    for key, keywords in target_map.items():
        ratios[key] = get_latest_value(df, keywords)
    return ratios

def get_trend_data_local(datasets):
    """
    Extracts P&L Trend with improved Profit Matching for Graphs.
    """
    df = datasets.get("PL", pd.DataFrame())
    if df.empty: return pd.DataFrame()
    try:
        df_t = df.T
        trend = pd.DataFrame(index=df_t.index)
        
        # Revenue
        for col in df_t.columns:
            if "revenue from operations" in str(col).lower() or "total revenue" in str(col).lower():
                trend["Revenue"] = df_t[col]
                break
                
        # Net Profit (Smart Search)
        found_profit = False
        for col in df_t.columns:
            c = str(col).lower()
            if "profit for the period" in c or "profit for the year" in c or "net profit after tax" in c:
                trend["Net Income"] = df_t[col]
                found_profit = True
                break
        
        if not found_profit:
            for col in df_t.columns:
                c = str(col).lower()
                if "net profit" in c and "before" not in c:
                    trend["Net Income"] = df_t[col]
                    break
        
        # Fallback: Any "Profit" row that looks like bottom line
        if "Net Income" not in trend.columns:
             for col in df_t.columns:
                c = str(col).lower()
                if ("profit" in c or "loss" in c) and not any(x in c for x in ["before", "gross", "operating", "cash"]):
                    trend["Net Income"] = df_t[col]
                    break

        return trend.apply(pd.to_numeric, errors='coerce')
    except: return pd.DataFrame()

def get_balance_sheet_trend(datasets):
    """
    Extracts Balance Sheet Trend for Graphs.
    """
    df = datasets.get("BS", pd.DataFrame())
    if df.empty: return pd.DataFrame()
    try:
        df_t = df.T
        bs_trend = pd.DataFrame(index=df_t.index)
        
        # Assets
        for col in df_t.columns:
            if "Total Assets" in str(col) or "Equity & Liabilities" in str(col):
                bs_trend["Total Assets"] = df_t[col]
                break
        
        # Equity
        for col in df_t.columns:
            if "Total Equity" in str(col) or "Net Worth" in str(col) or str(col).strip() == "Equity":
                bs_trend["Total Equity"] = df_t[col]
                break
                
        # Liabilities
        found_liab = False
        for col in df_t.columns:
            if "Total Liabilities" in str(col) or "Total Debt" in str(col):
                bs_trend["Total Liabilities"] = df_t[col]
                found_liab = True
                break
        
        if not found_liab and "Total Assets" in bs_trend.columns and "Total Equity" in bs_trend.columns:
             bs_trend["Total Liabilities"] = bs_trend["Total Assets"] - bs_trend["Total Equity"]
             
        return bs_trend.apply(pd.to_numeric, errors='coerce')
    except: return pd.DataFrame()

# --- THIS FUNCTION WAS MISSING & IS NOW RESTORED ---
def calculate_growth_metrics(datasets):
    """
    Calculates absolute and % growth for Revenue, Profit, Assets, Liabilities.
    Used for Text Cards if needed.
    """
    growth = {}
    
    def calc_change(df, keywords, exclude=[]):
        if df.empty: return None
        target_row = None
        for idx in df.index:
            s = str(idx).lower()
            if any(k.lower() in s for k in keywords):
                if not any(e.lower() in s for e in exclude):
                    target_row = df.loc[idx]
                    break
        
        if target_row is not None:
            valid_vals = target_row[target_row != 0].dropna()
            if len(valid_vals) >= 2:
                s, e = valid_vals.iloc[0], valid_vals.iloc[-1]
                return {"start": s, "end": e, "abs": e-s, "pct": ((e-s)/abs(s))*100, "years": len(valid_vals)}
        return None

    pl = datasets.get("PL", pd.DataFrame())
    bs = datasets.get("BS", pd.DataFrame())
    
    growth["Revenue"] = calc_change(pl, ["revenue", "sales"])
    growth["Net Profit"] = calc_change(pl, ["profit", "loss"], exclude=["before", "gross", "operating", "cash"])
    growth["Assets"] = calc_change(bs, ["total assets", "equity & liabilities"])
    
    # Smart Liabilities Calculation
    liab = calc_change(bs, ["total liabilities", "total debt"])
    if not liab:
        # Try calculating from Assets - Equity
        try:
            a_growth = growth.get("Assets")
            e_growth = calc_change(bs, ["total equity", "net worth"])
            if a_growth and e_growth:
                s = a_growth["start"] - e_growth["start"]
                e = a_growth["end"] - e_growth["end"]
                liab = {"start": s, "end": e, "abs": e-s, "pct": ((e-s)/abs(s))*100, "years": a_growth["years"]}
        except: pass
    growth["Liabilities"] = liab
    
    return growth