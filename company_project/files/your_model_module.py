# 전체 코드 구성 (k겹 평가, 시각화 4종, 비교표 생성까지 모두 포함)
import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor


def simple_moving_average(series, window=3):
    return pd.Series(series).rolling(window=window).mean().shift(1).bfill()

def weighted_moving_average(series, weights=[0.1, 0.3, 0.6]):
    window = len(weights)
    def apply_wma(x):
        return np.dot(x, weights)
    return pd.Series(series).rolling(window=window).apply(apply_wma, raw=True).shift(1).bfill()

def exponential_smoothing(series, alpha=0.4):
    result = [series.iloc[0]]
    for t in range(1, len(series)):
        result.append(alpha * series.iloc[t] + (1 - alpha) * result[t - 1])
    return pd.Series(result)

def linear_regression_forecast(df, label):
    df = df.copy()
    df['t'] = np.arange(len(df))
    model = LinearRegression()
    model.fit(df[['t']], df[[label]])
    return pd.Series(model.predict(df[['t']]).flatten())

def run_kfold_timeseries_xgb(df, label, k=5, data_type='Production'):
    df = df[['Date', label]].dropna().reset_index(drop=True)
    df['ma'] = simple_moving_average(df[label])
    df['wma'] = weighted_moving_average(df[label])
    df['exp'] = exponential_smoothing(df[label])
    df['reg'] = linear_regression_forecast(df, label)

    feature_cols = ['ma', 'wma', 'exp', 'reg']
    X = df[feature_cols]
    y = df[label]

    tscv = TimeSeriesSplit(n_splits=k)
    metrics = []
    rmse_list, mae_list, mad_list, r2_list = [], [], [], []

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = XGBRegressor(n_estimators=100, max_depth=4, random_state=429)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        rmse = mean_squared_error(y_test, preds) ** 0.5
        mae = mean_absolute_error(y_test, preds)
        mad = np.mean(np.abs(y_test - preds))
        r2 = r2_score(y_test, preds)

        rmse_list.append(rmse)
        mae_list.append(mae)
        mad_list.append(mad)
        r2_list.append(r2)

        metrics.append({
            "Fold": fold,
            "Type": data_type,
            "RMSE": round(rmse, 3),
            "MAE": round(mae, 3),
            "MAD": round(mad, 3),
            "R²": round(r2, 3)
        })

    avg_row = {
        "Fold": "avg",
        "Type": data_type,
        "RMSE": round(np.mean(rmse_list), 3),
        "MAE": round(np.mean(mae_list), 3),
        "MAD": round(np.mean(mad_list), 3),
        "R²": round(np.mean(r2_list), 3)
    }
    metrics.append(avg_row)

    return pd.DataFrame(metrics)

def train_and_predict(df, label):
    df = df[['Date', label]].dropna().reset_index(drop=True)
    df['ma'] = simple_moving_average(df[label])
    df['wma'] = weighted_moving_average(df[label])
    df['exp'] = exponential_smoothing(df[label])
    df['reg'] = linear_regression_forecast(df, label)

    feature_cols = ['ma', 'wma', 'exp', 'reg']
    train_df = df.dropna()
    model = XGBRegressor(n_estimators=100, max_depth=4, random_state=429)
    model.fit(train_df[feature_cols], train_df[label])
    df[f'{label}_Predicted'] = model.predict(df[feature_cols].fillna(0))
    return df

