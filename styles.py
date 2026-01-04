import streamlit as st

def apply_custom_css():
    # --- STEP 1: CSS FOR DASHBOARD TILES ---
    st.markdown("""
        <style>
        /* 1. Center the Title and adjust font weight */
        .main-title {
            text-align: center;
            font-weight: 300;
            letter-spacing: 1px;
            margin-bottom: 30px;
        }
        
        /* 2. Style the Benchmark Tiles (Glassmorphism) */
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 15px 20px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease;
        }
        
        [data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            border-color: #4e73df;
        }

        /* 3. Refine Metric Label and Value text */
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #808495 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        /* Style the Tab Bar container */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            border-bottom: 2px solid rgba(78, 115, 223, 0.1);
        }

        /* Style individual Tab buttons */
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px 4px 0px 0px;
            gap: 10px;
            font-weight: 600;
            color: #858796; /* Gray for inactive */
            transition: all 0.3s ease;
        }

        /* Style the Active Tab */
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #4e73df !important; /* Professional Blue */
            border-bottom: 3px solid #4e73df !important;
            background-color: rgba(78, 115, 223, 0.05);
        }

        /* Hover effect */
        .stTabs [data-baseweb="tab"]:hover {
            color: #4e73df;
            background-color: rgba(78, 115, 223, 0.02);
        }
        </style>
        """, unsafe_allow_html=True)
    
    # --- SURGICAL CSS FOR VISIBILITY ---
    # This fixes the "white-out" input boxes and ensures text is visible 
    # without overriding your entire theme.
    st.markdown("""
        <style>
        /* 1. Fix text input box visibility: Adds a distinct border and clear background */
        div[data-testid="stTextInput"] div[data-baseweb="input"] {
            border: 1px solid #4e73df !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
        }
        
        /* 2. Ensure the text typed inside the boxes is always visible */
        div[data-testid="stTextInput"] input {
            color: inherit !important;
        }

        /* 3. Make labels (titles above boxes) slightly bolder for readability */
        div[data-testid="stWidgetLabel"] p {
            font-weight: 600 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # --- STEP 1: CSS FOR THE ACCOUNT PROFILE CARD ---
    st.markdown("""
        <style>
        /* Profile Section Container - Integrated Blue Tint */
        .profile-card {
            background-color: rgba(78, 115, 223, 0.05);
            border: 1px solid rgba(78, 115, 223, 0.2);
            padding: 20px 25px;
            border-radius: 12px;
            margin-top: 10px;
            margin-bottom: 30px; /* Acts as an invisible divider */
        }
        
        /* Card Title Style */
        .card-title {
            margin-top: 0; 
            font-size: 1.2rem; 
            color: #4e73df;
            font-weight: 700;
            margin-bottom: 15px;
        }

        /* Small Label Styling */
        .profile-label {
            font-size: 0.75rem;
            color: #858796;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 2px;
            font-weight: 600;
        }
        
        /* Value Styling */
        .profile-value {
            font-size: 1.05rem;
            font-weight: 500;
            color: inherit; /* Adjusts to light/dark mode automatically */
            margin-bottom: 0;
        }
        </style>
        """, unsafe_allow_html=True)

    # --- STEP 1: ADD CSS FOR SUMMARY CARDS ---
    st.markdown("""
        <style>
        .summary-card {
            background: rgba(78, 115, 223, 0.05) !important;
            border: 1px solid rgba(78, 115, 223, 0.3) !important;
            padding: 25px !important;
            border-radius: 15px !important;
            margin-bottom: 30px !important;
            display: block !important;
        }
        .summary-label {
            font-size: 0.75rem !important;
            color: #858796 !important;
            text-transform: uppercase !important;
            margin-bottom: 5px !important;
            display: block !important;
        }
        .summary-value {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            color: inherit !important;
            margin: 0 !important;
        }
        .pnl-positive { color: #28a745 !important; }
        .pnl-negative { color: #dc3545 !important; }
        .sim-active { border: 1px solid #f6c23e !important; background: rgba(246, 194, 62, 0.05) !important; }
        </style>
        """, unsafe_allow_html=True)

    # --- STEP 1: CSS FOR CHARTS & RADIO BUTTONS ---
    st.markdown("""
        <style>
        /* Wrap charts in a card */
        .chart-container {
            background-color: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(78, 115, 223, 0.1);
            border-radius: 15px;
            padding: 20px;
        }
        
        /* Make Radio Buttons look like Pills */
        div[data-testid="stRadio"] > div {
            flex-direction: row;
            gap: 10px;
        }
        div[data-testid="stRadio"] label {
            background-color: rgba(78, 115, 223, 0.05);
            border: 1px solid rgba(78, 115, 223, 0.2);
            padding: 5px 15px;
            border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # 1. Inject the Card Styling (Put this once at the top of your script or right here)
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
            font-weight: 700 !important;
        }
        .stMetric {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(78,115,223,0.1);
            padding: 15px;
            border-radius: 12px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        /* Change the Primary Button Color (The Red one) */
        div.stButton > button[kind="primary"] {
            background-color: #36b9cc; /* Professional Royal Blue */
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            transition: all 0.3s ease;
        }

        /* Hover Effect: Darken slightly when mouse is over it */
        div.stButton > button[kind="primary"]:hover {
            background-color: #2e59d9;
            border-color: #2e59d9;
            box-shadow: 0 4px 15px rgba(78, 115, 223, 0.4);
        }

        /* Active/Click Effect */
        div.stButton > button[kind="primary"]:active {
            background-color: #224abe;
        }
        </style>
    """, unsafe_allow_html=True)