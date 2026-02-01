import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from datetime import timedelta
import market 

def run_ensemble_forecast(df, days=30):
    if len(df) < 100: return 0.0, [], [], {}, {}, pd.DataFrame(), "Insufficient Data"
    
    data = market.add_technical_indicators(df)
    data['Date_Ord'] = data['Date'].apply(lambda x: x.toordinal())
    
    feature_cols = ['Date_Ord', 'MA_5', 'MA_20', 'RSI', 'BB_Upper', 'BB_Lower', 'Lag_1', 'Lag_2', 'Lag_5']
    X = data[feature_cols]
    y = data['Close']
    
    split = int(len(data) * 0.9)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    models = {
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=300, max_depth=15, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, max_depth=4, random_state=42)
    }
    
    best_error = float('inf')
    best_model = None
    best_name = ""
    best_metrics = {}
    perf_data = []
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, pred))
        mape = np.mean(np.abs((y_test - pred) / y_test)) * 100
        mae = mean_absolute_error(y_test, pred)
        r2 = r2_score(y_test, pred)
        perf_data.append({"Model": name, "R2 Score": r2, "RMSE": rmse, "MAE": mae, "MAPE (%)": mape})
        
        if rmse < best_error:
            best_error = rmse
            best_model = model
            best_name = name
            best_metrics = {"R2": r2, "RMSE": rmse, "MAE": mae, "MAPE": mape}

    perf_df = pd.DataFrame(perf_data).set_index("Model")
    best_model.fit(X, y)
    
    future_prices = []
    future_dates = []
    last_row = data.iloc[-1]
    curr_state = {
        'Date': last_row['Date'], 'Close': last_row['Close'],
        'Lag_1': last_row['Close'], 'Lag_2': last_row['Lag_1'], 'Lag_5': last_row['Lag_5'],
        'MA_5': last_row['MA_5'], 'MA_20': last_row['MA_20'],
        'BB_Upper': last_row['BB_Upper'], 'BB_Lower': last_row['BB_Lower'], 'RSI': last_row['RSI']
    }
    
    for i in range(days):
        curr_state['Date'] += timedelta(days=1)
        future_dates.append(curr_state['Date'])
        feat = pd.DataFrame([{
            'Date_Ord': curr_state['Date'].toordinal(),
            'MA_5': curr_state['MA_5'], 'MA_20': curr_state['MA_20'],
            'RSI': curr_state['RSI'], 'BB_Upper': curr_state['BB_Upper'], 'BB_Lower': curr_state['BB_Lower'],
            'Lag_1': curr_state['Lag_1'], 'Lag_2': curr_state['Lag_2'], 'Lag_5': curr_state['Lag_5']
        }])
        pred = best_model.predict(feat)[0]
        future_prices.append(pred)
        curr_state['Lag_5'] = curr_state['Lag_2']
        curr_state['Lag_2'] = curr_state['Lag_1']
        curr_state['Lag_1'] = pred
        curr_state['MA_5'] = (curr_state['MA_5'] * 4 + pred) / 5
        
    checkpoints = {"Today": 0, "Yesterday": 1, "Last Week": 7, "Last Month": 30}
    reality_check = {}
    for label, gap in checkpoints.items():
        target_idx = -1 - gap
        if len(data) > abs(target_idx) + 50:
            if gap == 0: train_sub, target_row = data.iloc[:-1], data.iloc[-1]
            else: train_sub, target_row = data.iloc[:target_idx], data.iloc[target_idx]
            
            if "Ridge" in best_name: model_bt = Ridge(alpha=1.0)
            elif "Forest" in best_name: model_bt = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42)
            else: model_bt = GradientBoostingRegressor(n_estimators=150, max_depth=3, learning_rate=0.05, random_state=42)
                
            model_bt.fit(train_sub[feature_cols], train_sub['Close'])
            feat_bt = pd.DataFrame([target_row[feature_cols]])
            pred_val = model_bt.predict(feat_bt)[0]
            reality_check[label] = {
                "Date": target_row['Date'], "Actual": target_row['Close'], "Predicted": pred_val
            }
            
    return future_prices[-1], future_prices, future_dates, best_metrics, reality_check, perf_df, best_name