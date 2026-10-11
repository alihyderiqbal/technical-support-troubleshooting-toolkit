import streamlit as st
import datetime
import time
import requests

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Tier 2 Support Intelligence",
    page_icon="🛡️",
    layout="wide"
)

# ---------------------------------------------------------
# STYLING: Flawless Dark Navy SaaS Theme (Zero White Boxes)
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* Global App Background */
    .stApp {
        background-color: #050b1a;
        color: #f1f5f9;
    }
    
    /* Sidebar Background & Border */
    [data-testid="stSidebar"] {
        background-color: #070e1b;
        border-right: 1px solid #1b2a4a;
    }
    
    /* Force ALL text labels, headers, and paragraphs to be bright white */
    label, .stTextInput label, .stTextArea label, .stSelectbox label, p, span, h1, h2, h3, h4 {
        color: #f8fafc !important;
    }
    
    /* Input Fields & Text Areas */
    .stTextArea textarea, .stTextInput input {
        background-color