def run_model_and_get_outputs(df_product, df_sale, product_name):
    df_product = train_and_predict(df_product, product_name)
    df_sale = train_and_predict(df_sale, product_name)

    figs = []
    fig_size = (15, 5)

    forecast_start = df_product['Date'].iloc[-30]
    actual_mask = df_product['Date'] < forecast_start

    # 1번: 생산량 예측 전체
    fig1, ax1 = plt.subplots(figsize=fig_size)
    sns.lineplot(x='Date', y=product_name, data=df_product[actual_mask], label='Actual', linewidth=2, ax=ax1)
    sns.lineplot(x='Date', y=f'{product_name}_Predicted', data=df_product, label='Predicted', linestyle='--', color='orange', ax=ax1)
    ax1.axvline(x=forecast_start, color='gray', linestyle='--', label='Forecast Start')
    ax1.set_title(f"{product_name} - Production Predict: Actual vs Predicted")
    ax1.set_xlabel("Date"); ax1.set_ylabel("Quantity"); ax1.legend(); ax1.tick_params(axis='x', rotation=45)
    figs.append(fig1)

    # 2번: 판매량 예측 전체
    fig2, ax2 = plt.subplots(figsize=fig_size)
    sns.lineplot(x='Date', y=product_name, data=df_sale[df_sale['Date'] < forecast_start], label='Actual', linewidth=2, ax=ax2)
    sns.lineplot(x='Date', y=f'{product_name}_Predicted', data=df_sale, label='Predicted', linestyle='--', color='orange', ax=ax2)
    ax2.axvline(x=forecast_start, color='gray', linestyle='--', label='Forecast Start')
    ax2.set_title(f"{product_name} - Sale Predict: Actual vs Predicted")
    ax2.set_xlabel("Date"); ax2.set_ylabel("Quantity"); ax2.legend(); ax2.tick_params(axis='x', rotation=45)
    figs.append(fig2)

    # 예측 부분 자르기
    forecast_mask = df_product['Date'].isin(df_product['Date'].iloc[-30:])

    # 3번: 예측 생산 vs 판매 (예측 부분만)
    merged = pd.merge(
        df_product[forecast_mask][['Date', f'{product_name}_Predicted']],
        df_sale[forecast_mask][['Date', f'{product_name}_Predicted']],
        on='Date', suffixes=('_Production', '_Sale')
    )
    fig3, ax3 = plt.subplots(figsize=fig_size)
    ax3.plot(merged['Date'], merged[f'{product_name}_Predicted_Production'], label='Predicted Production')
    ax3.plot(merged['Date'], merged[f'{product_name}_Predicted_Sale'], label='Predicted Sale')
    ax3.set_title('Predicted Production vs Sale (Forecast Only)')
    ax3.legend()
    figs.append(fig3)

    # 4번: 차이 시각화 (예측 부분만)
    merged['Difference'] = merged[f'{product_name}_Predicted_Production'] - merged[f'{product_name}_Predicted_Sale']
    status = merged['Difference'].apply(lambda x: 'Overproduction' if x > 0 else 'Underproduction' if x < 0 else 'Balanced')
    colors = ['green' if s == 'Overproduction' else 'red' if s == 'Underproduction' else 'gray' for s in status]

    fig4, ax4 = plt.subplots(figsize=fig_size)
    ax4.bar(merged['Date'], merged['Difference'], color=colors)
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', label='Underproduction'),
        Patch(facecolor='green', label='Overproduction')
    ]
    ax4.legend(handles=legend_elements, title='Status')
    ax4.set_title(f'{product_name} - Forecast: Production vs Sale Difference (Forecast Only)')
    ax4.set_xlabel('Date'); ax4.set_ylabel('Production - Sale')
    ax4.tick_params(axis='x', rotation=45)
    figs.append(fig4)

    forecast_table = pd.DataFrame({
        'Date': merged['Date'],
        'Predicted_Production': merged[f'{product_name}_Predicted_Production'],
        'Predicted_Sale': merged[f'{product_name}_Predicted_Sale'],
        'Difference (Prod - Sale)': merged['Difference'],
        'Status': status
    })

    metrics_product = run_kfold_timeseries_xgb(df_product, product_name, k=5, data_type="Production")
    metrics_sale = run_kfold_timeseries_xgb(df_sale, product_name, k=5, data_type="Sale")
    eval_metrics = pd.concat([metrics_product, metrics_sale], ignore_index=True)

    return forecast_table, eval_metrics, figs[0], figs[1], figs[2], figs[3]
