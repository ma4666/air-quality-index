from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px


df = pd.read_csv(
    "https://docs.google.com/spreadsheets/d/1D7N-VkG3cjUF2jMzbFyA7b-vPwdvmHih8Ct_RB3_p8E/export?format=csv"
)

df.columns = df.columns.str.strip().str.lower()

print("Columns:", df.columns)


df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["month"] = df["date"].dt.month

# Ensure string consistency
df["site"] = df["site"].astype(str).str.strip().str.lower()

pollutants = ["pm25", "no2", "o3", "so2", "pm10"]


def calculate_aqi(x):
    if x <= 12: return 50
    elif x <= 35.4: return 100
    elif x <= 55.4: return 150
    elif x <= 150.4: return 200
    elif x <= 250.4: return 300
    else: return 400


def get_recommendation(aqi):
    if aqi <= 50:
        return "Good air quality. Enjoy outdoor activities."
    elif aqi <= 100:
        return "Moderate. Sensitive people reduce outdoor activity."
    elif aqi <= 150:
        return "Unhealthy for sensitive groups."
    elif aqi <= 200:
        return "Unhealthy. Wear mask."
    elif aqi <= 300:
        return "Very unhealthy. Stay indoors."
    else:
        return "Hazardous! Avoid going outside."


app = Dash(__name__)
server = app.server


app.layout = html.Div([

    html.H1("Air Quality Dashboard",
            style={"textAlign": "center"}),

    # FILTERS
    html.Div([
        dcc.Dropdown(
            id="city",
            options=[{"label":i.title(), "value":i} for i in df["site"].unique()],
            value=df["site"].unique()[0]
        ),

        dcc.Dropdown(
            id="pollutant",
            options=[{"label":i.upper(), "value":i} for i in pollutants],
            value="pm25"
        )
    ], style={"width":"40%", "margin":"auto"}),

    html.Br(),

    # ALERT CARD
    html.Div(id="recommendation_card"),

    html.Br(),

    # TOP 5 GRAPH
    dcc.Graph(id="top_polluted"),

    # MAP
    dcc.Graph(id="hotspot_map")

])


@app.callback(
    Output("recommendation_card", "children"),
    Output("top_polluted", "figure"),
    Output("hotspot_map", "figure"),
    Input("city", "value"),
    Input("pollutant", "value")
)
def update_dashboard(city, pollutant):

    # FILTER DATA (SAFE)
    filtered = df[df["site"] == city]
    filtered = filtered.dropna(subset=[pollutant])

    print("Filtered rows:", len(filtered))

    if filtered.empty:
        return html.Div("⚠️ No data available"), {}, {}

    # LATEST VALUE
    latest = filtered.sort_values("date").iloc[-1][pollutant]

    # AQI
    aqi = calculate_aqi(latest)

    # RECOMMENDATION
    rec = get_recommendation(aqi)

    # ALERT CARD
    card = html.Div([
        html.H3(f"AQI: {aqi}"),
        html.H4(f"{city.title()} - {pollutant.upper()}"),
        html.P(rec)
    ], style={
        "padding":"20px",
        "borderRadius":"10px",
        "textAlign":"center",
        "backgroundColor":"#ffcccc" if aqi > 150 else "#ccffcc"
    })

    # TOP 5 POLLUTED LOCATIONS
    top = df.groupby("site")[pollutant].mean().reset_index()
    top = top.sort_values(by=pollutant, ascending=False).head(5)

    top_fig = px.bar(
        top,
        x="site",
        y=pollutant,
        color=pollutant,
        color_continuous_scale="Reds",
        title="Top 5 Polluted Locations"
    )

    # MAP DATA
    map_data = df.groupby("site").mean(numeric_only=True).reset_index()

    map_fig = px.scatter_mapbox(
        map_data,
        lat="latitude",
        lon="longitude",
        size=pollutant,
        color=pollutant,
        hover_name="site",
        zoom=4,
        height=500
    )

    map_fig.update_layout(mapbox_style="open-street-map")

    return card, top_fig, map_fig



if __name__ == "__main__":
    app.run(debug=True)