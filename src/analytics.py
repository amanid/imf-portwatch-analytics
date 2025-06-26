import pandas as pd
from dash import html
from prophet import Prophet

# -------------------------
# KPI GENERATOR
# -------------------------
def generate_kpis(df: pd.DataFrame, metric: str = 'TRAFFIC') -> html.Div:
    if df.empty or metric not in df.columns or 'DATE' not in df.columns:
        return html.Div("⚠️ No data available or invalid metric.")

    df = df.copy()
    df['DATE'] = pd.to_datetime(df['DATE'])

    total = df[metric].sum()
    avg = df[metric].mean()
    std = df[metric].std(ddof=0)
    min_val = df[metric].min()
    max_val = df[metric].max()

    anomalies = df['ANOMALY'].sum() if 'ANOMALY' in df.columns else 0
    latest_date = df['DATE'].max().date()
    earliest_date = df['DATE'].min().date()

    # Week-over-week trend
    current_week = df[df['DATE'] >= df['DATE'].max() - pd.Timedelta(days=6)]
    prev_week = df[(df['DATE'] < df['DATE'].max() - pd.Timedelta(days=6)) &
                   (df['DATE'] >= df['DATE'].max() - pd.Timedelta(days=13))]

    current_avg = current_week[metric].mean() if not current_week.empty else 0
    prev_avg = prev_week[metric].mean() if not prev_week.empty else 0

    delta_pct = ((current_avg - prev_avg) / prev_avg * 100) if prev_avg > 0 else None
    trend_symbol = "🔼" if delta_pct and delta_pct > 0 else "🔽" if delta_pct and delta_pct < 0 else "⏺"
    trend_color = "green" if delta_pct and delta_pct > 0 else "red" if delta_pct and delta_pct < 0 else "gray"

    metric_label = metric.title().replace("_", " ")

    return html.Div([
        html.H5(f"📊 {metric_label} KPIs", style={"marginTop": "10px", "marginBottom": "10px"}),
        html.Div(f"📅 Period: {earliest_date} → {latest_date}"),
        html.Div(f"🔢 Total {metric_label}: {total:,.0f}"),
        html.Div(f"📈 Average Daily {metric_label}: {avg:,.0f}"),
        html.Div(f"📉 Std Dev: {std:,.0f} | Min: {min_val:,.0f} | Max: {max_val:,.0f}"),
        html.Div(f"⚠️ Anomalies Detected: {anomalies:,}"),
        html.Div([
            f"{trend_symbol} Δ vs Last Week: ",
            html.Span(f"{delta_pct:.1f}%" if delta_pct is not None else "N/A", style={"color": trend_color})
        ])
    ])


# -------------------------
# ANOMALY DETECTION
# -------------------------
def detect_anomalies(df: pd.DataFrame, method: str = 'zscore', threshold: float = 2.5, metric: str = 'TRAFFIC') -> pd.DataFrame:
    df = df.copy()
    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' not found in DataFrame.")

    if method == 'zscore':
        if df[metric].std() == 0:
            df['ANOMALY'] = False
        else:
            df['Z_SCORE'] = (df[metric] - df[metric].mean()) / df[metric].std()
            df['ANOMALY'] = df['Z_SCORE'].abs() > threshold

    elif method == 'rolling':
        rolling_mean = df[metric].rolling(window=7, min_periods=1).mean()
        rolling_std = df[metric].rolling(window=7, min_periods=1).std()
        df['ANOMALY'] = (df[metric] - rolling_mean).abs() > threshold * rolling_std

    else:
        raise ValueError("Unsupported anomaly detection method: use 'zscore' or 'rolling'.")

    return df

# -------------------------
# FORECASTING
# -------------------------

def forecast_metric(df: pd.DataFrame, metric: str = 'TRAFFIC', periods: int = 30) -> pd.DataFrame:
    if metric not in df.columns:
        raise ValueError(f"Column '{metric}' not found in DataFrame.")

    # Prepare data
    df = df[['DATE', metric]].copy().rename(columns={'DATE': 'ds', metric: 'y'}).dropna()

    # Ensure timezone is removed
    df['ds'] = pd.to_datetime(df['ds']).dt.tz_localize(None)

    if len(df) < 10:
        return pd.DataFrame()

    try:
        model = Prophet(
            daily_seasonality=True,
            yearly_seasonality=True,
            weekly_seasonality=True,
            changepoint_range=0.95
        )
        model.fit(df)

        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)

        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    except Exception as e:
        print(f"❌ Forecasting failed: {e}")
        return pd.DataFrame()


# -------------------------
# DATA HEALTH REPORT
# -------------------------
def get_data_quality_report(df: pd.DataFrame, metric: str = 'TRAFFIC') -> dict:
    return {
        "total_rows": len(df),
        "missing_metric_pct": df[metric].isna().mean() * 100 if metric in df.columns else None,
        "missing_port_pct": df['PORT'].isna().mean() * 100,
        "zero_metric_pct": (df[metric] == 0).mean() * 100 if metric in df.columns else None,
        "min_date": df['DATE'].min(),
        "max_date": df['DATE'].max(),
        "ports_count": df['PORT'].nunique()
    }

# -------------------------
# PORT RANKING
# -------------------------
def get_top_ports(df: pd.DataFrame, metric: str = 'TRAFFIC', top_n: int = 5) -> pd.DataFrame:
    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' not found in DataFrame.")

    return (
        df.groupby("PORT")[metric]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
        .rename(columns={metric: f"TOTAL_{metric.upper()}"})
    )
