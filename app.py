from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
app = Dash(__name__)
server = app.server
# Load dataset
df = pd.read_csv("UK_Air_Quality_Small.csv")
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.month
pollutants = ["co","nox","no2","o3","so2","pm10","pm25"]

# KPI values
avg_pm25 = round(df["pm25"].mean(),2)
avg_no2 = round(df["no2"].mean(),2)
avg_o3 = round(df["o3"].mean(),2)

app.layout = html.Div([

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------

html.H1(
    "UK Air Quality Analytics Dashboard",
    style={"textAlign":"center","marginBottom":"30px"}
),

# ---------------------------------------------------
# KPI CARDS
# ---------------------------------------------------

html.Div([

html.Div([
html.H4("Average PM2.5"),
html.H2(avg_pm25)
], className="card"),

html.Div([
html.H4("Average NO2"),
html.H2(avg_no2)
], className="card"),

html.Div([
html.H4("Average O3"),
html.H2(avg_o3)
], className="card"),

], style={"display":"flex","justifyContent":"space-around"}),

html.Br(),

# ---------------------------------------------------
# FILTERS
# ---------------------------------------------------

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

], style={"width":"25%","margin":"auto"}),

html.Br(),

# ---------------------------------------------------
# TREND + MONTHLY
# ---------------------------------------------------

html.Div([

dcc.Graph(id="trend_graph", style={"width":"48%"}),

dcc.Graph(id="monthly_graph", style={"width":"48%"})

], style={"display":"flex","justifyContent":"space-between"}),

# ---------------------------------------------------
# SITE COMPARISON + DISTRIBUTION
# ---------------------------------------------------

html.Div([

dcc.Graph(id="site_graph", style={"width":"48%"}),

dcc.Graph(id="distribution_graph", style={"width":"48%"})

], style={"display":"flex","justifyContent":"space-between"}),

# ---------------------------------------------------
# CORRELATION HEATMAP
# ---------------------------------------------------

dcc.Graph(id="correlation_graph"),

# ---------------------------------------------------
# MAP
# ---------------------------------------------------

dcc.Graph(id="map_graph")

])


# ---------------------------------------------------
# CALLBACK
# ---------------------------------------------------

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

    trend = px.line(
        filtered,
        x="date",
        y=pollutant,
        title=f"{pollutant.upper()} Trend at {site}"
    )

    monthly = filtered.groupby("month")[pollutant].mean().reset_index()

    monthly_fig = px.bar(
        monthly,
        x="month",
        y=pollutant,
        title="Monthly Average Pollution"
    )

    site_avg = df.groupby("site")[pollutant].mean().reset_index().head(20)

    site_fig = px.bar(
        site_avg,
        x="site",
        y=pollutant,
        title="Top 20 Sites Pollution"
    )

    dist = px.histogram(
        filtered,
        x=pollutant,
        nbins=40,
        title="Pollution Distribution"
    )

    corr = df[pollutants].sample(min(5000, len(df))).corr()

    corr_fig = px.imshow(
        corr,
        text_auto=True,
        title="Pollutant Correlation Heatmap"
    )

    map_data = df.groupby("site").first().reset_index()

    map_fig = px.scatter_map(
        map_data,
        lat="latitude",
        lon="longitude",
        hover_name="site",
        zoom=4,
        height=500
    )

    return trend, monthly_fig, site_fig, dist, corr_fig, map_fig
# ---------------------------------------------------
# RUN SERVER
# ---------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)