from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DATA_PATH

# -------------------------------
# LOAD DATA
# -------------------------------
df = pd.read_csv("https://docs.google.com/spreadsheets/d/1D7N-VkG3cjUF2jMzbFyA7b-vPwdvmHih8Ct_RB3_p8E/export?format=csv")
df.columns = df.columns.str.strip().str.lower()
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date", "site"])

df["month"] = df["date"].dt.month
df["year"] = df["date"].dt.year

# Season mapping (User Story 3)
def get_season(month):
    if month in [12,1,2]:
        return "Winter"
    elif month in [3,4,5]:
        return "Spring"
    elif month in [6,7,8]:
        return "Summer"
    else:
        return "Autumn"

df["season"] = df["month"].apply(get_season)

pollutants = ["co", "nox", "no2", "o3", "so2", "pm10", "pm2.5"]

# -------------------------------
# AQI + RECOMMENDATION #sprint 4
# -------------------------------
def calculate_aqi(pm25):
    if pm25 <= 12: return 50
    elif pm25 <= 35.4: return 100
    elif pm25 <= 55.4: return 150
    elif pm25 <= 150.4: return 200
    elif pm25 <= 250.4: return 300
    else: return 400

def get_recommendation(aqi):
    if aqi <= 50:
        return "Good air quality. Enjoy outdoor activities."
    elif aqi <= 100:
        return "Moderate air quality. Sensitive people reduce outdoor activity."
    elif aqi <= 150:
        return "Unhealthy for sensitive groups."
    elif aqi <= 200:
        return "Unhealthy. Wear a mask."
    elif aqi <= 300:
        return "Very unhealthy. Stay indoors."
    else:
        return "Hazardous! Avoid going outside."

# KPI values
avg_pm25 = round(df["pm2.5"].mean(), 2)
avg_no2 = round(df["no2"].mean(), 2)
avg_o3 = round(df["o3"].mean(), 2)

# -------------------------------
# DASH APP
# -------------------------------
app = Dash(__name__)
server = app.server

app.layout = html.Div([

    html.H1(
        "UK Air Quality Analytics Dashboard",
        style={"textAlign": "center", "marginBottom": "30px"}
    ),


    # Filters
    html.Div([
        html.Label("Select City"),
        dcc.Dropdown(
            id="city",
            options=[{"label":i,"value":i} for i in df["site"].dropna().unique()],
            value=df["site"].dropna().unique()[0]
        )

    ], style={"width":"30%","margin":"auto"}),

    html.Br(),

    
    html.Button("Download Dataset", id="download-btn"),
    dcc.Download(id="download-data"),

    html.Br(),
    html.Br(),

    html.Label("Select Date Range"),
    dcc.DatePickerRange(
        id="date-range",
        start_date=df["date"].min().date(),
        end_date=df["date"].max().date()
    ),
    html.H1("Air Quality Insights",
            style={"textAlign":"center"}),

    html.Br(),
    html.Br(),

    # KPI Cards
    html.Div([
        html.Div([html.H4("Average PM2.5"), html.H2(avg_pm25)], className="card"),
        html.Div([html.H4("Average NO2"), html.H2(avg_no2)], className="card"),
        html.Div([html.H4("Average O3"), html.H2(avg_o3)], className="card"),
    ], style={"display": "flex", "justifyContent": "space-around"}),

    html.Br(),

    # Filters
    html.Div([
        html.Label("Select Monitoring Site"),
        dcc.Dropdown(
            id="site",
            options=[{"label": i, "value": i} for i in sorted(df["site"].dropna().unique())],
            value=sorted(df["site"].dropna().unique())[0]
        ),

        html.Br(),

        html.Label("Select Pollutant"),
        dcc.Dropdown(
            id="pollutant",
            options=[{"label": i.upper(), "value": i} for i in pollutants],
            value="pm2.5"
        )
    ], style={"width": "30%", "margin": "auto"}),

    html.Br(),

    html.Div(id="stats-box"),
    html.Br(),
    html.Div(id="pollutant-info"),
    html.Br(),
html.Br(),
#sprint 4
# Recommendation Card
html.Div(id="recommendation_card"),

# Top polluted
dcc.Graph(id="top_polluted"),

# Hotspot map
dcc.Graph(id="hotspot_map"),
    # Graphs
    html.Div([
        dcc.Graph(id="trend_graph"),
        dcc.Graph(id="monthly_graph")
    ]),

    html.Div([
        dcc.Graph(id="site_graph"),
        dcc.Graph(id="distribution_graph")
    ]),

    # US21 — Site type comparison
    html.H2("Site Type Comparison", style={"textAlign": "center"}),
    html.Div([
        html.Label("Select Pollutant"),
        dcc.Dropdown(
            id="site-type-pollutant",
            options=[{"label": p.upper(), "value": p} for p in pollutants],
            value="no2",
            clearable=False,
        ),
    ], style={"width": "30%", "margin": "auto"}),
    dcc.Graph(id="site-type-chart"),
    html.Br(),

    dcc.Graph(id="bubble-chart"),
    dcc.Graph(id="correlation_graph"),
    html.Div(id="correlation-explanation", style={
    "padding": "20px",
    "margin": "20px auto",
    "width": "70%",
    "backgroundColor": "#f8f9fa",
    "borderRadius": "8px",
    "fontSize": "15px"
}),
    dcc.Graph(id="map_graph"),

    # -------------------------------
    # USER STORY 18
    # -------------------------------
    html.H2("Advanced Insights"),
    html.Div(id="most_polluted_year"),
    dcc.Graph(id="year_graph"),

    # -------------------------------
    # USER STORY 19
    # -------------------------------
    html.Div(id="most_polluted_month"),
    dcc.Graph(id="month_graph"),

    # -------------------------------
    # USER STORY 20
    # -------------------------------
    html.Div(id="best_season"),
    dcc.Graph(id="season_graph"),

    # -------------------------------
    # USER STORY 21 — Peak Hour
    # -------------------------------
    html.H2("Peak Pollution Hour", style={"textAlign": "center"}),
    
    dcc.Graph(id="hourly_pollution_graph"),
    
    html.Div(id="peak_hour_text", style={"textAlign": "center", "fontSize": 20}),
])


