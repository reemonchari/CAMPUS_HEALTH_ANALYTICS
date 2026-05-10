"""
University Clinic – Patient Volume Prediction System
=====================================================
A clean, professional tool for clinic supervisors.
  - Calendar + Live Weather Mode: upload academic calendar, fetch real weather, bulk predict
  - Manual Entry Mode: categorical dropdowns (no raw numbers) for quick single-day estimates
"""

import streamlit as st
import pickle
import numpy as np
import pandas as pd
import requests
from datetime import date

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Clinic Patient Prediction",
    layout="wide",
)

# ─── Minimal, professional styling ────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}

    /* Clean font */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    }

    /* Page background */
    .stApp { background-color: navy blue; }

    /* Top header bar */
    .app-header {
        background: #1a2e4a;
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    .app-header h1 { margin: 0; font-size: 1.4rem; font-weight: 600; }
    .app-header p  { margin: 0.2rem 0 0; font-size: 0.85rem; opacity: 0.75; }

    /* Section cards */
    .section-card {
        background: white;
        border: 1px solid #e2e6ea;
        border-radius: 8px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.2rem;
    }
    .section-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6c757d;
        margin-bottom: 0.8rem;
    }

    /* Result box */
    .result-box {
        background: #eaf4ff;
        border-left: 4px solid #1a2e4a;
        border-radius: 4px;
        padding: 1rem 1.4rem;
        margin-top: 1rem;
    }
    .result-number { font-size: 2.2rem; font-weight: 700; color: #1a2e4a; }
    .result-range  { font-size: 0.9rem; color: #555; margin-top: 0.2rem; }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e6ea;
        border-radius: 8px;
        padding: 0.8rem 1rem;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 2px solid #dee2e6; }
    .stTabs [data-baseweb="tab"] {
        padding: 0.6rem 1.4rem;
        font-size: 0.88rem;
        font-weight: 500;
        color: #6c757d;
        border-radius: 0;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
    }
    .stTabs [aria-selected="true"] {
        color: #1a2e4a !important;
        border-bottom: 2px solid #1a2e4a !important;
        font-weight: 600;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: #1a2e4a;
        border: none;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .stButton > button[kind="primary"]:hover {
        background: #253d61;
        border: none;
    }

    /* Divider */
    hr { border-color: #e2e6ea; }
</style>
""", unsafe_allow_html=True)


# ─── Load model ───────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    with open("clinic_model.pkl", "rb") as f:
        return pickle.load(f)

try:
    model = load_model()
    model_loaded = True
except FileNotFoundError:
    model_loaded = False


# ─── Weather fetch ─────────────────────────────────────────────────────────────
def _fetch_from_api(url: str, lat: float, lon: float,
                    start: str, end: str) -> pd.DataFrame | None:
    """Call one Open-Meteo API endpoint and return a DataFrame or None."""
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "daily":      ["temperature_2m_max", "precipitation_sum"],
        "start_date": start,
        "end_date":   end,
        "timezone":   "auto",
    }
    try:
        data = requests.get(url, params=params, timeout=15).json()
    except Exception:
        return None
    if "daily" not in data:
        return None
    return pd.DataFrame({
        "date":        data["daily"]["time"],
        "temperature": data["daily"]["temperature_2m_max"],
        "rainfall":    data["daily"]["precipitation_sum"],
    })


def fetch_weather(city: str, dates: list) -> pd.DataFrame:
    """
    Fetch daily max-temperature and precipitation for every date in the list.

    Strategy:
      - Geocode the city to lat/lon.
      - Split dates into PAST (≤ today) and FUTURE (> today).
      - Past dates → Open-Meteo archive API (has full historical data).
      - Future dates → Open-Meteo forecast API (up to 16 days ahead).
      - Combine both results into one DataFrame.
      - Any date that neither API could cover gets filled later with defaults.

    Returns a DataFrame[date, temperature, rainfall] or None if geocoding fails.
    """
    # ── Step 1: geocode ──────────────────────────────────────────────────────
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=10,
        ).json()
    except Exception:
        return None

    if not geo.get("results"):
        return None

    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    # ── Step 2: split dates by today ─────────────────────────────────────────
    today_str = date.today().strftime("%Y-%m-%d")
    past_dates   = sorted(d for d in dates if d <= today_str)
    future_dates = sorted(d for d in dates if d  > today_str)

    ARCHIVE_URL  = "https://archive-api.open-meteo.com/v1/archive"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    frames = []

    # ── Past dates → archive API ─────────────────────────────────────────────
    if past_dates:
        df = _fetch_from_api(ARCHIVE_URL, lat, lon,
                             past_dates[0], past_dates[-1])
        if df is not None:
            frames.append(df)

    # ── Future dates → forecast API ──────────────────────────────────────────
    if future_dates:
        df = _fetch_from_api(FORECAST_URL, lat, lon,
                             future_dates[0], future_dates[-1])
        if df is not None:
            frames.append(df)

    if not frames:
        return None

    # ── Combine and keep only dates we actually asked for ────────────────────
    combined = pd.concat(frames, ignore_index=True)
    combined = combined[combined["date"].isin(dates)].drop_duplicates("date")
    return combined.reset_index(drop=True)


# ─── Calendar parser ───────────────────────────────────────────────────────────
def parse_calendar(uploaded_file) -> pd.DataFrame:
    """
    Read any CSV or Excel academic calendar file — robustly.

    Rules:
      - Any column whose name contains 'date' is used as the date column.
      - exam_period is read if present; otherwise inferred from common synonyms;
        otherwise defaults to 0 with a warning.
      - Any extra columns (period_label, semester, notes, etc.) are ignored.
      - Weekends are NOT filtered out — the app predicts whatever dates are given.
      - Duplicate dates are deduplicated (first occurrence kept).

    Returns DataFrame[date (YYYY-MM-DD str), exam_period (int 0/1)] or None on error.
    """
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            # Try UTF-8 first, fall back to latin-1 for files with special chars
            try:
                cal = pd.read_csv(uploaded_file, encoding="utf-8")
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                cal = pd.read_csv(uploaded_file, encoding="latin-1")
        elif name.endswith((".xlsx", ".xls")):
            cal = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a CSV or Excel (.xlsx / .xls) file.")
            return None
    except Exception as e:
        st.error(f"Could not open the file: {e}")
        return None

    if cal.empty:
        st.error("The uploaded file appears to be empty.")
        return None

    # Normalise column names
    cal.columns = [str(c).strip().lower().replace(" ", "_") for c in cal.columns]

    # ── Find date column ─────────────────────────────────────────────────────
    date_col = next((c for c in cal.columns if "date" in c), None)
    if date_col is None:
        st.error(
            "No date column found. Make sure your file has a column whose name "
            "contains the word 'date' (e.g. 'date', 'Date', 'event_date')."
        )
        return None

    cal["date"] = pd.to_datetime(cal[date_col], dayfirst=False, errors="coerce").dt.strftime("%Y-%m-%d")
    bad_dates = cal["date"].isna().sum()
    cal = cal.dropna(subset=["date"])

    if bad_dates > 0:
        st.warning(f"{bad_dates} row(s) had unreadable dates and were skipped.")

    if cal.empty:
        st.error("No valid dates could be read from the file.")
        return None

    # ── Find or build exam_period column ────────────────────────────────────
    EXAM_SYNONYMS = ["is_exam", "exam", "type", "event", "period",
                     "exam_period", "exams", "assessment"]
    EXAM_VALUES   = {"1", "yes", "true", "exam", "exam period", "exams",
                     "cat week", "cat", "examination", "examinations",
                     "semester 1 – examinations", "semester 2 – examinations",
                     "semester 1 – cat week", "semester 2 – cat week"}

    if "exam_period" in cal.columns:
        # Column exists — handle both numeric (0/1) and text ("Yes"/"No") values
        def to_exam_flag(v):
            s = str(v).strip().lower()
            if s in {"1", "yes", "true"}:
                return 1
            try:
                return 1 if int(float(s)) == 1 else 0
            except (ValueError, TypeError):
                return 0
        cal["exam_period"] = cal["exam_period"].apply(to_exam_flag)

    else:
        # Look for a synonym column
        exam_col = next(
            (c for c in cal.columns if c in EXAM_SYNONYMS), None
        )
        if exam_col:
            cal["exam_period"] = cal[exam_col].apply(
                lambda v: 1 if str(v).strip().lower() in EXAM_VALUES else 0
            )
            st.info(
                f"No 'exam_period' column found — used '{exam_col}' column to determine exam days."
            )
        elif "period_label" in cal.columns:
            # Rich calendar format: infer from period_label text
            cal["exam_period"] = cal["period_label"].apply(
                lambda v: 1 if str(v).strip().lower() in EXAM_VALUES else 0
            )
            st.info("Exam periods inferred from the 'period_label' column.")
        else:
            cal["exam_period"] = 0
            st.warning(
                "No exam period column found. All dates treated as Regular Days. "
                "For accurate predictions add an 'exam_period' column (1 = exam, 0 = regular)."
            )

    result = (
        cal[["date", "exam_period"]]
        .drop_duplicates("date")
        .reset_index(drop=True)
    )
    return result


# ─── Categorical-to-numeric helpers ───────────────────────────────────────────
RAINFALL_MAP = {
    "None (0 mm)":         0.0,
    "Light (1 – 5 mm)":    3.0,
    "Moderate (6 – 20 mm)": 13.0,
    "Heavy (21 – 50 mm)":  35.0,
    "Very Heavy (> 50 mm)": 70.0,
}

TEMPERATURE_MAP = {
    "Cold (< 15 °C)":        12.0,
    "Cool (15 – 19 °C)":     17.0,
    "Mild (20 – 24 °C)":     22.0,
    "Warm (25 – 29 °C)":     27.0,
    "Hot (≥ 30 °C)":         32.0,
}


# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
    <h1>University Clinic &mdash; Patient Volume Prediction</h1>
    <p>Internal tool for clinic supervisors · Predictions are model estimates, not guarantees</p>
</div>
""", unsafe_allow_html=True)

if not model_loaded:
    st.error(
        "Model file `clinic_model.pkl` not found. "
        "Run the training notebook and place the file in the same directory as this app."
    )
    st.stop()

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Calendar & Live Weather", "Quick Single-Day Estimate"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CALENDAR + WEATHER
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    st.markdown('<div class="section-title">Step 1 — Academic Calendar</div>', unsafe_allow_html=True)
    
    uploaded_cal = st.file_uploader(
        "Academic calendar file", type=["csv", "xlsx", "xls"], key="cal_upload", label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown('<div class="section-title">Step 2 — University City</div>', unsafe_allow_html=True)
    city = st.text_input(
        "City name", value="Nairobi", placeholder="e.g. Nairobi, Cape Town, Lagos…",
        label_visibility="collapsed"
    )

    st.markdown("---")

    run = st.button("Run Predictions", type="primary", use_container_width=False)

    if run:
        if uploaded_cal is None:
            st.error("Please upload an academic calendar file before running.")
        elif not city.strip():
            st.error("Please enter a city name.")
        else:
            with st.spinner("Reading calendar…"):
                cal_df = parse_calendar(uploaded_cal)

            if cal_df is None:
                st.error(
                    "Could not read the calendar file. "
                    "Ensure it has a 'date' column and is saved as CSV or Excel."
                )
            else:
                with st.spinner(f"Fetching weather data for {city}…"):
                    weather_df = fetch_weather(city, cal_df["date"].tolist())

                if weather_df is None:
                    st.error(
                        f"Weather data could not be retrieved for '{city}'. "
                        "Check the city name spelling and try again."
                    )
                else:
                    merged = cal_df.merge(weather_df, on="date", how="left")

                    # Report coverage before filling gaps
                    covered = merged["temperature"].notna().sum()
                    total   = len(merged)
                    missing = total - covered
                    if missing == 0:
                        st.success(f"Weather data: {covered}/{total} dates covered.")
                    else:
                        st.warning(
                            f"Weather data: {covered}/{total} dates covered. "
                            f"{missing} date(s) had no forecast or archive data — "
                            "those dates will use default values (25 °C, 0 mm rainfall)."
                        )

                    merged["temperature"] = merged["temperature"].fillna(25.0)
                    merged["rainfall"]    = merged["rainfall"].fillna(0.0)

                    X = merged[["exam_period", "rainfall", "temperature"]].values
                    merged["predicted_patients"] = (
                        model.predict(X).round(0).astype(int).clip(min=0)
                    )
                    merged["period"] = merged["exam_period"].map(
                        {1: "Exam Period", 0: "Regular Day"}
                    )

                    # ── Summary metrics ────────────────────────────────────
                    st.markdown("---")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Total Dates",        len(merged))
                    c2.metric("Exam Days",           int(merged["exam_period"].sum()))
                    c3.metric("Avg Patients / Day",  int(merged["predicted_patients"].mean()))
                    c4.metric("Peak Day",            int(merged["predicted_patients"].max()))

                    # ── Chart ──────────────────────────────────────────────
                    st.markdown("**Daily Patient Volume Forecast**")
                    chart_data = merged.set_index("date")[["predicted_patients"]].rename(
                        columns={"predicted_patients": "Patients"}
                    )
                    st.line_chart(chart_data, use_container_width=True)

                    # ── Table ──────────────────────────────────────────────
                    st.markdown("**Full Daily Breakdown**")
                    display_df = merged[[
                        "date", "period", "temperature", "rainfall", "predicted_patients"
                    ]].rename(columns={
                        "date":               "Date",
                        "period":             "Period",
                        "temperature":        "Temp (°C)",
                        "rainfall":           "Rainfall (mm)",
                        "predicted_patients": "Predicted Patients",
                    })
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                    # ── Download ───────────────────────────────────────────
                    st.download_button(
                        "Download as CSV",
                        data=display_df.to_csv(index=False).encode("utf-8"),
                        file_name="clinic_predictions.csv",
                        mime="text/csv",
                    )

                    # ── Exam vs Regular comparison ─────────────────────────
                    st.markdown("**Exam Period vs Regular Days — Summary**")
                    comp = (
                        merged.groupby("exam_period")["predicted_patients"]
                        .agg(["mean", "min", "max"])
                        .round(0).astype(int)
                    )
                    comp.index = ["Regular Days", "Exam Period"]
                    comp.columns = ["Average", "Minimum", "Maximum"]
                    st.dataframe(comp, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MANUAL SINGLE-DAY ESTIMATE
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    st.markdown(
        "Use this for a quick estimate when you don't have a full calendar. "
        "Select the conditions that best describe the day."
    )
    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">Academic Period</div>', unsafe_allow_html=True)
        exam_label = st.selectbox(
            "Period type",
            options=["Regular Day", "Exam Period"],
            label_visibility="collapsed",
        )
        exam_val = 1 if exam_label == "Exam Period" else 0

        st.markdown('<div class="section-title" style="margin-top:1.2rem;">Rainfall</div>', unsafe_allow_html=True)
        rainfall_label = st.selectbox(
            "Rainfall level",
            options=list(RAINFALL_MAP.keys()),
            index=1,   # default: Light
            label_visibility="collapsed",
        )

    with col_b:
        st.markdown('<div class="section-title">Temperature</div>', unsafe_allow_html=True)
        temp_label = st.selectbox(
            "Temperature range",
            options=list(TEMPERATURE_MAP.keys()),
            index=2,   # default: Mild
            label_visibility="collapsed",
        )

    st.markdown("---")
    predict_btn = st.button("Estimate Patient Volume", type="primary")

    if predict_btn:
        rainfall_val = RAINFALL_MAP[rainfall_label]
        temp_val     = TEMPERATURE_MAP[temp_label]

        features   = np.array([[exam_val, rainfall_val, temp_val]])
        prediction = max(0, round(float(model.predict(features)[0])))
        low        = int(prediction * 0.85)
        high       = int(prediction * 1.15)

        period_text   = "an exam period" if exam_val == 1 else "a regular day"
        rainfall_text = rainfall_label.split(" (")[0].lower()
        temp_text     = temp_label.split(" (")[0].lower()

        st.markdown(f"""
        <div class="result-box">
            <div style="font-size:0.8rem;font-weight:600;letter-spacing:0.06em;
                        text-transform:uppercase;color:#6c757d;margin-bottom:0.3rem;">
                Predicted Patient Volume
            </div>
            <div class="result-number">{prediction}</div>
            <div class="result-range">Estimated range: {low} – {high} patients (± 15 %)</div>
            <div style="margin-top:0.8rem;font-size:0.88rem;color:#444;">
                On {period_text} with {rainfall_text} rainfall and {temp_text} temperatures,
                the clinic is projected to receive approximately <strong>{prediction} patients</strong>.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Weather data: [Open-Meteo](https://open-meteo.com/) (free, no API key required). "
    "Predictions are estimates from a trained Linear Regression model."
)
