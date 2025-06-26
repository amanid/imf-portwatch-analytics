import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
from datetime import timedelta

from src.data_loader import fetch_from_arcgis_api
from src.preprocess import clean_and_engineer
from src.analytics import generate_kpis, detect_anomalies
from src.visualizations import (
    plot_traffic_time_series,
    plot_forecast,
    plot_top_ports,
    plot_import_export,
    plot_traffic_pie,
    plot_heatmap
)

# Initialize Dash app
app = dash.Dash(
    __name__,
    title="IMF PortWatch Dashboard",
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

# Load and preprocess data
raw_data = fetch_from_arcgis_api(sample_fraction=0.05)
full_data = clean_and_engineer(raw_data)

# Default 2-year range
default_end = full_data["DATE"].max()
default_start = default_end - pd.DateOffset(years=2)

# -----------------------------------
# DASHBOARD LAYOUT
# -----------------------------------
app.layout = dbc.Container([
    html.H2("📱 IMF PortWatch Analytics Dashboard", className="text-center my-4 text-primary"),

    dcc.Store(id='cached-data', data=full_data.to_dict('records')),

    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='port-dropdown',
                options=[{'label': p, 'value': p} for p in sorted(full_data['PORT'].unique())],
                placeholder="Select a Port (optional)",
                multi=True
            )
        ], width=4),

        dbc.Col([
            dcc.DatePickerRange(
                id='date-range',
                start_date=default_start,
                end_date=default_end,
                display_format='YYYY-MM-DD',
                min_date_allowed=full_data["DATE"].min(),
                max_date_allowed=full_data["DATE"].max()
            )
        ], width=4),

        dbc.Col([
            dcc.Dropdown(
                id='metric-dropdown',
                options=[
                    {'label': 'Port Calls (Traffic)', 'value': 'TRAFFIC'},
                    {'label': 'Total Import Volume', 'value': 'TOTAL_IMPORT'},
                    {'label': 'Total Export Volume', 'value': 'TOTAL_EXPORT'},
                    {'label': 'Total Trade Volume', 'value': 'TOTAL_TRADE_VOLUME'}
                ],
                value='TRAFFIC'
            )
        ], width=5)
    ], className='mb-3'),

    html.Div(id='kpi-output', className='mb-4'),

    dcc.Tabs(id="tabs", value='forecast', children=[
        dcc.Tab(label='📈 Forecast & Trends', value='forecast', className='fw-bold'),
        dcc.Tab(label='📊 Insights (Top Ports, Pie, Heatmap)', value='insights', className='fw-bold'),
        dcc.Tab(label='📟 Raw Data Snapshot', value='raw', className='fw-bold')
    ], className="mb-3"),

    dcc.Loading(html.Div(id='tab-content'), type="default"),

    html.Div([
        html.Button("⬇️ Download CSV", id="btn_csv", className='me-2 btn btn-outline-primary'),
        dcc.Download(id="download-dataframe-csv"),

        html.Button("⬇️ Download Excel", id="btn_excel", className='btn btn-outline-success'),
        dcc.Download(id="download-dataframe-xlsx")
    ], className='my-4 text-center')
])

# -----------------------------------
# KPI CALLBACK
# -----------------------------------
@app.callback(
    Output('kpi-output', 'children'),
    Input('cached-data', 'data'),
    Input('port-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input('metric-dropdown', 'value')
)
def update_kpis(data, port, start_date, end_date, metric):
    df = pd.DataFrame(data)
    df["DATE"] = pd.to_datetime(df["DATE"])

    if port:
        df = df[df['PORT'].isin(port)]

    df = df[(df['DATE'] >= start_date) & (df['DATE'] <= end_date)]
    df = detect_anomalies(df, metric=metric)

    if df.empty:
        return html.Div("⚠️ No data for KPI computation.", className="text-danger")

    return generate_kpis(df, metric=metric)

# -----------------------------------
# TAB SWITCH CALLBACK
# -----------------------------------
@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value'),
    State('cached-data', 'data'),
    State('port-dropdown', 'value'),
    State('date-range', 'start_date'),
    State('date-range', 'end_date'),
    State('metric-dropdown', 'value')
)
def render_tab(tab, data, port, start_date, end_date, metric):
    df = pd.DataFrame(data)
    df["DATE"] = pd.to_datetime(df["DATE"])

    if port:
        df = df[df['PORT'].isin(port)]

    df = df[(df['DATE'] >= start_date) & (df['DATE'] <= end_date)]
    df = detect_anomalies(df, metric=metric)

    if df.empty:
        return html.Div("⚠️ No data in selected range or port.", className="text-warning")

    if tab == 'forecast':
        return html.Div([
            dcc.Graph(figure=plot_traffic_time_series(df, metric=metric), style={'height': '500px'}),
            dcc.Graph(figure=plot_forecast(df, metric=metric), style={'height': '500px'}),
            dcc.Graph(figure=plot_import_export(df), style={'height': '500px'})
        ])

    elif tab == 'insights':
        return html.Div([
            dcc.Graph(figure=plot_top_ports(df, metric=metric), style={'height': '500px'}),
            dcc.Graph(figure=plot_traffic_pie(df, metric=metric), style={'height': '500px'}),
            dcc.Graph(figure=plot_heatmap(df, metric=metric), style={'height': '500px'})
        ])

    elif tab == 'raw':
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df.columns],
            page_size=20,
            sort_action='native',
            filter_action='native',
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'minWidth': '120px', 'maxWidth': '250px', 'whiteSpace': 'normal'
            },
            style_header={'backgroundColor': '#003366', 'color': 'white'}
        )

# -----------------------------------
# DOWNLOAD CALLBACKS
# -----------------------------------
def filter_df(data, port, start_date, end_date):
    df = pd.DataFrame(data)
    df["DATE"] = pd.to_datetime(df["DATE"])
    if port:
        df = df[df['PORT'].isin(port)]
    return df[(df["DATE"] >= start_date) & (df["DATE"] <= end_date)]

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    State("cached-data", "data"),
    State('port-dropdown', 'value'),
    State('date-range', 'start_date'),
    State('date-range', 'end_date'),
    prevent_initial_call=True
)
def download_csv(n_clicks, data, port, start_date, end_date):
    df = filter_df(data, port, start_date, end_date)
    return dcc.send_data_frame(df.to_csv, "portwatch_filtered.csv")

@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("btn_excel", "n_clicks"),
    State("cached-data", "data"),
    State('port-dropdown', 'value'),
    State('date-range', 'start_date'),
    State('date-range', 'end_date'),
    prevent_initial_call=True
)
def download_excel(n_clicks, data, port, start_date, end_date):
    df = filter_df(data, port, start_date, end_date)
    return dcc.send_data_frame(df.to_excel, "portwatch_filtered.xlsx", sheet_name="Report")

# -----------------------------------
# RUN
# -----------------------------------
if __name__ == '__main__':
    app.run(debug=True)