# -------------------------------
# DOWNLOAD CALLBACK
# -------------------------------
@app.callback(
    Output("download-data", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_dataset(n_clicks):
    return dcc.send_data_frame(df.to_csv, "UK_Air_Quality_Cleaned.csv", index=False)

# -------------------------------
# DASHBOARD CALLBACK
# -------------------------------
@app.callback(
    Output("recommendation_card", "children"),
    Output("top_polluted", "figure"),
    Output("hotspot_map", "figure"),
    Output("trend_graph", "figure"),
    Output("monthly_graph", "figure"),
    Output("site_graph", "figure"),
    Output("distribution_graph", "figure"),
    Output("bubble-chart", "figure"),
    Output("correlation_graph", "figure"),
    Output("map_graph", "figure"),
    Output("stats-box", "children"),
    Output("pollutant-info", "children"),
    Output("most_polluted_year", "children"),
    Output("year_graph", "figure"),
    Output("most_polluted_month", "children"),
    Output("month_graph", "figure"),
    Output("best_season", "children"),
    Output("season_graph", "figure"),
    Output("correlation-explanation", "children"),
    Input("pollutant", "value"),
    Input("city", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_dashboard(pollutant, city, start_date, end_date):

    filtered = df[
        (df["site"] == city) &
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ].copy()

    filtered = filtered.dropna(subset=[pollutant])

   if filtered.empty:
      return (None,) * 19

    filtered = filtered.sort_values("date").tail(1000)

    latest_pm25 = filtered["pm2.5"].iloc[-1] if "pm2.5" in filtered.columns else 0

    aqi = calculate_aqi(latest_pm25)
    rec = get_recommendation(aqi)

    card = html.Div([
       html.H3(f"AQI: {aqi}"),
       html.P(rec)
    ])

top_sites = df.groupby("site")[pollutant].mean().reset_index()
top_sites = top_sites.sort_values(by=pollutant, ascending=False).head(5)

top_fig = px.bar(top_sites, x="site", y=pollutant)
map_data = df.groupby("site").first().reset_index()

map_fig = px.scatter_mapbox(
    map_data,
    lat="latitude",
    lon="longitude",
    hover_name="site",
    zoom=4
)

map_fig.update_layout(mapbox_style="open-street-map")

    stats_box = html.Div([
        html.H4(f"{pollutant.upper()} Summary Statistics"),
        html.P(f"Mean: {filtered[pollutant].mean():.2f}"),
        html.P(f"Minimum: {filtered[pollutant].min():.2f}"),
        html.P(f"Maximum: {filtered[pollutant].max():.2f}"),
        html.P(f"Standard Deviation: {filtered[pollutant].std():.2f}")
    ])

    # -------------------------------
    # USER STORY 18: Most Polluted Year
    # -------------------------------
    
    year_avg = df.groupby("year")[pollutant].mean().reset_index()
    worst_year = year_avg.sort_values(by=pollutant, ascending=False).iloc[0]["year"]

    year_fig = px.bar(
        year_avg,
        x="year",
        y=pollutant,
        title="Average Pollution by Year"
    )

    year_text = html.H2(
        f"Most Polluted Year: {int(worst_year)}",
        style={"textAlign":"center","color":"red"}
    )

    # -------------------------------
    # USER STORY 19: Most Polluted Month
    # -------------------------------
    month_avg = df.groupby("month")[pollutant].mean().reset_index()
    worst_month = month_avg.sort_values(by=pollutant, ascending=False).iloc[0]["month"]

    month_fig = px.bar(
        month_avg,
        x="month",
        y=pollutant,
        title="Average Pollution by Month"
    )

    month_text = html.H2(
        f"Most Polluted Month: {int(worst_month)}",
        style={"textAlign":"center","color":"red"}
    )

    # -------------------------------
    # USER STORY 20: Best Season (City Based)
    # -------------------------------
    city_df = df[df["site"] == city]

    season_avg = city_df.groupby("season")[pollutant].mean().reset_index()
    best_season_val = season_avg.sort_values(by=pollutant, ascending=True).iloc[0]["season"]

    season_fig = px.bar(
        season_avg,
        x="season",
        y=pollutant,
        title=f"Seasonal Air Quality in {city}"
    )

    season_text = html.H2(
        f"Best Season to Visit {city}: {best_season_val}",
        style={"textAlign":"center","color":"green"}
    )

    pollutant_descriptions = {
        "no2": "Nitrogen dioxide is mainly produced by road traffic and can irritate the lungs.",
        "pm2.5": "PM2.5 refers to very small particles that can enter deep into the lungs and bloodstream.",
        "co": "Carbon monoxide is a poisonous gas formed by incomplete combustion.",
        "o3": "Ground-level ozone is a harmful air pollutant that can affect breathing.",
        "pm10": "PM10 includes inhalable particles that may affect the respiratory system.",
        "so2": "Sulphur dioxide can irritate the nose, throat, and lungs.",
        "nox": "Nitrogen oxides are gases mainly produced during fuel combustion."
    }

    pollutant_info = html.Div([
        html.H4(f"About {pollutant.upper()}"),
        html.P(pollutant_descriptions.get(pollutant, "No description available."))
    ])

    trend = px.line(
        filtered,
        x="date",
        y=pollutant,
        title=f"{pollutant.upper()} Trend",
        color_discrete_sequence=["#00CC96"]
    )

    monthly = filtered.groupby("month")[pollutant].mean().reset_index()
    monthly_fig = px.bar(
        monthly,
        x="month",
        y=pollutant,
        color=pollutant,
        color_continuous_scale="Reds",
        title="Monthly Average"
    )

    site_avg = df.groupby("site")[pollutant].mean().reset_index().head(20)
    site_avg["highlight"] = site_avg[pollutant].apply(
        lambda x: "Worst Site" if x == site_avg[pollutant].max() else "Other Sites"
    )

    site_fig = px.bar(
        site_avg,
        y="site",
        x=pollutant,
        color="highlight",
        orientation="h",
        title="Average Pollutant by Site"
    )

    dist = px.histogram(
        filtered,
        x=pollutant,
        nbins=40,
        title="Distribution",
        color_discrete_sequence=["#636EFA"]
    )

    bubble_fig = px.scatter(
        filtered,
        x="pm2.5",
        y="no2",
        size="co",
        color="o3",
        hover_name="site",
        title="Pollution Relationship: PM2.5 vs NO2, CO, and O3"
    )

# -------------------------------
# USER STORY 23: Correlation Matrix
# -------------------------------
    

    corr = df[pollutants].dropna().sample(min(5000, len(df.dropna(subset=pollutants)))).corr()
    corr_fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title="Correlation Heatmap"
    )

    strong_pos = []
    strong_neg = []
    pollutant_list = corr.columns.tolist()
    for i in range(len(pollutant_list)):
        for j in range(i+1, len(pollutant_list)):
            val = corr.iloc[i, j]
            pair = f"{pollutant_list[i].upper()} & {pollutant_list[j].upper()} (r={val:.2f})"
            if val >= 0.7:
                strong_pos.append(pair)
            elif val <= -0.7:
                strong_neg.append(pair)

    explanation_children = [html.H4("Correlation Analysis")]
    if strong_pos:
        explanation_children.append(html.P(
            f"Strong positive relationships (r ≥ 0.7): {', '.join(strong_pos)}. "
            "These pollutants tend to rise and fall together, likely sharing common sources."
        ))
    else:
        explanation_children.append(html.P("No strong positive correlations found (r ≥ 0.7)."))

    if strong_neg:
        explanation_children.append(html.P(
            f"Strong negative relationships (r ≤ -0.7): {', '.join(strong_neg)}. "
            "These pollutants tend to move in opposite directions."
        ))
    else:
        explanation_children.append(html.P("No strong negative correlations found (r ≤ -0.7)."))

    explanation_children.append(html.P(
        "Note: Correlation values range from -1 (perfect negative) to +1 (perfect positive). "
        "Values near 0 indicate no linear relationship."
    ))

    corr_explanation = html.Div(explanation_children)

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

    

    return (
        card,
        top_fig,
        map_fig,
        trend,
        monthly_fig,
        site_fig,
        dist,
        bubble_fig,
        corr_fig,
        map_fig,
        stats_box,
        pollutant_info,
        year_text, 
        year_fig, 
        month_text, 
        month_fig, 
        season_text, 
        season_fig,
        corr_explanation
    )

@app.callback(
Output("site-type-chart", "figure"),
Input("site-type-pollutant", "value")
)
def update_site_type_chart(pollutant):
    site_type_avg = (
        df.groupby("site_type")[pollutant]
        .mean()
        .dropna()
        .reset_index()
        .sort_values(by=pollutant, ascending=False)
    )
    site_type_avg.columns = ["site_type", "value"]

    fig = px.bar(
        site_type_avg,
        x="site_type",
        y="value",
        color="site_type",
        title=f"Average {pollutant.upper()} by Site Type",
        labels={"site_type": "Site Type", "value": pollutant.upper()},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    fig.update_layout(
        xaxis_title="Site Type",
        yaxis_title=f"Average {pollutant.upper()}",
        plot_bgcolor="#343a40",
        paper_bgcolor="#343a40",
        font_color="white",
        showlegend=False,
        margin=dict(t=50, b=40, l=60, r=20),
    )
    fig.update_yaxes(showgrid=True, gridcolor="#4a4f54")

    return fig

#-------------------
#USER STORY 25
#-------------------
@app.callback(
    Output("hourly_pollution_graph", "figure"),
    Output("peak_hour_text", "children"),
    Input("pollutant", "value"),
    Input("city", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date")
)
def update_peak_hour(pollutant, city, start_date, end_date):

    filtered = df[
        (df["site"] == city) &
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ].copy()

    if filtered.empty or pollutant not in filtered.columns:
        return {}, "No data available."

    filtered["hour"] = filtered["date"].dt.hour

    hourly_means = filtered.groupby("hour")[pollutant].mean()

    peak_hour = hourly_means.idxmax()

    colors = ["red" if h == peak_hour else "blue" for h in hourly_means.index]

    fig = px.bar(
        x=hourly_means.index,
        y=hourly_means.values,
        labels={"x": "Hour of Day", "y": f"Average {pollutant.upper()}"},
        title=f"Average {pollutant.upper()} by Hour"
    )

    fig.update_traces(marker_color=colors)

    fig.update_layout(xaxis=dict(dtick=1))

    text = f"Most Polluted Hour: {peak_hour}:00"

    return fig, text

if __name__ == "__main__":
    app.run(debug=True)

# -------------------------------
# ✅ ENHANCED AI ASSISTANT
# -------------------------------
def air_quality_assistant(query):
    q = query.lower()

    if "polluted year" in q:
        year_data = df.groupby("year")["pm25"].mean()
        year = year_data.idxmax()
        value = round(year_data.max(), 2)

        return f"The most polluted year is {year} with an average PM2.5 of {value}. This indicates higher pollution levels. You can verify this in the yearly chart above."

    elif "polluted month" in q:
        month_data = df.groupby("month")["pm25"].mean()
        month = month_data.idxmax()
        value = round(month_data.max(), 2)

        return f"The most polluted month is {month} with PM2.5 around {value}. This may be due to weather conditions like low wind. Check the monthly graph."

    elif any(word in q for word in ["best season", "air quality best", "when is air quality best", "clean air", "lowest pollution"]):
        season_data = df.groupby("season")["pm25"].mean()
        season = season_data.idxmin()
        value = round(season_data.min(), 2)

        return f"The best season is {season} with lowest pollution (PM2.5 ≈ {value}). You can confirm this in the seasonal chart."

    elif "polluted city" in q:
        city_data = df.groupby("site")["pm25"].mean()
        city = city_data.idxmax()
        value = round(city_data.max(), 2)

        return f"The most polluted city is {city} with PM2.5 around {value}. This indicates poor air quality compared to others."

    elif "trend" in q:
        return "Pollution trends show how air quality changes over time. See the trend chart for patterns."

    else:
        return "Ask about polluted year, month, city, best season, or trend."


    # -------------------------------
    # USER STORY 1
    # -------------------------------
    html.Div(id="most_polluted_year"),
    dcc.Graph(id="year_graph"),

    # -------------------------------
    # USER STORY 2
    # -------------------------------
    html.Div(id="most_polluted_month"),
    dcc.Graph(id="month_graph"),

    # -------------------------------
    # USER STORY 3
    # -------------------------------
    html.Div(id="best_season"),
    dcc.Graph(id="season_graph"),

    html.Br(),

    # -------------------------------
    # AI ASSISTANT UI
    # -------------------------------
    html.H3("Ask AI Assistant"),
    dcc.Input(id="user_input", type="text", placeholder="Ask something..."),
    html.Button("Ask", id="ask_btn"),
    html.Div(id="ai_output", style={"marginTop":"20px","fontWeight":"bold"})

])
# -------------------------------
# MAIN CALLBACK
# -------------------------------
@app.callback(
    Output("most_polluted_year","children"),
    Output("year_graph","figure"),
    Output("most_polluted_month","children"),
    Output("month_graph","figure"),
    Output("best_season","children"),
    Output("season_graph","figure"),
    Input("pollutant","value"),
    Input("city","value")
)
def update_dashboard(pollutant, city):

    # USER STORY 1
    year_avg = df.groupby("year")[pollutant].mean().reset_index()
    worst_year = year_avg.sort_values(by=pollutant, ascending=False).iloc[0]["year"]

    year_fig = px.bar(year_avg, x="year", y=pollutant,
                      title="Average Pollution by Year")

    year_text = html.H2(
        f"Most Polluted Year: {int(worst_year)}",
        style={"textAlign":"center","color":"red"}
    )

    # USER STORY 2
    month_avg = df.groupby("month")[pollutant].mean().reset_index()
    worst_month = month_avg.sort_values(by=pollutant, ascending=False).iloc[0]["month"]

    month_fig = px.bar(month_avg, x="month", y=pollutant,
                       title="Average Pollution by Month")

    month_text = html.H2(
        f"Most Polluted Month: {int(worst_month)}",
        style={"textAlign":"center","color":"red"}
    )

    # USER STORY 3
    city_df = df[df["site"] == city]

    season_avg = city_df.groupby("season")[pollutant].mean().reset_index()
    best_season_val = season_avg.sort_values(by=pollutant, ascending=True).iloc[0]["season"]

    season_fig = px.bar(season_avg, x="season", y=pollutant,
                        title=f"Seasonal Air Quality in {city}")

    season_text = html.H2(
        f"Best Season to Visit {city}: {best_season_val}",
        style={"textAlign":"center","color":"green"}
    )

    return year_text, year_fig, month_text, month_fig, season_text, season_fig


# -------------------------------
# AI CALLBACK
# -------------------------------
@app.callback(
    Output("ai_output","children"),
    Input("ask_btn","n_clicks"),
    Input("user_input","value")
)
def chat(n_clicks, query):
    if n_clicks and query:
        return air_quality_assistant(query)
    return ""

# -------------------------------
# RUN
# -------------------------------
app.run(jupyter_mode="inline")