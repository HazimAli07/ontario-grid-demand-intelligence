from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
GOLD = ROOT / "data" / "gold"

st.set_page_config(
    page_title="Ontario Grid Demand Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root { --ink:#0c1b2a; --muted:#5b6b79; --accent:#d8ff4f; --teal:#33d6c4; }
      .stApp { background: #f5f7f2; color: var(--ink); }
      [data-testid="stSidebar"] { background: #0c1b2a; }
      [data-testid="stSidebar"] * { color: #eef7f3; }
      .hero {
        padding: 2.2rem 2.4rem; border-radius: 24px; color: white;
        background: radial-gradient(circle at 85% 15%, rgba(51,214,196,.34), transparent 30%),
                    linear-gradient(125deg, #0c1b2a 0%, #14394a 58%, #17665f 100%);
        box-shadow: 0 18px 55px rgba(12,27,42,.17); margin-bottom: 1.2rem;
      }
      .eyebrow { color: var(--accent); font-weight: 800; letter-spacing: .12em; font-size:.78rem; }
      .hero h1 { font-size: 2.65rem; margin: .4rem 0 .55rem; line-height: 1.05; }
      .hero p { color:#d8e8e5; font-size:1.04rem; max-width: 760px; margin:0; }
      .status-pill { display:inline-block; margin-top:1rem; padding:.38rem .72rem; border-radius:999px;
        background:rgba(216,255,79,.13); border:1px solid rgba(216,255,79,.55); color:#efffb6; font-size:.82rem; }
      [data-testid="stMetric"] { background:#ffffff; border:1px solid #e2e8df; padding:1rem 1.05rem;
        border-radius:16px; box-shadow:0 7px 24px rgba(12,27,42,.06); }
      [data-testid="stMetricLabel"] { color:#66766f; }
      .section-note { color:#65746e; margin-top:-.35rem; }
      .callout { background:#e9f7f2; border-left:5px solid #1c9f8f; border-radius:10px;
        padding:.85rem 1rem; color:#173d39; margin:.5rem 0 1rem; }
      .footer-note { color:#6b7872; font-size:.82rem; border-top:1px solid #dce4dc; padding-top:1rem; }
      div[data-testid="stTabs"] button { font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_outputs() -> dict[str, object]:
    required = {
        "daily": GOLD / "daily_demand.csv",
        "monthly": GOLD / "monthly_demand.csv",
        "profile": GOLD / "hourly_profile.csv",
        "peaks": GOLD / "top_peak_hours.csv",
        "evaluation": GOLD / "forecast_evaluation.csv",
        "future": GOLD / "next_24h_forecast.csv",
        "importance": GOLD / "feature_importance.csv",
        "metrics": GOLD / "model_metrics.json",
        "quality": GOLD / "data_quality_report.json",
    }
    missing = [path for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Pipeline outputs are missing. Run `PYTHONPATH=src python run_pipeline.py`."
        )
    outputs: dict[str, object] = {}
    for key, path in required.items():
        if path.suffix == ".json":
            outputs[key] = json.loads(path.read_text(encoding="utf-8"))
        else:
            outputs[key] = pd.read_csv(path)
    for key in ("evaluation", "future", "peaks"):
        outputs[key]["timestamp"] = pd.to_datetime(outputs[key]["timestamp"])
    outputs["daily"]["date"] = pd.to_datetime(outputs["daily"]["date"])
    return outputs


def base_layout(figure: go.Figure, height: int = 420) -> go.Figure:
    figure.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=78, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter, Arial, sans-serif", color="#173042"),
        title=dict(y=0.98, x=0.01, xanchor="left"),
        legend=dict(orientation="h", y=1.05, x=0.52, xanchor="left"),
        hovermode="x unified",
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(gridcolor="#e8eeea", zeroline=False)
    return figure


try:
    data = load_outputs()
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

metrics = data["metrics"]
quality = data["quality"]
daily = data["daily"]
evaluation = data["evaluation"]
future = data["future"]

with st.sidebar:
    st.markdown("## ⚡ Grid intelligence")
    st.caption("Portfolio analytics workspace")
    eval_window = st.select_slider(
        "Forecast evaluation window",
        options=[7, 14, 30, 60],
        value=14,
        format_func=lambda days: f"Last {days} days",
    )
    st.markdown("---")
    st.markdown("**Data source**")
    st.caption("IESO Hourly Demand Reports")
    st.markdown("**Coverage**")
    st.caption(
        f"{pd.Timestamp(quality['start_timestamp']):%b %Y} — "
        f"{pd.Timestamp(quality['end_timestamp']):%b %d, %Y}"
    )
    st.markdown("**Forecast design**")
    st.caption("24-hour horizon • chronological holdout • history-only lag features")

st.markdown(
    f"""
    <section class="hero">
      <div class="eyebrow">ONTARIO ENERGY ANALYTICS</div>
      <h1>Grid demand, made decision-ready.</h1>
      <p>An end-to-end lakehouse and machine-learning project that turns official hourly electricity data into quality-controlled metrics, peak-demand intelligence and a 24-hour demand forecast.</p>
      <div class="status-pill">DATA CURRENT THROUGH {pd.Timestamp(quality['end_timestamp']):%B %d, %Y}</div>
    </section>
    """,
    unsafe_allow_html=True,
)

model_metrics = metrics["model"]
next_peak = future.loc[future["forecast_demand_mw"].idxmax()]
recent_load_factor = daily.tail(30)["load_factor"].mean()
metric_columns = st.columns(4)
metric_columns[0].metric("Test MAPE", f"{model_metrics['mape_percent']:.2f}%")
metric_columns[1].metric(
    "MAE vs baseline",
    f"{metrics['mae_improvement_percent']:.1f}% better",
)
metric_columns[2].metric("Next-day peak", f"{next_peak['forecast_demand_mw']:,.0f} MW")
metric_columns[3].metric("30-day load factor", f"{recent_load_factor:.1%}")

overview_tab, forecast_tab, operations_tab, methodology_tab = st.tabs(
    ["Demand pulse", "Forecast lab", "Operational patterns", "Methodology"]
)

with overview_tab:
    st.subheader("Ontario demand pulse")
    st.markdown(
        '<p class="section-note">Daily demand exposes seasonal load shifts and the spread between average and peak system requirements.</p>',
        unsafe_allow_html=True,
    )
    display_daily = daily.tail(365)
    demand_fig = go.Figure()
    demand_fig.add_trace(
        go.Scatter(
            x=display_daily["date"], y=display_daily["peak_demand_mw"],
            name="Daily peak", line=dict(color="#0c1b2a", width=2.1)
        )
    )
    demand_fig.add_trace(
        go.Scatter(
            x=display_daily["date"], y=display_daily["average_demand_mw"],
            name="Daily average", line=dict(color="#1bb8a6", width=2),
            fill="tonexty", fillcolor="rgba(51,214,196,.12)"
        )
    )
    demand_fig.update_layout(title="Latest 365 days: average and peak demand")
    demand_fig.update_yaxes(title="Demand (MW)")
    st.plotly_chart(base_layout(demand_fig), width="stretch")

    left, right = st.columns([1.15, 1])
    with left:
        month_fig = px.bar(
            data["monthly"].tail(18), x="month", y="total_energy_gwh",
            color="average_demand_mw", color_continuous_scale=["#d7f4eb", "#16796f", "#0c1b2a"],
            title="Monthly energy served"
        )
        month_fig.update_yaxes(title="Energy (GWh)")
        month_fig.update_xaxes(title="")
        month_fig.update_layout(coloraxis_colorbar_title="Avg MW")
        st.plotly_chart(base_layout(month_fig, 380), width="stretch")
    with right:
        peaks = data["peaks"].head(10).copy()
        peaks["When"] = peaks["timestamp"].dt.strftime("%b %d, %Y %H:%M")
        peaks["Ontario demand"] = peaks["ontario_demand_mw"].map(lambda value: f"{value:,.0f} MW")
        st.markdown("#### Highest observed demand hours")
        st.dataframe(
            peaks[["When", "Ontario demand"]], hide_index=True, width="stretch",
            height=335
        )

with forecast_tab:
    st.subheader("24-hour demand outlook")
    st.markdown(
        '<div class="callout">Forecasts use only calendar signals and demand history available at least 24 hours earlier. The shaded band is an empirical 90% interval calibrated on a separate validation period.</div>',
        unsafe_allow_html=True,
    )
    forecast_fig = go.Figure()
    forecast_fig.add_trace(
        go.Scatter(
            x=pd.concat([future["timestamp"], future["timestamp"].iloc[::-1]]),
            y=pd.concat([future["upper_90_mw"], future["lower_90_mw"].iloc[::-1]]),
            fill="toself", fillcolor="rgba(51,214,196,.18)", line=dict(color="rgba(0,0,0,0)"),
            hoverinfo="skip", name="90% interval"
        )
    )
    forecast_fig.add_trace(
        go.Scatter(
            x=future["timestamp"], y=future["forecast_demand_mw"], name="Forecast",
            line=dict(color="#0c1b2a", width=3), mode="lines+markers"
        )
    )
    forecast_fig.update_layout(title="Next available 24-hour forecast")
    forecast_fig.update_yaxes(title="Demand (MW)")
    st.plotly_chart(base_layout(forecast_fig), width="stretch")

    cutoff = evaluation["timestamp"].max().to_pydatetime() - timedelta(days=int(eval_window))
    recent_eval = evaluation[evaluation["timestamp"] >= cutoff]
    eval_fig = go.Figure()
    eval_fig.add_trace(
        go.Scatter(x=recent_eval["timestamp"], y=recent_eval["ontario_demand_mw"],
                   name="Actual", line=dict(color="#0c1b2a", width=2.1))
    )
    eval_fig.add_trace(
        go.Scatter(x=recent_eval["timestamp"], y=recent_eval["predicted_demand_mw"],
                   name="Model", line=dict(color="#1bb8a6", width=2))
    )
    eval_fig.update_layout(title=f"Chronological holdout: last {eval_window} days")
    eval_fig.update_yaxes(title="Demand (MW)")
    st.plotly_chart(base_layout(eval_fig), width="stretch")

with operations_tab:
    st.subheader("When demand pressure builds")
    profile = data["profile"]
    profile_fig = px.line(
        profile, x="hour_of_day", y="average_demand_mw", color="day_type",
        color_discrete_map={"Weekday": "#0c1b2a", "Weekend": "#1bb8a6"},
        markers=True, title="Average hourly load profile"
    )
    profile_fig.update_xaxes(title="Hour of day", dtick=2)
    profile_fig.update_yaxes(title="Average demand (MW)")
    st.plotly_chart(base_layout(profile_fig), width="stretch")

    importance = data["importance"].sort_values("importance_mae").tail(10)
    imp_fig = px.bar(
        importance, x="importance_mae", y="feature", orientation="h",
        color="importance_mae", color_continuous_scale=["#d7f4eb", "#1bb8a6", "#0c1b2a"],
        title="Which signals most affect forecast error?"
    )
    imp_fig.update_xaxes(title="Increase in MAE when feature is shuffled")
    imp_fig.update_yaxes(title="")
    imp_fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(base_layout(imp_fig), width="stretch")

with methodology_tab:
    st.subheader("Evidence before polish")
    method_left, method_right = st.columns(2)
    with method_left:
        st.markdown("#### Validation design")
        st.markdown(
            """
            - Chronological train, validation and test periods
            - 24-hour, 48-hour and 7-day lag features
            - Rolling statistics shifted by 24 hours to prevent leakage
            - Seasonal-naive benchmark using the same hour one week earlier
            - Prediction interval calibrated only on validation residuals
            """
        )
    with method_right:
        st.markdown("#### Data quality checks")
        quality_table = pd.DataFrame(
            {
                "Check": ["Rows", "Duplicate timestamps", "Missing demand", "Missing hours"],
                "Result": [
                    f"{quality['row_count']:,}",
                    str(quality["duplicate_timestamps"]),
                    str(quality["missing_ontario_demand"]),
                    str(quality["missing_timestamps"]),
                ],
            }
        )
        st.dataframe(quality_table, hide_index=True, width="stretch")

st.markdown(
    """
    <p class="footer-note">Source: Independent Electricity System Operator (IESO) Hourly Demand Reports. This portfolio project is independent and is not affiliated with or endorsed by the IESO. Forecasts are educational and should not be used for grid operations.</p>
    """,
    unsafe_allow_html=True,
)
