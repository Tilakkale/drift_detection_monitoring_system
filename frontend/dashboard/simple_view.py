"""Compact Streamlit dashboard that highlights drift detection results."""

import os
import pandas as pd
import requests
import streamlit as st

API = os.getenv("DRIFT_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="Drift Detection", layout="wide")
st.title("Drift Detection Summary")
st.caption("PSI and KS-based drift view for server machine monitoring")

machine = st.selectbox("Machine ID", [1, 2, 3], index=0)
buckets = st.slider("PSI Buckets", 5, 50, 10)

if st.button("Run Drift Analysis", use_container_width=True):
    with st.spinner("Running drift analysis..."):
        try:
            response = requests.get(
                f"{API}/analyze-drift",
                params={"machine_id": machine, "buckets": buckets},
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            st.error(f"Unable to fetch drift analysis.\n\n{exc}")
            st.stop()

    avg_psi = round(float(data.get("average_psi", 0)), 4)
    drifted_count = data.get("drifted_feature_count", 0)
    high_conf_count = data.get("high_confidence_drift_count", 0)
    feature_count = data.get("feature_count", 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average PSI", avg_psi)
    c2.metric("Drifted Features", drifted_count)
    c3.metric("High Confidence Drift", high_conf_count)
    c4.metric("Total Features", feature_count)

    st.divider()

    df = pd.DataFrame(data.get("drift_results", []))
    if df.empty:
        st.warning("No drift results available.")
    else:
        st.subheader("Top Drifted Features")
        top_drifted = df[df["psi_score"] > 0.10].sort_values("psi_score", ascending=False)
        st.dataframe(
            top_drifted[
                [
                    "feature",
                    "psi_score",
                    "psi_status",
                    "ks_statistic",
                    "ks_p_value",
                    "ks_drift",
                    "high_confidence_drift",
                ]
            ],
            use_container_width=True,
            height=420,
        )

st.markdown("---")
st.write("Quick backend check:")
st.code("uvicorn backend.app.main:app --reload")
st.code("streamlit run frontend/dashboard/app.py")
