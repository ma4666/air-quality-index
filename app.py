from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import gdown

# -------------------------------
# LOAD DATA FROM GOOGLE DRIVE
# -------------------------------
df = pd.read_csv(
    "https://docs.google.com/spreadsheets/d/1D7N-VkG3cjUF2jMzbFyA7b-vPwdvmHih8Ct_RB3_p8E/export?format=csv"
)

df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.month

pollutants = ["pm25","no2","o3","so2","pm10"]

# -------------------------------
# AQI CALCULATION (PM2.5 BASED)
# -------------------------------
def calculate_aqi(pm25):
    if pm25 <= 12: return 50
    elif pm25 <= 35.4: return 100
    elif pm25 <= 55.4: return 150
    elif pm25 <= 150.4: return 200
    elif pm25 <= 250.4: return 300
    else: return 400

# -------------------------------
# RECOMMENDATION RULES
# -------------------------------
def get_recommendation(aqi):
    if aqi <= 50:
        return "Air quality is good. Enjoy outdoor activities."
    elif aqi <= 100:
        return "Moderate air quality. Sensitive individuals should limit outdoor exertion."
    elif aqi <= 150:
        return "Unhealthy for sensitive groups. Reduce prolonged outdoor activity."
    elif aqi <= 200:
        return "Unhealthy. Wear a mask and avoid outdoor exercise."
    elif aqi <= 300:
        return "Very unhealthy. Stay indoors and use air purifiers."
    else:
        return "Hazardous! Avoid going outside. Take protective measures."

# -------------------------------
# DASH APP
# -------------------------------
app = Dash(__name__)
server = app.server

# -------------------------------
# LAYOUT
# -------------------------------
app.layout = html.Div([

    html.H1("Air Quality Dashboard with Recommendations",
            style={"textAlign":"center"}),

    # Filters
    html.Div([
        dcc.Dropdown(
            id="city",
            options=[{"label":i,"value":i} for i in df["site"].unique()],
            value=df["site"].unique()[0],
            placeholder="Select City"
        ),

        dcc.Dropdown(
            id="pollutant",
            options=[{"label":i.upper(),"value":i} for i in pollutants],
            value="pm25",
            placeholder="Select Pollutant"
        )
    ], style={"width":"40%","margin":"auto"}),

    html.Br(),

    # Recommendation Card
    html.Div(id="recommendation_card"),

    html.Br(),

    # Top polluted locations
    dcc.Graph(id="top_polluted"),

    # Hotspot map
    dcc.Graph(id="hotspot_map")

])

# -------------------------------
# CALLBACK
# -------------------------------
@app.callback(
    Output("recommendation_card","children"),
    Output("top_polluted","figure"),
    Output("hotspot_map","figure"),
    Input("city","value"),
    Input("pollutant","value")
)

def update_dashboard(city, pollutant):

    # Filter data
    filtered = df[df["site"] == city].dropna(subset=[pollutant])

    if filtered.empty:
        return "No data available", {}, {}

    # Latest pollutant value
    latest = filtered.sort_values("date").iloc[-1][pollutant]

    # AQI calculation (using PM2.5 logic)
    aqi = calculate_aqi(latest)

    recommendation = get_recommendation(aqi)

    # -------------------------------
    # ALERT CARD
    # -------------------------------
    card = html.Div([
        html.H3(f"AQI: {aqi}"),
        html.H4(f"{city} - {pollutant.upper()}"),
        html.P(recommendation)
    ], style={
        "border":"1px solid #ccc",
        "padding":"20px",
        "borderRadius":"10px",
        "textAlign":"center",
        "backgroundColor":"#ffcccc" if aqi > 150 else "#ccffcc"
    })

    # -------------------------------
    # TOP 5 POLLUTED LOCATIONS
    # -------------------------------
    top_sites = df.groupby("site")[pollutant].mean().reset_index()
    top_sites = top_sites.sort_values(by=pollutant, ascending=False).head(5)

    top_fig = px.bar(
        top_sites,
        x="site",
        y=pollutant,
        title="Top 5 Polluted Locations",
        color=pollutant,
        color_continuous_scale="Reds"
    )

    # -------------------------------
    # HOTSPOT MAP
    # -------------------------------
    map_data = df.groupby("site").mean(numeric_only=True).reset_index()

    map_fig = px.scatter_mapbox(
        map_data,
        lat="latitude",
        lon="longitude",
        size=pollutant,
        color=pollutant,
        hover_name="site",
        color_continuous_scale="Reds",
        zoom=4,
        height=500
    )

    map_fig.update_layout(mapbox_style="open-street-map")

    return card, top_fig, map_fig


# -------------------------------
# RUN SERVER
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)