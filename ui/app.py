import streamlit as st
import requests
import os

st.set_page_config(page_title="Fraud Forge", layout="wide")

st.title("Fraud Forge Dashboard")

api_url = os.getenv("API_URL", "http://api:8000")

st.sidebar.header("Status")
try:
    response = requests.get(f"{api_url}/health")
    if response.status_code == 200:
        st.sidebar.success("API Connected")
    else:
        st.sidebar.error(f"API Error: {response.status_code}")
except Exception as e:
    st.sidebar.error(f"API Unavailable: {e}")

st.write("Welcome to the Fraud Forge War Room.")
