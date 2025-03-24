import datetime
import numpy as np 
import pandas as pd 
import dash 
from dash import dcc, html
import dash_bootstrap_components as dbc 
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go 
import plotly.io as pio 
from sklearn.decomposition import PCA 
from openbb import obb


obb.user.preferences.output_type = "dataframe"

# Pick the styling, chart templates and initialize the app
pio.templates.default = "plotly"
app = dash.Dash(__name__ , external_stylesheets=[
    dbc.themes.BOOTSTRAP
])

# Here we are building the components of the user interface
# The text field to the enter the list of ticker symbols
ticker_field = [
    html.Label("Enter Ticker Symbols:"),
    dcc.Input(
        id="ticker-input",
        type="text",
        placeholder="Enter Tickers separated by commas (e.g. AAPL,MSFT)",
        style={"width": "50%"}
    ),
]

# The dropdown to select the number of components
components_field = [
    html.Label("Select Number of Components:"),
    dcc.Dropdown(
        id="component-dropdown",
        options=[{"label": i, "value": i} for i in range(1, 6)],
        value=3,
        style={"width": "50%"}
    ),
]

# The date picker to select the range of data
date_picker_field = [
    html.Label("Select Date Range:"), # Label for date picker
    dcc.DatePickerRange(
        id="date-picker",
        start_date=datetime.datetime.now() - datetime.timedelta(
            365 * 3
        ),
        end_date=datetime.datetime.now(),
        # Default to today's date
        display_format="YYYY-MM-DD",
    ),
]

# Submit button to run the app
submit = [
    html.Button("Submit", id="submit-button"),
]

# Here we are combining the form elements and placeholders for visualizations form the appl layout
app.layout = dbc.Container(
    [
        html.H1("PCA on Stock Returns"),
        dbc.Row([dbc.Col(ticker_field)]),
        dbc.Row([dbc.Col(components_field)]),
        dbc.Row([dbc.Col(date_picker_field)]),
        dbc.Row([dbc.Col(submit)]),
        dbc.Row(
            [
                dbc.Col([dcc.Graph(id="bar-chart")], width=4),
                dbc.Col([dcc.Graph(id="line-chart")], width=4),
                dbc.Col([dcc.Graph(id="scatter-plot")], width=4),
            ]
        ),
    ]
)

# Here we are implementing the function that updates the chars upon user input
@app.callback(
    [
        Output("bar-chart", "figure"),
        Output("line-chart", "figure"),
        Output("scatter-plot", "figure"),
    ],
    [Input("submit-button", "n_clicks")],
    [
        State("ticker-input", "value"),
        State("component-dropdown", "value"),
        State("date-picker", "start_date"),
        State("date-picker", "end_date")
    ],
)
def update_graphs(n_clicks, tickers, n_components, start_date, end_date):

    # Create empty figures for initial load or when no tickers provided
    empty_fig = go.Figure()

    # If n_clicks is None(app just loaded) or no tickers provided, return empty figures
    if n_clicks is None or not tickers:
        return empty_fig, empty_fig, empty_fig
        
    try:
        # Parse inputs from the user
        tickers = tickers.split(",")

        # Process the date strings
        if isinstance(start_date, str):
        # Convert date strings to datetime objects
            start_date = datetime.datetime.strptime(start_date.split("T")[0], "%Y-%m-%d").date()
        else:
            start_date = start_date.date() if hasattr(start_date, 'date') else start_date

        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date.split("T")[0], "%Y-%m-%d").date()
        else:
            end_date = end_date.date() if hasattr(end_date, 'date') else end_date
        # Download historical stock data
        data = obb.equity.price.historical(
            tickers, start_date=start_date, end_date=end_date, provider="yfinance"
        ).pivot(columns="symbol", values="close")
        # Calculate daily returns
        daily_returns = data.pct_change().dropna()

        # Apply PCA to the daily returns
        pca = PCA(n_components=n_components)
        pca.fit(daily_returns)
        explained_var_ratio = pca.explained_variance_ratio_

        # Create a bar chart for individual explained variance
        bar_chart = go.Figure(
            data=[
                go.Bar(
                    x=["PC" + str(i + 1) for i in range(n_components)],
                    y=explained_var_ratio,
                )              
            ],
            layout=go.Layout(
                title="Explained Variance by Component",
                xaxis=dict(title="Principal Component"),
                yaxis=dict(title="Explained Variance"),
            ),
        )


        # Create a line chart for cumulative explained variance
        cumulative_var_ratio = np.cumsum(explained_var_ratio)
        line_chart = go.Figure(
            data=[
                go.Scatter(
                    x=["PC" + str(i + 1) for i in range(n_components)],
                    y=cumulative_var_ratio,
                    mode="lines+markers",
                )
            ],
            layout=go.Layout(
                title="Cumulative Explained Variance",
                xaxis=dict(title="Principal Component"),
                yaxis=dict(title="Cumulative Explained Variance"),
            ),
        )

        # Compute factor exposures
        X = np.asarray(daily_returns)

        factor_returns = pd.DataFrame(
            columns=["f" + str(i + 1) for i in range(n_components)],
            index=daily_returns.index,
            data=X.dot(pca.components_.T),
        )

        # Calculate factor exposures for each stock
        factor_exposures = pd.DataFrame(
            index=["f" + str(i + 1) for i in range(n_components)],
            columns=daily_returns.columns,
            data=pca.components_,
        ).T

        labels = factor_exposures.index
        data = factor_exposures.values

        # Create a scatter plot for the first two factors
        scatter_plot = go.Figure(
            data=[
                go.Scatter(
                    x=factor_exposures["f1"] if "f1" in factor_exposures.columns else [],
                    y=factor_exposures["f2"] if "f2" in factor_exposures.columns and n_components > 1 else [],
                    mode="markers+text",
                    text=labels,
                    textposition="top center",
                )
            ],
            layout=go.layout(
                title="Scatter Plot of First Two Factors",
                xaxis=dict(title="Factor 1"),
                yaxis=dict(title="Factor 2"),
            ),
        )

        return bar_chart, line_chart, scatter_plot

    except Exception as e:
        print(f"Error in callback: {e}")
        # Return empty figures in case of error
        return empty_fig, empty_fig, empty_fig

if __name__ == "__main__":
    # Run the Dash app
    app.run(debug=True)


