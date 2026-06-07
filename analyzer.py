import streamlit as st
st.title("Loading...")
st.write("App is starting")

import anthropic
import os
import csv
import plotly.express as px
import pandas as pd
from collections import defaultdict
from dotenv import load_dotenv

st.write("Imports ok")

load_dotenv()
st.write("Dotenv ok")

api_key = os.getenv("ANTHROPIC_API_KEY")
st.write(f"API key found: {bool(api_key)}")

client = anthropic.Anthropic(api_key=api_key)
st.write("Client ok")

st.title("📊 Market Signal Analyzer")
st.write("Everything loaded successfully")

# Test CSV reading
if os.path.exists("results.csv"):
    st.write("results.csv found")
    with open("results.csv", "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    st.write(f"Rows in CSV: {len(rows)}")
    st.write("First row keys:", list(rows[0].keys()))
else:
    st.error("results.csv NOT found — this is the problem")

# Test tabs
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])
with tab1:
    st.write("Tab 1 works")
with tab2:
    st.write("Tab 2 works")