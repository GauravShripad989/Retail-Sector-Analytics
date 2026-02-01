import yfinance as yf
# Example for Trent Ltd (NSE)
data = yf.download("TRENT.NS", start="2015-01-01", end="2025-12-31")
data.to_csv("trent_stock_10yrs.csv")
data_abfrl = yf.download("ABFRL.NS", start="2015-01-01", end="2025-12-31")
data_abfrl.to_csv("ABFRL_stock_10yrs.csv")

# 2. Avenue Supermarts Ltd. (DMart)
data_dmart = yf.download("DMART.NS", start="2015-01-01", end="2025-12-31")
data_dmart.to_csv("DMART_stock_10yrs.csv")

# 3. Shoppers Stop Ltd.
data_shoppers = yf.download("SHOPERSTOP.NS", start="2015-01-01", end="2025-12-31")
data_shoppers.to_csv("Shoppers_Stop_stock_10yrs.csv")

# 4. Spencer'S Retail Ltd.
data_spencers = yf.download("SPENCERS.NS", start="2015-01-01", end="2025-12-31")
data_spencers.to_csv("Spencers_Retail_stock_10yrs.csv")

# 5. V-Mart Retail Ltd.
data_vmart = yf.download("VMART.NS", start="2015-01-01", end="2025-12-31")
data_vmart.to_csv("VMART_stock_10yrs.csv")