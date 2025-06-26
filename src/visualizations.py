import plotly.express as px
import plotly.graph_objects as go
from src.analytics import forecast_metric, get_top_ports

DEFAULT_HEIGHT = 500
DEFAULT_MARGIN = dict(l=40, r=40, t=60, b=40)

# -------------------------
# TIME SERIES LINE PLOT
# -------------------------
def plot_traffic_time_series(df, metric='TRAFFIC', show_rolling_avg=True):
    if df.empty or metric not in df.columns:
        return go.Figure().update_layout(title='No data available.', height=DEFAULT_HEIGHT)

    fig = px.line(
        df,
        x='DATE',
        y=metric,
        color='PORT',
        title=f'{metric.replace("_", " ").title()} Over Time',
        labels={metric: metric.replace("_", " ").title()}
    )

    if 'ANOMALY' in df.columns and metric in df.columns:
        anomalies = df[df['ANOMALY']]
        if not anomalies.empty:
            fig.add_trace(go.Scatter(
                x=anomalies['DATE'],
                y=anomalies[metric],
                mode='markers',
                name='Anomalies',
                marker=dict(color='red', size=8, symbol='x'),
                hovertemplate='Anomaly<br>Date=%{x}<br>Value=%{y}<extra></extra>'
            ))

    if show_rolling_avg and metric == 'TRAFFIC' and 'ROLLING_AVG_TRAFFIC' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['DATE'],
            y=df['ROLLING_AVG_TRAFFIC'],
            name='7-day Avg',
            mode='lines',
            line=dict(dash='dot', width=2),
            opacity=0.6
        ))

    fig.update_layout(
        height=DEFAULT_HEIGHT,
        autosize=False,
        hovermode='x unified',
        margin=DEFAULT_MARGIN,
        uirevision=True,
        template='plotly_white'
    )
    return fig


# -------------------------
# PROPHET FORECAST PLOT
# -------------------------
def plot_forecast(df, metric='TRAFFIC'):
    forecast_df = forecast_metric(df, metric=metric)
    if forecast_df.empty:
        return go.Figure().update_layout(title='Forecast (Insufficient data)', height=DEFAULT_HEIGHT)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=forecast_df['ds'], y=forecast_df['yhat'],
        mode='lines', name='Forecast',
        line=dict(color='blue', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df['ds'], y=forecast_df['yhat_upper'],
        mode='lines', name='Upper Bound',
        line=dict(dash='dot'), opacity=0.2, showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df['ds'], y=forecast_df['yhat_lower'],
        fill='tonexty',
        mode='lines', name='Lower Bound',
        line=dict(dash='dot'), opacity=0.2, showlegend=False
    ))

    fig.update_layout(
        title=f'30-Day Forecast for {metric.replace("_", " ").title()}',
        hovermode='x unified',
        xaxis_title='Date',
        yaxis_title=metric.replace("_", " ").title(),
        height=DEFAULT_HEIGHT,
        autosize=True,
        width=None,
        margin=DEFAULT_MARGIN,
        uirevision=True,
        template='plotly_white'
    )
    return fig


# -------------------------
# TOP N PORTS BAR CHART
# -------------------------
def plot_top_ports(df, metric='TRAFFIC', top_n=5):
    if df.empty or metric not in df.columns:
        return go.Figure().update_layout(title='Top Ports (No data available)', height=DEFAULT_HEIGHT)

    top_df = get_top_ports(df, metric=metric, top_n=top_n)
    fig = px.bar(
        top_df,
        x='PORT',
        y=f'TOTAL_{metric.upper()}',
        title=f'Top {top_n} Ports by {metric.replace("_", " ").title()}',
        labels={f'TOTAL_{metric.upper()}': metric.replace("_", " ").title()},
        text_auto='.2s'
    )

    fig.update_layout(
        xaxis_title='Port',
        yaxis_title=metric.replace("_", " ").title(),
        height=DEFAULT_HEIGHT,
        autosize=True,
        width=None,
        margin=DEFAULT_MARGIN,
        uirevision=True,
        template='plotly_white'
    )
    return fig


# -------------------------
# IMPORT vs EXPORT LINE PLOT
# -------------------------
def plot_import_export(df):
    if df.empty or not {'TOTAL_IMPORT', 'TOTAL_EXPORT'}.issubset(df.columns):
        return go.Figure().update_layout(title='Import/Export data not available.', height=DEFAULT_HEIGHT)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['DATE'], y=df['TOTAL_IMPORT'],
        mode='lines', name='Total Import',
        line=dict(color='green')
    ))
    fig.add_trace(go.Scatter(
        x=df['DATE'], y=df['TOTAL_EXPORT'],
        mode='lines', name='Total Export',
        line=dict(color='orange')
    ))

    fig.update_layout(
        title='Import vs Export Over Time',
        hovermode='x unified',
        xaxis_title='Date',
        yaxis_title='Trade Volume',
        height=DEFAULT_HEIGHT,
        autosize=True,
        width=None,
        margin=DEFAULT_MARGIN,
        uirevision=True,
        template='plotly_white'
    )
    return fig


# -------------------------
# PIE CHART - TRAFFIC BY COUNTRY
# -------------------------
def plot_traffic_pie(df, metric='TRAFFIC'):
    if df.empty or 'COUNTRY' not in df.columns or metric not in df.columns:
        return go.Figure().update_layout(title='Pie Chart (Data unavailable)', height=DEFAULT_HEIGHT)

    summary = df.groupby("COUNTRY")[metric].sum().sort_values(ascending=False).head(10)
    fig = px.pie(
        names=summary.index,
        values=summary.values,
        title=f'Top Countries by {metric.replace("_", " ").title()}',
        hole=0.4
    )
    fig.update_traces(textinfo='percent+label', pull=[0.05]*len(summary))
    fig.update_layout(
        height=DEFAULT_HEIGHT,
        autosize=True,
        width=None,
        margin=DEFAULT_MARGIN,
        uirevision=True,
        template='plotly_white'
    )
    return fig


# -------------------------
# HEATMAP - TRAFFIC BY PORT/DAY
# -------------------------
def plot_heatmap(df, metric='TRAFFIC'):
    if df.empty or metric not in df.columns:
        return go.Figure().update_layout(title='Heatmap (No data available)', height=DEFAULT_HEIGHT)

    pivot = df.pivot_table(index='PORT', columns='DATE', values=metric, aggfunc='sum').fillna(0)

    fig = px.imshow(
        pivot,
        labels=dict(x="Date", y="Port", color=metric.replace("_", " ").title()),
        aspect="auto",
        title=f'Heatmap of {metric.replace("_", " ").title()} by Port and Date',
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        height=DEFAULT_HEIGHT,
        autosize=True,
        width=None,
        margin=DEFAULT_MARGIN,
        xaxis_tickangle=-45,
        uirevision=True,
        template='plotly_white'
    )
    return fig
