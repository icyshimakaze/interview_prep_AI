"""Retired V1 launcher. Real assessments are served by the V2 web application."""

import streamlit as st

st.set_page_config(page_title="Interview Prep has moved", layout="centered")
st.title("Interview Prep has moved")
st.info("Self-rated sliders have been retired. Use the V2 Assessments workspace to answer questions, save attempts, and review scored responses.")
st.markdown("Start the frontend and API using the instructions in `docs/DEVELOPMENT.md`, then open **Assessments** in your account or the isolated demo workspace.")
st.caption("The original V1 source is retained only as a non-executable provenance fixture in content/provenance/streamlit-v1.txt.")
