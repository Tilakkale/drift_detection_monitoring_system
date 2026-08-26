import altair as alt
import numpy as np
import os
import pandas as pd
import requests
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Drift Monitoring System",
    page_icon="📊",
    layout="wide",
)

API = os.getenv("DRIFT_API_URL", "http://127.0.0.1:8000").rstrip("/")

# Dataset path (same machine as the backend)
DATASET = Path(__file__).resolve().parents[2] / "dataset" / "ServerMachineDataset"

# ---------------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container{
        padding-top:1.5rem;
        padding-bottom:2rem;
    }

    .hero{
        background:linear-gradient(135deg,#0f172a,#2563eb);
        color:white;
        padding:1.2rem 1.4rem;
        border-radius:14px;
        margin-bottom:1rem;
    }

    
    .hero h1{
        margin-bottom:0.2rem;
    }

    .hero p{
        opacity:0.9;
    }

    .status-pill{
        display:inline-block;
        padding:0.25rem 0.9rem;
        border-radius:999px;
        font-weight:600;
        font-size:0.85rem;
    }
    .pill-green{ background:#dcfce7; color:#15803d; }
    .pill-yellow{ background:#fef9c3; color:#a16207; }
    .pill-red{ background:#fee2e2; color:#b91c1c; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>📊 Drift Monitoring System</h1>
        <p>
        Production-ready monitoring for server machine behavior with
        Drift Detection, PSI Analysis and Anomaly Detection.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------
def psi_category(score):
    if score > 0.25:
        return "Significant"
    if score > 0.10:
        return "Moderate"
    return "No Drift"


def psi_color(score):
    if score > 0.25:
        return "#e74c3c"
    if score > 0.10:
        return "#f39c12"
    return "#2ecc71"


def load_machine_data(machine_id, dataset_type="train"):
    """Load raw dataset rows for a machine (train or test)."""
    data_dir = DATASET / dataset_type
    if not data_dir.exists():
        return None
    files = sorted(data_dir.glob(f"machine-{machine_id}-*.txt"))
    if not files:
        return None
    frames = [pd.read_csv(f, header=None) for f in files]
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------
with st.sidebar:

    st.header("⚙️ Controls")

    machine_id = st.selectbox(
        "Select Machine",
        [1, 2, 3],
        format_func=lambda x: f"Machine {x}",
    )

    buckets = st.slider(
        "PSI Buckets",
        5,
        50,
        10,
    )

    run_drift = st.button(
        "Run Drift Analysis",
        use_container_width=True,
    )

    run_eval = st.button(
        "Run Model Evaluation",
        use_container_width=True,
    )

    st.divider()

    try:

        health = requests.get(
            f"{API}/health",
            timeout=3,
        )

        if health.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Error")

    except Exception:

        st.error("❌ API Offline")


# ==========================================================
# TABS
# ==========================================================
tab1, tab2, tab3 = st.tabs(
    [
        "📉 Drift Analysis",
        "🤖 Model Evaluation",
        "🚨 Monitor",
    ]
)

# ==========================================================
# DRIFT ANALYSIS
# ==========================================================
with tab1:

    if run_drift:

        with st.spinner("Running Drift Analysis..."):

            try:

                response = requests.get(
                    f"{API}/analyze-drift",
                    params={
                        "machine_id": machine_id,
                        "buckets": buckets,
                    },
                    timeout=120,
                )

                response.raise_for_status()

                data = response.json()

            except Exception as exc:

                st.error(f"Unable to fetch drift analysis.\n\n{exc}")
                st.stop()

        # -------------------------
        # Summary Metrics
        # -------------------------
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

        if not df.empty:

            df["PSI Category"] = df["psi_score"].apply(psi_category)

            # -------------------------
            # 1. PSI Score Per Feature (bar chart)
            # -------------------------
            st.subheader("PSI Score Per Feature")

            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X(
                        "feature:N",
                        sort="-y",
                        axis=alt.Axis(labelAngle=-45),
                        title="Feature",
                    ),
                    y=alt.Y(
                        "psi_score:Q",
                        title="PSI Score",
                    ),
                    color=alt.Color(
                        "PSI Category:N",
                        scale=alt.Scale(
                            domain=["No Drift", "Moderate", "Significant"],
                            range=["#2ecc71", "#f39c12", "#e74c3c"],
                        ),
                        legend=alt.Legend(title="Drift Level"),
                    ),
                    tooltip=[
                        alt.Tooltip("feature:N", title="Feature"),
                        alt.Tooltip("psi_score:Q", title="PSI Score"),
                        alt.Tooltip("psi_status:N", title="PSI Status"),
                        alt.Tooltip("ks_statistic:Q", title="KS Statistic"),
                        alt.Tooltip("ks_p_value:Q", title="KS p-value"),
                        alt.Tooltip("high_confidence_drift:N", title="High Confidence"),
                    ],
                )
                .properties(height=420)
            )

            st.altair_chart(chart, use_container_width=True)

            st.divider()

            col1, col2, col3 = st.columns(3)
            col1.success("🟢 No Drift (PSI < 0.10)")
            col2.warning("🟡 Moderate Drift (0.10 – 0.25)")
            col3.error("🔴 Significant Drift (PSI > 0.25)")

            st.divider()

            # -------------------------
            # 2. Two-column layout: Category Donut + KS Statistic
            # -------------------------
            dcol1, dcol2 = st.columns(2)

            with dcol1:

                st.subheader("Drift Category Distribution")

                cat_counts = (
                    df["PSI Category"]
                    .value_counts()
                    .rename_axis("Category")
                    .reset_index(name="Count")
                )

                # Reorder categories for stable colors
                cat_order = ["No Drift", "Moderate", "Significant"]
                cat_counts["Category"] = pd.Categorical(
                    cat_counts["Category"],
                    categories=cat_order,
                    ordered=True,
                )
                cat_counts = cat_counts.sort_values("Category")

                donut = (
                    alt.Chart(cat_counts)
                    .mark_arc(innerRadius=55)
                    .encode(
                        theta=alt.Theta("Count:Q", title="Features"),
                        color=alt.Color(
                            "Category:N",
                            scale=alt.Scale(
                                domain=cat_order,
                                range=["#2ecc71", "#f39c12", "#e74c3c"],
                            ),
                            legend=alt.Legend(title="Drift Level"),
                        ),
                        tooltip=[
                            alt.Tooltip("Category:N"),
                            alt.Tooltip("Count:Q"),
                        ],
                    )
                    .properties(height=280)
                )

                # Center annotation via text layer
                total_features = int(df.shape[0])
                center_text = (
                    alt.Chart(pd.DataFrame({"v": [f"{drifted_count}/{total_features}"], "y": [1]}))
                    .mark_text(
                        align="center",
                        baseline="middle",
                        fontSize=18,
                        fontWeight="bold",
                        color="#1e3a5f",
                    )
                    .encode(text="v:N")
                )

                st.altair_chart(
                    donut + center_text,
                    use_container_width=True,
                )

            with dcol2:

                st.subheader("KS Statistic vs PSI Score")

                scatter = (
                    alt.Chart(df)
                    .mark_circle(size=120, opacity=0.8)
                    .encode(
                        x=alt.X(
                            "psi_score:Q",
                            title="PSI Score",
                            scale=alt.Scale(zero=False),
                        ),
                        y=alt.Y(
                            "ks_statistic:Q",
                            title="KS Statistic",
                            scale=alt.Scale(zero=False),
                        ),
                        color=alt.Color(
                            "PSI Category:N",
                            scale=alt.Scale(
                                domain=["No Drift", "Moderate", "Significant"],
                                range=["#2ecc71", "#f39c12", "#e74c3c"],
                            ),
                            legend=alt.Legend(title="Drift Level"),
                        ),
                        size=alt.Size(
                            "ks_p_value:Q",
                            scale=alt.Scale(range=[40, 400]),
                            title="KS p-value (inverse)",
                        ),
                        tooltip=[
                            alt.Tooltip("feature:N"),
                            alt.Tooltip("psi_score:Q"),
                            alt.Tooltip("ks_statistic:Q"),
                            alt.Tooltip("ks_p_value:Q"),
                            alt.Tooltip("high_confidence_drift:N"),
                        ],
                    )
                    .properties(height=280)
                )

                # Add drift threshold reference lines
                vline = (
                    alt.Chart(pd.DataFrame({"x": [0.10, 0.25]}))
                    .mark_rule(color="gray", strokeDash=[4, 4])
                    .encode(x="x:Q")
                )

                st.altair_chart(scatter + vline, use_container_width=True)

            st.divider()

            # -------------------------
            # 3. Top Drifted Features (horizontal bar)
            # -------------------------
            st.subheader("Top Drifted Features")

            top_drifted = (
                df[df["psi_score"] > 0.10]
                .sort_values("psi_score", ascending=True)
                .tail(10)
            )

            if not top_drifted.empty:

                hbar = (
                    alt.Chart(top_drifted)
                    .mark_bar()
                    .encode(
                        x=alt.X("psi_score:Q", title="PSI Score"),
                        y=alt.Y("feature:N", sort="-x", title=""),
                        color=alt.Color(
                            "PSI Category:N",
                            scale=alt.Scale(
                                domain=["No Drift", "Moderate", "Significant"],
                                range=["#2ecc71", "#f39c12", "#e74c3c"],
                            ),
                        ),
                        tooltip=[
                            alt.Tooltip("feature:N"),
                            alt.Tooltip("psi_score:Q", format=".4f"),
                            alt.Tooltip("ks_p_value:Q", format=".4f"),
                        ],
                    )
                    .properties(height=300)
                )

                htext = hbar.mark_text(
                    align="left",
                    dx=4,
                    fontSize=11,
                ).encode(text=alt.Text("psi_score:Q", format=".3f"))

                st.altair_chart(hbar + htext, use_container_width=True)

            else:

                st.info("No features have drifted beyond the moderate threshold (PSI > 0.10).")

            st.divider()

            # -------------------------
            # 4. Raw Distribution Comparison (train vs test)
            # -------------------------
            st.subheader("Feature Distribution Comparison (Train vs Test)")

            train_raw = load_machine_data(machine_id, "train")
            test_raw = load_machine_data(machine_id, "test")

            if train_raw is not None and test_raw is not None:

                feature_idx = st.selectbox(
                    "Select Feature to Compare",
                    options=list(range(1, train_raw.shape[1] + 1)),
                    format_func=lambda x: f"Feature {x}",
                    key="dist_feature",
                )

                train_series = train_raw.iloc[:, feature_idx - 1]
                test_series = test_raw.iloc[:, feature_idx - 1]

                # Sub-sample for plotting speed
                train_sample = train_series.sample(
                    min(20000, len(train_series)),
                    random_state=42,
                )
                test_sample = test_series.sample(
                    min(20000, len(test_series)),
                    random_state=42,
                )

                dist_df = pd.DataFrame(
                    {
                        "value": pd.concat([train_sample, test_sample]),
                        "dataset": ["Train (Baseline)"] * len(train_sample)
                        + ["Test (Production)"] * len(test_sample),
                    }
                )

                dist_chart = (
                    alt.Chart(dist_df)
                    .transform_density(
                        "value",
                        groupby=["dataset"],
                        as_=["value", "density"],
                    )
                    .mark_area(opacity=0.55)
                    .encode(
                        x=alt.X("value:Q", title="Feature Value"),
                        y=alt.Y("density:Q", title="Density"),
                        color=alt.Color(
                            "dataset:N",
                            scale=alt.Scale(
                                domain=["Train (Baseline)", "Test (Production)"],
                                range=["#2563eb", "#e74c3c"],
                            ),
                            legend=alt.Legend(title="Dataset"),
                        ),
                        tooltip=["value:Q", "density:Q", "dataset:N"],
                    )
                    .properties(height=380)
                )

                # Show the feature's PSI in the header
                feat_psi = df[df["feature"] == f"feature_{feature_idx}"]["psi_score"]
                feat_psi_val = float(feat_psi.iloc[0]) if not feat_psi.empty else None

                if feat_psi_val is not None:
                    color = psi_color(feat_psi_val)
                    st.markdown(
                        f"<span class='status-pill' style='background:"
                        f"{color}22;color:{color};'>"
                        f"Feature {feature_idx} — PSI = {feat_psi_val:.4f}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("")

                st.altair_chart(dist_chart, use_container_width=True)

            else:

                st.warning("Raw dataset files not found for distribution comparison.")

            st.divider()

            # -------------------------
            # 5. Full results table + download
            # -------------------------
            st.subheader("KS-Test + Ensemble Results")

            st.dataframe(
                df[
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

            st.download_button(
                label="⬇️ Download CSV",
                data=df.to_csv(index=False),
                file_name=f"drift_machine_{machine_id}.csv",
                mime="text/csv",
            )

        else:

            st.warning("No drift results available.")

    else:

        # Pre-run instructions
        st.info(
            "👈 Select a machine and press **'Run Drift Analysis'** "
            "to visualize PSI drift, KS statistics, and distribution shifts."
        )

# ==========================================================
# MODEL EVALUATION
# ==========================================================
with tab2:

    if run_eval:

        with st.spinner("Running Model Evaluation..."):

            try:

                response = requests.post(
                    f"{API}/evaluation/{machine_id}/run",
                    timeout=120,
                )

                response.raise_for_status()

                ev = response.json()

            except Exception as exc:

                st.error(f"Evaluation failed\n\n{exc}")
                st.stop()

        if ev.get("status") == "skipped":

            st.info(
                ev.get(
                    "message",
                    "No evaluation metrics available.",
                )
            )

        else:

            # ==========================
            # Performance Metrics
            # ==========================
            st.subheader("📈 Performance Metrics")

            c1, c2, c3, c4 = st.columns(4)

            accuracy = ev.get("accuracy")
            precision = ev.get("precision")
            recall = ev.get("recall")
            f1 = ev.get("f1_score")

            c1.metric(
                "Accuracy",
                f"{accuracy*100:.2f}%" if accuracy is not None else "N/A",
            )

            c2.metric(
                "Precision",
                f"{precision*100:.2f}%" if precision is not None else "N/A",
            )

            c3.metric(
                "Recall",
                f"{recall*100:.2f}%" if recall is not None else "N/A",
            )

            c4.metric(
                "F1 Score",
                f"{f1*100:.2f}%" if f1 is not None else "N/A",
            )

            st.divider()

            # ==========================
            # Metric Bars (visualization)
            # ==========================
            st.subheader("Performance Metrics Comparison")

            metric_names = ["Accuracy", "Precision", "Recall", "F1 Score"]
            metric_values = [accuracy, precision, recall, f1]

            if any(v is not None for v in metric_values):

                metrics_df = pd.DataFrame(
                    {
                        "Metric": metric_names,
                        "Value": [v if v is not None else 0 for v in metric_values],
                        "Display": [
                            f"{v*100:.1f}%" if v is not None else "N/A"
                            for v in metric_values
                        ],
                    }
                )

                metric_chart = (
                    alt.Chart(metrics_df)
                    .mark_bar(size=45)
                    .encode(
                        x=alt.X("Metric:N", title=""),
                        y=alt.Y("Value:Q", title="Score (0–1)", scale=alt.Scale(domain=[0, 1])),
                        color=alt.Color(
                            "Metric:N",
                            scale=alt.Scale(
                                domain=metric_names,
                                range=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"],
                            ),
                            legend=None,
                        ),
                        tooltip=["Metric:N", "Display:N"],
                    )
                    .properties(height=320)
                )

                text_labels = metric_chart.mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-5,
                    fontSize=13,
                    fontWeight="bold",
                ).encode(text="Display:N")

                st.altair_chart(metric_chart + text_labels, use_container_width=True)

            st.divider()

            # ==========================
            # Dataset Statistics
            # ==========================
            st.subheader("📊 Dataset Statistics")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Total Samples", ev.get("total_samples", 0))
            c2.metric("True Anomalies", ev.get("true_anomalies", 0))
            c3.metric("Predicted Anomalies", ev.get("predicted_anomalies", 0))
            c4.metric("Machine", f"Machine {machine_id}")

            st.divider()

            # ==========================
            # Confusion Matrix (heatmap)
            # ==========================
            st.subheader("Confusion Matrix")

            cm_raw = ev.get("confusion_matrix", [])

            if cm_raw:

                cm_labels = ["Normal", "Anomaly"]

                cm_df = pd.DataFrame(
                    cm_raw,
                    index=[f"Actual {cm_labels[0]}", f"Actual {cm_labels[1]}"],
                    columns=[f"Predicted {cm_labels[0]}", f"Predicted {cm_labels[1]}"],
                )

                # Heatmap via Altair
                heat_df = cm_df.reset_index().melt(
                    id_vars="index",
                    var_name="Predicted",
                    value_name="Count",
                )
                heat_df = heat_df.rename(columns={"index": "Actual"})

                heat_chart = (
                    alt.Chart(heat_df)
                    .mark_rect()
                    .encode(
                        x=alt.X("Predicted:N", title="Predicted"),
                        y=alt.Y("Actual:N", title="Actual"),
                        color=alt.Color(
                            "Count:Q",
                            scale=alt.Scale(
                                scheme="blues",
                                domain=[0, heat_df["Count"].max() or 1],
                            ),
                            legend=alt.Legend(title="Count"),
                        ),
                        tooltip=["Actual:N", "Predicted:N", "Count:Q"],
                    )
                    .properties(width=420, height=320)
                )

                heat_text = (
                    alt.Chart(heat_df)
                    .mark_text(fontSize=18, fontWeight="bold", color="black")
                    .encode(
                        x=alt.X("Predicted:N"),
                        y=alt.Y("Actual:N"),
                        text=alt.Text("Count:Q", format=","),
                        color=alt.condition(
                            alt.datum.Count < (heat_df["Count"].max() or 1) / 2,
                            alt.value("black"),
                            alt.value("white"),
                        ),
                    )
                )

                st.altair_chart(heat_chart + heat_text, use_container_width=True)

            else:

                st.info("No confusion matrix available.")

    else:

        st.info(
            "👈 Select a machine and press **'Run Model Evaluation'** "
            "to see performance metrics and the confusion matrix."
        )

# ==========================================================
# MONITOR TAB
# ==========================================================
with tab3:

    st.subheader("🚨 Model Status")

    try:

        response = requests.get(
            f"{API}/monitor/status",
            timeout=5,
        )

        response.raise_for_status()

        status = response.json()

        st.success(f"✅ {status.get('total_models',0)} Models Loaded")
        st.info(f"Machines Loaded : {status.get('loaded_machines',0)}")

    except Exception:

        st.error("Unable to connect to Monitor API.")

    st.divider()

    # ==========================
    # Interactive anomaly monitor
    # ==========================
    st.subheader("🧪 Live Anomaly Detection Playground")

    st.caption(
        "Load rows from the machine's test dataset, run them through the "
        "Isolation Forest model via the `/monitor` API, and visualize the anomalies."
    )

    sample_size = st.slider(
        "Number of test rows to analyze",
        min_value=100,
        max_value=5000,
        value=1000,
        step=100,
    )

    run_monitor = st.button(
        "🚀 Run Monitor on Sample",
        type="primary",
        use_container_width=True,
    )

    if run_monitor:

        test_raw = load_machine_data(machine_id, "test")

        if test_raw is None:

            st.error("Test dataset not found.")

        else:

            # Take a sample of rows
            sample_df = test_raw.sample(
                min(sample_size, len(test_raw)),
                random_state=42,
            ).reset_index(drop=True)

            # Limit rows sent to API (avoid payload too large)
            api_sample = sample_df.head(2000)

            payload = {
                "machine_id": machine_id,
                "data": api_sample.values.tolist(),
            }

            with st.spinner(f"Running Isolation Forest on {len(api_sample)} rows..."):

                try:

                    resp = requests.post(
                        f"{API}/monitor",
                        json=payload,
                        timeout=120,
                    )

                    resp.raise_for_status()

                    mon = resp.json()

                except Exception as exc:

                    st.error(f"Monitor API failed\n\n{exc}")
                    st.stop()

            # -------------------------
            # Summary metrics
            # -------------------------
            total_rows = mon.get("total_rows", 0)
            anomaly_count = mon.get("anomaly_count", 0)
            anomaly_fraction = mon.get("anomaly_fraction", 0)

            mc1, mc2, mc3 = st.columns(3)

            mc1.metric("Total Rows", total_rows)
            mc2.metric("Anomalies Detected", anomaly_count)
            mc3.metric(
                "Anomaly Rate",
                f"{anomaly_fraction*100:.2f}%",
                delta=f"{anomaly_fraction*100:.2f}%",
            )

            st.divider()

            # -------------------------
            # Build per-row anomaly scores for visualization
            # -------------------------
            anomalies = mon.get("anomalies", [])
            anomaly_indices = {a["row_index"] for a in anomalies}

            vis_df = pd.DataFrame(
                {
                    "row_index": range(len(api_sample)),
                    "is_anomaly": [
                        1 if i in anomaly_indices else 0 for i in range(len(api_sample))
                    ],
                }
            )

            # Attach a sample anomaly score (from API if available)
            score_map = {a["row_index"]: a["anomaly_score"] for a in anomalies}
            vis_df["anomaly_score"] = vis_df["row_index"].map(score_map)

            vcol1, vcol2 = st.columns(2)

            with vcol1:

                st.subheader("Anomaly Score Distribution")

                # Build a synthetic score for normal rows for visualization
                if vis_df["anomaly_score"].isna().all():

                    st.info(
                        "Anomaly scores are only returned for detected anomalies. "
                        "Showing a bar chart of normal vs anomaly rows instead."
                    )

                    bar_counts = (
                        vis_df["is_anomaly"]
                        .value_counts()
                        .rename(index={0: "Normal", 1: "Anomaly"})
                        .rename_axis("Class")
                        .reset_index(name="Count")
                    )

                    class_chart = (
                        alt.Chart(bar_counts)
                        .mark_bar(size=55)
                        .encode(
                            x=alt.X("Class:N", title=""),
                            y=alt.Y("Count:Q", title="Rows"),
                            color=alt.Color(
                                "Class:N",
                                scale=alt.Scale(
                                    domain=["Normal", "Anomaly"],
                                    range=["#2ecc71", "#e74c3c"],
                                ),
                            ),
                            tooltip=["Class:N", "Count:Q"],
                        )
                        .properties(height=300)
                    )

                    st.altair_chart(class_chart, use_container_width=True)

                else:

                    score_df = vis_df.dropna(subset=["anomaly_score"]).copy()
                    score_df["severity"] = score_df["anomaly_score"].apply(
                        lambda s: "High" if s < -0.1 else "Medium"
                    )

                    score_chart = (
                        alt.Chart(score_df)
                        .mark_bar()
                        .encode(
                            x=alt.X(
                                "anomaly_score:Q",
                                title="Anomaly Score (decision function)",
                                bin=alt.Bin(maxbins=30),
                            ),
                            y=alt.Y("count()", title="Count"),
                            color=alt.Color(
                                "severity:N",
                                scale=alt.Scale(
                                    domain=["Medium", "High"],
                                    range=["#f39c12", "#e74c3c"],
                                ),
                                legend=alt.Legend(title="Severity"),
                            ),
                            tooltip=["anomaly_score:Q", "count()"],
                        )
                        .properties(height=300)
                    )

                    st.altair_chart(score_chart, use_container_width=True)

            with vcol2:

                st.subheader("Anomaly Severity Breakdown")

                if anomalies:

                    sev_counts = (
                        pd.DataFrame(anomalies)["severity"]
                        .value_counts()
                        .rename_axis("Severity")
                        .reset_index(name="Count")
                    )

                    sev_donut = (
                        alt.Chart(sev_counts)
                        .mark_arc(innerRadius=50)
                        .encode(
                            theta=alt.Theta("Count:Q"),
                            color=alt.Color(
                                "Severity:N",
                                scale=alt.Scale(
                                    domain=["Medium", "High"],
                                    range=["#f39c12", "#e74c3c"],
                                ),
                                legend=alt.Legend(title="Severity"),
                            ),
                            tooltip=["Severity:N", "Count:Q"],
                        )
                        .properties(height=300)
                    )

                    st.altair_chart(sev_donut, use_container_width=True)

                else:

                    st.info("No anomalies detected in this sample.")

            st.divider()

            # -------------------------
            # Anomaly position map (where anomalies occur in the batch)
            # -------------------------
            st.subheader("Anomaly Position in Batch")

            if anomalies:

                pos_df = pd.DataFrame(
                    {
                        "row_index": range(len(api_sample)),
                        "is_anomaly": vis_df["is_anomaly"],
                    }
                )

                tick_chart = (
                    alt.Chart(pos_df)
                    .mark_tick(size=14, thickness=2)
                    .encode(
                        x=alt.X(
                            "row_index:Q",
                            title="Row Index",
                            bin=alt.Bin(maxbins=60),
                        ),
                        y=alt.Y(
                            "is_anomaly:N",
                            title="",
                            sort=["0", "1"],
                        ),
                        color=alt.Color(
                            "is_anomaly:N",
                            scale=alt.Scale(
                                domain=["0", "1"],
                                range=["#2ecc71", "#e74c3c"],
                            ),
                            legend=alt.Legend(
                                title="Class",
                                labelExpr="datum.label == '1' ? 'Anomaly' : 'Normal'",
                            ),
                        ),
                    )
                    .properties(height=180)
                )

                st.altair_chart(tick_chart, use_container_width=True)

            else:

                st.info("No anomalies to visualize.")

            st.divider()

            st.subheader("🔍 Anomaly Details")

            if anomalies:

                details_df = pd.DataFrame(anomalies)
                details_df["severity_label"] = details_df["severity"].apply(
                    lambda s: "🔴 High" if s == "high" else "🟠 Medium"
                )
                st.dataframe(
                    details_df[["row_index", "anomaly_score", "severity_label"]],
                    use_container_width=True,
                    height=250,
                )

            else:

                st.success("✅ No anomalies found — the sample is healthy.")

    st.divider()

    st.subheader("📨 Send Test Batch")

    st.code(
        """
POST /monitor

{
    "machine_id":1,
    "data":[
        [38 feature values]
    ]
}
""",
        language="json",
    )

