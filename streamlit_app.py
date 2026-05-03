import streamlit as st
import pickle
import numpy as np

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Clinic Demand Dashboard",
    page_icon="🏥",
    layout="centered"
)

# -------------------------
# LOAD MODEL
# -------------------------
with open("clinic_model.pkl", "rb") as file:
    model = pickle.load(file)

# -------------------------
# HEADER
# -------------------------
st.title("🏥 Clinic Patient Demand Dashboard")
st.markdown("### AI-powered prediction system for hospital planning")

st.markdown("---")

# -------------------------
# INPUT SECTION (CARD STYLE)
# -------------------------
st.subheader("📊 Input Patient Demand Factors")

col1, col2 = st.columns(2)

with col1:
    exam_period_label = st.selectbox(
        "Exam Period",
        ["No Exam Period", "Exam Period Active"]
    )
    exam_period = 1 if exam_period_label == "Exam Period Active" else 0

    rainfall_label = st.selectbox(
        "Rainfall Level",
        ["Low", "Moderate", "High", "Very High"]
    )

with col2:
    temperature_label = st.selectbox(
        "Temperature Level",
        ["Cold", "Mild", "Warm", "Hot"]
    )

# mapping
rainfall_map = {
    "Low": 25,
    "Moderate": 100,
    "High": 200,
    "Very High": 350
}

temp_map = {
    "Cold": 15,
    "Mild": 22,
    "Warm": 28,
    "Hot": 38
}

rainfall = rainfall_map[rainfall_label]
temperature = temp_map[temperature_label]

st.markdown("---")

# -------------------------
# PREDICTION BUTTON
# -------------------------
if st.button("🔍 Predict Patient Demand"):

    features = np.array([[exam_period, rainfall, temperature]])
    prediction = model.predict(features)[0]

    # -------------------------
    # KPI DISPLAY
    # -------------------------
    st.subheader("📈 Prediction Result")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Predicted Patients", f"{round(prediction)}")

    with col2:
        st.metric("Low Scenario", f"{round(prediction * 0.6)}")

    with col3:
        st.metric("High Scenario", f"{round(prediction * 1.4)}")

    # -------------------------
    # RISK LEVEL
    # -------------------------
    st.subheader("⚠️ Demand Risk Level")

    if prediction < 30:
        st.success("Low Demand 🟢")
    elif prediction < 70:
        st.warning("Moderate Demand 🟡")
    else:
        st.error("High Demand 🔴")

    # -------------------------
    # CHART
    # -------------------------
    st.subheader("📊 Demand Trend Visualization")

    st.line_chart({
        "Low": [prediction * 0.6],
        "Expected": [prediction],
        "High": [prediction * 1.4]
    })

st.markdown("---")
st.caption("Clinic Demand Prediction System | Final Year Project")