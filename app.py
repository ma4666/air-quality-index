from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# -------------------------------
# LOAD DATA
# -------------------------------
df = pd.read_csv("UK_Air_Quality_Small.csv")

df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.month

pollutants = ["co","nox","no2","o3","so2","pm10","pm25"]

# KPI values
avg_pm25 = round(df["pm25"].mean(),2)
avg_no2 = round(df["no2"].mean(),2)
avg_o3 = round(df["o3"].mean(),2)

# -------------------------------
# DASH APP
# -------------------------------
app = Dash(__name__)
server = app.server

# -------------------------------
# LAYOUT
# -------------------------------
app.layout = html.Div([

    html.H1("UK Air Quality Analytics Dashboard",
            style={"textAlign":"center","marginBottom":"30px"}),

    # KPI Cards
    html.Div([
        html.Div([html.H4("Average PM2.5"), html.H2(avg_pm25)], className="card"),
        html.Div([html.H4("Average NO2"), html.H2(avg_no2)], className="card"),
        html.Div([html.H4("Average O3"), html.H2(avg_o3)], className="card"),
    ], style={"display":"flex","justifyContent":"space-around"}),

    html.Br(),

    # Filters
    html.Div([
        html.Label("Select Monitoring Site"),
        dcc.Dropdown(
            id="site",
            options=[{"label":i,"value":i} for i in df["site"].unique()],
            value=df["site"].unique()[0]
        ),

        html.Br(),

        html.Label("Select Pollutant"),
        dcc.Dropdown(
            id="pollutant",
            options=[{"label":i.upper(),"value":i} for i in pollutants],
            value="pm25"
        )

    ], style={"width":"30%","margin":"auto"}),

    html.Br(),

    # Graphs
    html.Div([
        dcc.Graph(id="trend_graph"),
        dcc.Graph(id="monthly_graph")
    ]),

    html.Div([
        dcc.Graph(id="site_graph"),
        dcc.Graph(id="distribution_graph")
    ]),

    dcc.Graph(id="correlation_graph"),
    dcc.Graph(id="map_graph")

])

# -------------------------------
# CALLBACK
# -------------------------------
@app.callback(
    Output("trend_graph","figure"),
    Output("monthly_graph","figure"),
    Output("site_graph","figure"),
    Output("distribution_graph","figure"),
    Output("correlation_graph","figure"),
    Output("map_graph","figure"),
    Input("site","value"),
    Input("pollutant","value")
)

def update_dashboard(site, pollutant):

    filtered = df[df["site"] == site]
    filtered = filtered.dropna(subset=[pollutant])

    if filtered.empty:
        return {}, {}, {}, {}, {}, {}

    filtered = filtered.sort_values("date").tail(1000)

    # Trend
    trend = px.line(
        filtered,
        x="date",
        y=pollutant,
        title=f"{pollutant.upper()} Trend",
        color_discrete_sequence=["#00CC96"]
    )

    # Monthly
    monthly = filtered.groupby("month")[pollutant].mean().reset_index()

    monthly_fig = px.bar(
        monthly,
        x="month",
        y=pollutant,
        color=pollutant,
        color_continuous_scale="Reds",
        title="Monthly Average"
    )

    # Site comparison
    site_avg = df.groupby("site")[pollutant].mean().reset_index().head(20)

    site_fig = px.bar(
        site_avg,
        x="site",
        y=pollutant,
        color="site",
        title="Top Sites"
    )

    # Distribution
    dist = px.histogram(
        filtered,
        x=pollutant,
        nbins=40,
        title="Distribution",
        color_discrete_sequence=["#636EFA"]
    )

    # Correlation
    corr = df[pollutants].sample(min(5000, len(df))).corr()

    corr_fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        title="Correlation Heatmap"
    )

    # Map
    map_data = df.groupby("site").first().reset_index()

    map_fig = px.scatter_mapbox(
        map_data,
        lat="latitude",
        lon="longitude",
        hover_name="site",
        zoom=4,
        height=500,
        color="site"
    )

    map_fig.update_layout(mapbox_style="open-street-map")

    return trend, monthly_fig, site_fig, dist, corr_fig, map_fig


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)