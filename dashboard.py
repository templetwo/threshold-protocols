import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import subprocess
import psutil
import time
import os
from pathlib import Path
import yaml
import json
from datetime import datetime

# Threshold Protocols Dashboard
# Monitors circuit metrics, sim outcomes, Jetson perf, thresholds

st.set_page_config(page_title="Threshold Protocols Dashboard", layout="wide")

# Sidebar
st.sidebar.title("🌀 Threshold Monitor")
refresh = st.sidebar.slider("Refresh (s)", 5, 60, 10)
jetson_ip = st.sidebar.text_input("Jetson IP", "192.168.1.205")
mode = st.sidebar.selectbox("Mode", ["Local", "Jetson", "Full"])


# Cache metrics
@st.cache_data(ttl=refresh)
def get_local_metrics():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    return {"cpu": cpu, "mem_used": mem.percent, "timestamp": datetime.now()}


@st.cache_data(ttl=refresh)
def get_jetson_metrics(ip):
    try:
        result = subprocess.run(
            [
                "ssh",
                f"tony@{ip}",
                "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        gpu_util, mem_used = result.stdout.strip().split(", ")
        result = subprocess.run(
            ["ssh", f"tony@{ip}", "psutil cpu mem"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {"gpu_util": gpu_util, "gpu_mem": mem_used, "timestamp": datetime.now()}
    except:
        return {"error": "Jetson unreachable"}


@st.cache_data(ttl=3600)
def load_rollout():
    with open("rollout.yaml") as f:
        return yaml.safe_load(f)


@st.cache_data(ttl=3600)
def load_recent_logs():
    logs = []
    if Path("intervention/logs").exists():
        for f in Path("intervention/logs").glob("*.json"):
            try:
                data = json.load(f.open())
                logs.append(data.get("summary", {}))
            except:
                pass
    return pd.DataFrame(logs) if logs else pd.DataFrame()


# Pages
tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Circuit Metrics", "Jetson Perf", "Rollout & Logs"]
)

with tab1:
    st.title("🌀 Threshold Protocols Dashboard")
    col1, col2 = st.columns(2)
    with col1:
        local = get_local_metrics()
        st.metric("Local CPU", f"{local['cpu']}%")
        st.metric("Local MEM", f"{local['mem_used']}%")
    with col2:
        jetson = get_jetson_metrics(jetson_ip)
        if "error" not in jetson:
            st.metric("Jetson GPU Util", f"{jetson['gpu_util']}%")
            st.metric("Jetson GPU MEM", f"{jetson['gpu_mem']}%")
        else:
            st.error(jetson["error"])

with tab2:
    st.subheader("Sim Outcomes & Thresholds")
    # Mock data - integrate simulator
    df_sim = pd.DataFrame(
        {
            "scenario": ["REORGANIZE", "DEFER", "ROLLBACK"],
            "prob": [0.3, 0.25, 0.1],
            "reversibility": [0.65, 0.9, 0.95],
        }
    )
    fig = px.bar(df_sim, x="scenario", y="reversibility", color="prob")
    st.plotly_chart(fig)

with tab3:
    st.subheader("Jetson Live Perf")
    if mode == "Jetson":
        jetson = get_jetson_metrics(jetson_ip)
        if "gpu_util" in jetson:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=[jetson["gpu_util"]], name="GPU %"))
            st.plotly_chart(fig)
        st.button("MLX Test Run")

with tab4:
    rollout = load_rollout()
    st.json(rollout)
    logs = load_recent_logs()
    if not logs.empty:
        st.dataframe(logs)

# Auto-refresh
time.sleep(refresh)
st.rerun()

if st.sidebar.button("Run Live Fire"):
    os.system("python examples/btb/derive_harness.py --scenario live_fire --count 100")
