from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_PATH = (
    ROOT
    / "data"
    / "processed"
    / "analysis"
    / "stop_updates_with_quality_flags.csv"
)

st.set_page_config(
    page_title="TransitCast | Edmonton Bus Delays",
    page_icon="🚌",
    layout="wide",
)

# Friendly, lightweight styling.
st.markdown(
    """
    <style>
    .block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem;}
    .hero {
        padding: 1.5rem 1.7rem; border-radius: 18px;
        background: linear-gradient(120deg, #123b52 0%, #176b72 100%);
        color: white; margin-bottom: 1rem;
    }
    .hero h1 {margin: 0; font-size: 2.35rem;}
    .hero p {margin: .45rem 0 0 0; color: #e4f4f3; font-size: 1.05rem;}
    .notice {
        padding: .85rem 1rem; border-radius: 12px;
        background: #fff4d6; color: #664b00;
        border: 1px solid #f0d58a; margin: .8rem 0 1.1rem 0;
    }
    .small-note {color: #687782; font-size: .88rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=5)
def load_data(path: str, modified_time: float) -> pd.DataFrame:
    data = pd.read_csv(path, low_memory=False)

    for column in ("departure_delay_seconds", "arrival_delay_seconds", "stop_sequence"):
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    for column in ("feed_timestamp_utc", "departure_prediction_utc"):
        if column in data.columns:
            data[column] = pd.to_datetime(data[column], utc=True, errors="coerce")

    for column in ("route_id", "stop_id", "snapshot_file"):
        if column in data.columns:
            data[column] = data[column].astype("string").str.strip()

    return data


def minutes_text(seconds):
    if pd.isna(seconds):
        return "Not available"
    minutes = round(float(seconds) / 60)
    if minutes <= 0:
        return "On time or early"
    if minutes == 1:
        return "About 1 minute"
    return f"About {minutes} minutes"


def delay_status(seconds):
    if pd.isna(seconds):
        return "No estimate"
    if seconds <= 300:
        return "On time or nearly on time"
    if seconds <= 900:
        return "Running late"
    return "Significantly delayed"


if not DATA_PATH.exists():
    st.error(
        "I couldn't find the processed transit data. Make sure this app is in "
        "your project folder and the data file exists at "
        "`data/processed/analysis/stop_updates_with_quality_flags.csv`."
    )
    st.stop()

df = load_data(
    str(DATA_PATH),
    DATA_PATH.stat().st_mtime,
)

st.markdown(
    """
    <div class="hero">
      <h1>🚌 TransitCast</h1>
      <p>Edmonton bus delay information, in plain English.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write(
    "Choose a route to explore the delay estimates reported in the transit feed. "
    "This is a research prototype, not a live arrival tracker."
)

required = {"snapshot_file", "route_id", "departure_delay_seconds"}
if not required.issubset(df.columns):
    st.error("The dataset is missing columns this dashboard needs.")
    st.stop()

labeled = df.dropna(subset=["snapshot_file", "route_id", "departure_delay_seconds"]).copy()
labeled = labeled[labeled["route_id"].astype(str).str.len() > 0]
if labeled.empty:
    st.warning("There are no departure-delay estimates available in this dataset yet.")
    st.stop()

# Only show snapshots that actually have a departure-delay estimate.
snapshot_info = (
    labeled.groupby("snapshot_file", dropna=False)
    .agg(
        feed_time=("feed_timestamp_utc", "max"),
        records=("departure_delay_seconds", "size"),
    )
    .reset_index()
    .sort_values("feed_time")
)

snapshot_names = snapshot_info["snapshot_file"].astype(str).tolist()
latest_snapshot = snapshot_names[-1]
selected_snapshot = st.selectbox(
    "Which data sample do you want to view?",
    options=snapshot_names,
    index=len(snapshot_names) - 1,
    format_func=lambda name: (
        f"Latest sample — {name}" if name == latest_snapshot else name
    ),
)

selected_info = snapshot_info[snapshot_info["snapshot_file"].astype(str) == selected_snapshot]
selected_time = selected_info["feed_time"].iloc[0] if not selected_info.empty else pd.NaT

if pd.notna(selected_time):
    now_utc = pd.Timestamp.now(tz="UTC")
    age_hours = max(0, (now_utc - selected_time).total_seconds() / 3600)
    local_time = selected_time.tz_convert("America/Edmonton")
    time_label = local_time.strftime("%b %d, %Y at %I:%M %p MT").replace(" 0", " ")
    if age_hours < 1:
        age_label = "less than an hour ago"
    elif age_hours < 48:
        age_label = f"about {round(age_hours)} hours ago"
    else:
        age_label = f"about {round(age_hours / 24)} days ago"

    if age_hours > 2:
        st.markdown(
            f'<div class="notice"><strong>These estimates are old.</strong> '
            f'This sample was recorded {age_label} ({time_label}). '
            f'Don’t use it to decide whether a bus is late right now.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info(f"Sample recorded {age_label} — {time_label}. This is still a feed estimate, not a verified arrival.")

sample = labeled[labeled["snapshot_file"].astype(str) == selected_snapshot].copy()
sample["delay_minutes"] = sample["departure_delay_seconds"] / 60
sample["late_over_5"] = sample["departure_delay_seconds"] > 300

route_ids = sorted(sample["route_id"].dropna().astype(str).unique(), key=str)
route_options = ["All routes"] + route_ids
chosen_route = st.selectbox("Find your bus route", route_options)

view = sample.copy()
if chosen_route != "All routes":
    view = view[view["route_id"].astype(str) == chosen_route]

if view.empty:
    st.warning("There are no delay estimates for that selection in this sample.")
    st.stop()

# Keep the headline values human-readable.
median_seconds = view["departure_delay_seconds"].median()
late_percent = view["late_over_5"].mean() * 100
num_routes = view["route_id"].nunique()
num_estimates = len(view)

c1, c2, c3 = st.columns(3)
c1.metric("Delay estimates available", f"{num_estimates:,}")
c2.metric("Typical reported delay", minutes_text(median_seconds))
c3.metric("Estimates over 5 minutes late", f"{late_percent:.0f}%")

st.caption(
    "These figures describe the selected sample only. Missing estimates are not counted as on-time."
)

st.divider()

if chosen_route == "All routes":
    st.subheader("Routes to look at")
    st.write("These routes had the highest typical reported delays in this sample.")
    route_summary = (
        view.groupby("route_id")
        .agg(
            estimates=("departure_delay_seconds", "size"),
            typical_delay=("departure_delay_seconds", "median"),
            over_five=("late_over_5", "mean"),
        )
        .reset_index()
    )
    route_summary = route_summary[route_summary["estimates"] >= 10].copy()
    if route_summary.empty:
        st.info("There aren't enough estimates in this sample to compare routes reliably.")
    else:
        route_summary["over_five"] = route_summary["over_five"] * 100
        route_summary["typical_delay_minutes"] = route_summary["typical_delay"] / 60
        route_summary = route_summary.sort_values("typical_delay_minutes", ascending=False).head(10)
        chart = px.bar(
            route_summary.sort_values("typical_delay_minutes"),
            x="typical_delay_minutes",
            y=route_summary.sort_values("typical_delay_minutes")["route_id"].astype(str),
            orientation="h",
            labels={
                "typical_delay_minutes": "Typical reported delay (minutes)",
                "y": "Bus route",
            },
            hover_data={
                "estimates": True,
                "over_five": ":.0f",
                "typical_delay_minutes": ":.1f",
            },
        )
        chart.update_layout(
            showlegend=False,
            yaxis_title="Bus route",
            xaxis_title="Typical reported delay (minutes)",
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(chart, use_container_width=True)
        st.dataframe(
            route_summary[["route_id", "estimates", "typical_delay_minutes", "over_five"]]
            .rename(
                columns={
                    "route_id": "Route",
                    "estimates": "Number of estimates",
                    "typical_delay_minutes": "Typical delay (minutes)",
                    "over_five": "Estimates over 5 minutes late (%)",
                }
            )
            .round(1),
            use_container_width=True,
            hide_index=True,
        )
else:
    route_delays = view["departure_delay_seconds"].dropna()
    route_median = route_delays.median()
    status = delay_status(route_median)
    st.subheader(f"Route {chosen_route}")
    if status == "On time or nearly on time":
        st.success(f"Typical reported status: **{status}**")
    elif status == "Running late":
        st.warning(f"Typical reported status: **{status}**")
    elif status == "Significantly delayed":
        st.error(f"Typical reported status: **{status}**")
    else:
        st.info("No delay estimate is available for this route in the selected sample.")

    st.write(
        f"The typical reported delay is **{minutes_text(route_median)}**. "
        f"{late_percent:.0f}% of the available estimates for this route were over five minutes late."
    )

    chart_data = view.copy()
    chart_data["delay_group"] = pd.cut(
        chart_data["departure_delay_seconds"],
        bins=[float("-inf"), 0, 300, 900, float("inf")],
        labels=["Early / on time", "Up to 5 min late", "5–15 min late", "Over 15 min late"],
        right=True,
    )
    counts = (
        chart_data["delay_group"]
        .value_counts(sort=False)
        .reindex(["Early / on time", "Up to 5 min late", "5–15 min late", "Over 15 min late"], fill_value=0)
        .rename_axis("Reported status")
        .reset_index(name="Number of estimates")
    )
    chart = px.bar(
        counts,
        x="Reported status",
        y="Number of estimates",
        labels={"Reported status": "Reported delay category"},
    )
    chart.update_layout(showlegend=False, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(chart, use_container_width=True)

st.subheader("What these words mean")
a, b, c = st.columns(3)
a.markdown("**On time or nearly on time**  \nUp to 5 minutes late")
b.markdown("**Running late**  \nMore than 5 and up to 15 minutes late")
c.markdown("**Significantly delayed**  \nMore than 15 minutes late")

with st.expander("About this data"):
    st.write(
        "TransitCast currently uses saved snapshots from a transit data feed. "
        "The feed reports estimates; it does not confirm when a bus actually arrived. "
        "This page shows one saved sample at a time, so it may not describe current service."
    )
    st.write(
        "A blank estimate means there is no reported delay value for that record. "
        "It does not mean the bus was on time."
    )

st.download_button(
    "Download this view",
    data=view.to_csv(index=False).encode("utf-8"),
    file_name="transitcast_route_estimates.csv",
    mime="text/csv",
)

st.caption("TransitCast · Edmonton transit data prototype")
