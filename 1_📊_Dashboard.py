import textwrap
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time, timedelta
import yfinance as yf
import plotly.graph_objects as go
import requests
from dateutil.relativedelta import relativedelta
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from styles import apply_custom_css  # Import the style function
import utils as ut 


# 1. Your curated dictionary of scheme codes
MY_FUNDS = {
    "PARAG PARIKH FLEXI CAP FUND - DIRECT PLAN": "122639",
    "UTI NIFTY 50 INDEX FUND - DIRECT PLAN": "120716",
    "ZERODHA NIFTY LARGEMIDCAP 250 INDEX FUND - DIRECT PLAN": "150393",
    "NAVI NIFTY NEXT 50 INDEX FUND - DIRECT PLAN": "148833",
    "ICICI PRUDENTIAL CORPORATE BOND FUND - DIRECT PLAN": "120692",
    "ADITYA BIRLA SUN LIFE BANKING & PSU DEBT FUND - DIRECT PLAN": "120531",
    "MOTILAL OSWAL NIFTY MIDCAP 150 INDEX FUND - DIRECT PLAN": "146916",
    "MOTILAL OSWAL NIFTY SMALLCAP 250 INDEX FUND - DIRECT PLAN": "146914",
    "MIRAE ASSET MIDCAP FUND - DIRECT PLAN": "146816",
    "ICICI PRUDENTIAL TECHNOLOGY FUND - DIRECT PLAN": "120594",
    "AXIS LARGE CAP FUND - DIRECT PLAN": "120465",
    "KOTAK SMALL CAP FUND - DIRECT PLAN": "120790"
}

# Page Config
st.set_page_config(page_title="Kite Portfolio Dashboard", page_icon="💰", layout="wide")

# 2. Apply the CSS from our separate file
apply_custom_css()

# --- STEP 2: CENTERED TITLE ---
st.markdown('<h1 class="main-title">💰 Zerodha Kite Portfolio Dashboard</h1>', unsafe_allow_html=True)

ut.show_live_benchmarks()

#st.write("<br>", unsafe_allow_html=True) # Subtle spacer instead of a heavy divider

# 1. Shows Login + What-If in Sidebar
ut.handle_kite_auth()
simulation_pct = ut.handle_what_if_sidebar()

# 2. Main Page Content
if st.session_state.get("authenticated"):
    try:
        if "kite" in st.session_state:
            kite_session = st.session_state.kite
            
            # --- STEP 2: ACCOUNT DETAILS LOGIC ---
            with st.spinner("🔄 Fetching Holdings & Profile..."):
                # Data Fetching
                user_profile = kite_session.profile()
                holdings = kite_session.holdings()
                mf_holdings = kite_session.mf_holdings()
                mf_sips = kite_session.mf_sips() 

                # We use a single markdown block to keep the HTML structure intact
                st.markdown(f"""
                <div class="profile-card">
                    <p class="card-title">👤 Account Identity</p>
                    <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 20px;">
                        <div style="flex: 1; min-width: 100px;">
                            <p class="profile-label">User ID</p>
                            <p class="profile-value">{user_profile['user_id']}</p>
                        </div>
                        <div style="flex: 1; min-width: 150px;">
                            <p class="profile-label">Username</p>
                            <p class="profile-value">{user_profile['user_name']}</p>
                        </div>
                        <div style="flex: 0.8; min-width: 100px;">
                            <p class="profile-label">Broker</p>
                            <p class="profile-value">{user_profile['broker']}</p>
                        </div>
                        <div style="flex: 1.5; min-width: 200px;">
                            <p class="profile-label">Email Address</p>
                            <p class="profile-value">{user_profile['email']}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # --- STEP A: PREPARE DATAFRAMES & SIMULATION ---
                multiplier = 1 + (simulation_pct / 100)
                
                df_eq = pd.DataFrame(holdings) if holdings else pd.DataFrame()
                df_mf = pd.DataFrame(mf_holdings) if mf_holdings else pd.DataFrame()

                if not df_eq.empty:
                    df_eq['invested_value'] = df_eq['quantity'] * df_eq['average_price']
                    # Apply simulation to current value
                    df_eq['current_value'] = (df_eq['quantity'] * df_eq['last_price']) * multiplier

                if not df_mf.empty:
                    df_mf['invested_value'] = df_mf['quantity'] * df_mf['average_price']
                    # Apply simulation to current value
                    df_mf['current_value'] = (df_mf['quantity'] * df_mf['last_price']) * multiplier

                # --- NEW: INSERT TOTAL SUMMARY HERE ---
                total_inv_combined = (df_eq['invested_value'].sum() if not df_eq.empty else 0) + \
                                     (df_mf['invested_value'].sum() if not df_mf.empty else 0)

                total_curr_combined = (df_eq['current_value'].sum() if not df_eq.empty else 0) + \
                                      (df_mf['current_value'].sum() if not df_mf.empty else 0)

                total_pnl_combined = total_curr_combined - total_inv_combined
                total_pnl_pct_combined = (total_pnl_combined / total_inv_combined * 100) if total_inv_combined != 0 else 0

                # --- FIXED PORTFOLIO OVERVIEW (No Code Leakage) ---

                # Determine colors and classes before rendering
                # --- PREPARE DATA BEFORE HTML ---
                pnl_color_class = "pnl-positive" if total_pnl_combined >= 0 else "pnl-negative"
                sim_status_class = "sim-active" if simulation_pct != 0 else ""
                display_label = "Current Value" if simulation_pct == 0 else f"Simulated ({simulation_pct:+.0f}%)"

                # Format the values using the helper function
                fmt_inv = ut.format_indian_currency(total_inv_combined)
                fmt_curr = ut.format_indian_currency(total_curr_combined)
                fmt_pnl = ut.format_indian_currency(total_pnl_combined)

                # --- RENDER SUMMARY ---
                st.markdown(f"""
                <div class="summary-card {sim_status_class}">
                    <p style="margin:0 0 20px 0; font-weight:700; color:#4e73df;">💰 PORTFOLIO OVERVIEW</p>
                    <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 20px;">
                        <div style="flex: 1;">
                            <span class="summary-label">Total Investment</span>
                            <p class="summary-value">₹{fmt_inv}</p>
                        </div>
                        <div style="flex: 1;">
                            <span class="summary-label">{display_label}</span>
                            <p class="summary-value" style="color:#4e73df;">₹{fmt_curr}</p>
                        </div>
                        <div style="flex: 1;">
                            <span class="summary-label">Combined P&L</span>
                            <p class="summary-value {pnl_color_class}">
                                ₹{fmt_pnl}
                                <span style="font-size:0.9rem; font-weight:400;">({total_pnl_pct_combined:+.2f}%)</span>
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # --- STEP 2: REFINED VISUALIZATION LOGIC ---
                st.markdown("### 💼 Portfolio Composition")

                total_eq_val = df_eq['current_value'].sum() if not df_eq.empty else 0
                total_mf_val = df_mf['current_value'].sum() if not df_mf.empty else 0
                grand_total = total_eq_val + total_mf_val

                # 1. Pre-format the values for the hover tooltip using your Indian formatter
                # We use customdata to pass these formatted strings to Plotly
                hover_values = [ut.format_indian_currency(total_eq_val), ut.format_indian_currency(total_mf_val)]

                viz_col1, viz_col2 = st.columns([1, 1.2]) # Give the Treemap slightly more room

                with viz_col1:
                    fig_asset = px.pie(
                        names=["Equity", "Mutual Funds"], 
                        values=[total_eq_val, total_mf_val], 
                        hole=0.6, 
                        color_discrete_sequence=['#4e73df', '#22c55e'] # Clean Blue and Green
                    )
                    # Professional Plotly Styling
                    fig_asset.update_traces(customdata=hover_values, textinfo='percent+label', pull=[0.05, 0],
                                            hovertemplate="<b>%{label}</b><br>Value: ₹%{customdata}<extra></extra>")
                    fig_asset.update_layout(
                        showlegend=False,
                        margin=dict(t=10, b=10, l=10, r=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        annotations=[dict(text=f'<span style="font-size:13px;color:#858796;">Total</span><br><b>₹{grand_total/100000:.1f}L</b>', x=0.5, y=0.5, font_size=18, showarrow=False)]
                    )
                    st.plotly_chart(fig_asset, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with viz_col2:
                    view_option = st.radio(
                        label="Select Category:",
                        options=["All", "Equity", "Mutual Funds"],
                        horizontal=True,
                        key="top_10_selector"
                    )

                    if view_option == "Equity":
                        df_top_10 = df_eq[['tradingsymbol', 'current_value']].rename(columns={'tradingsymbol': 'Name'}) if not df_eq.empty else pd.DataFrame()
                    elif view_option == "Mutual Funds":
                        df_top_10 = df_mf[['fund', 'current_value']].rename(columns={'fund': 'Name'}) if not df_mf.empty else pd.DataFrame()
                    else:
                        df_eq_sub = df_eq[['tradingsymbol', 'current_value']].rename(columns={'tradingsymbol': 'Name'}) if not df_eq.empty else pd.DataFrame()
                        df_mf_sub = df_mf[['fund', 'current_value']].rename(columns={'fund': 'Name'}) if not df_mf.empty else pd.DataFrame()
                        df_top_10 = pd.concat([df_eq_sub, df_mf_sub])

                    # --- WITHIN viz_col2 ---
                    if not df_top_10.empty:
                        df_top_10 = df_top_10.sort_values(by='current_value', ascending=False).head(10)

                        # 1. Clean names for better readability
                        df_top_10['Display_Name'] = df_top_10['Name'].str.replace(' - Direct Plan', '', case=False)
                        df_top_10['Display_Name'] = df_top_10['Display_Name'].str.replace('Growth Plan', '', case=False)
                        
                        # 2. Format values with 0 decimals (Strip everything after the decimal point)
                        # This keeps the Indian comma placement (e.g., 32,06,945)
                        df_top_10['formatted_val_0d'] = df_top_10['current_value'].apply(lambda x: ut.format_indian_currency(x).split('.')[0])

                        fig_tree = px.treemap(
                            df_top_10, 
                            path=[px.Constant("Top 10 Holdings"), 'Display_Name'], 
                            values='current_value',
                            color='current_value',
                            color_continuous_scale='Blues',
                            custom_data=['formatted_val_0d'] # Pass the 0-decimal string
                        )
                        
                        fig_tree.update_traces(
                            # Labels on the Treemap boxes
                            texttemplate="<b>%{label}</b><br>₹%{customdata[0]}", 
                            textposition="middle center",
                            textfont_size=14,
                            # Hover tooltip (now also 0 decimals)
                            hovertemplate="<b>%{label}</b><br>Value: ₹%{customdata[0]}<extra></extra>"
                        )
                        
                        fig_tree.update_layout(
                            margin=dict(t=0, l=0, r=0, b=0),
                            paper_bgcolor='rgba(0,0,0,0)',
                            coloraxis_showscale=False
                        )
                        st.plotly_chart(fig_tree, use_container_width=True)
                    else:
                        st.info(f"No {view_option} data available.")

                st.write("<br>", unsafe_allow_html=True)

            tab1, tab2, tab3 = st.tabs([
            "💎 EQUITY ASSETS", 
            "🧺 MUTUAL FUNDS", 
            "⏱️ SIP TRACKER"
        ])

            with tab1:
                if not df_eq.empty:
                    # Calculations for Tab 1 (already simulated in Step A)
                    df_eq['pnl'] = df_eq['current_value'] - df_eq['invested_value']
                    df_eq['pnl_pct'] = (df_eq['pnl'] / df_eq['invested_value']) * 100
                    df_eq = df_eq.sort_values(by='current_value', ascending=False).reset_index(drop=True)
                    df_eq.index = df_eq.index + 1
                    
                    # --- EQUITY CALCULATIONS ---
                    total_inv_eq = df_eq['invested_value'].sum()
                    current_val_eq = df_eq['current_value'].sum()
                    total_pnl_eq = current_val_eq - total_inv_eq
                    total_pnl_pct = (total_pnl_eq / total_inv_eq) * 100 if total_inv_eq != 0 else 0

                    # --- PREPARE FORMATTED STRINGS ---
                    fmt_inv_eq = ut.format_indian_currency(total_inv_eq)
                    fmt_curr_eq = ut.format_indian_currency(current_val_eq)
                    fmt_pnl_eq = ut.format_indian_currency(total_pnl_eq)

                    eq_pnl_class = "pnl-positive" if total_pnl_eq >= 0 else "pnl-negative"
                    sim_glow = "border: 1px solid #f6c23e;" if simulation_pct != 0 else "border: 1px solid rgba(78,115,223,0.1);"
                    curr_label_eq = "Current Value" if simulation_pct == 0 else f"Simulated ({simulation_pct:+.0f}%)"

                    # --- RENDER EQUITY HTML ---
                    equity_html = f"""
                    <div style="display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; width: 100%;">
                        <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.02); border: 1px solid rgba(78,115,223,0.1); padding: 15px; border-radius: 12px;">
                            <p style="font-size: 0.75rem; color: #858796; margin: 0; text-transform: uppercase;">Equity Investment</p>
                            <p style="font-size: 1.4rem; font-weight: 700; margin: 5px 0 0 0;">₹{fmt_inv_eq}</p>
                        </div>
                        <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.02); {sim_glow} padding: 15px; border-radius: 12px;">
                            <p style="font-size: 0.75rem; color: #858796; margin: 0; text-transform: uppercase;">{curr_label_eq}</p>
                            <p style="font-size: 1.4rem; font-weight: 700; margin: 5px 0 0 0; color: #4e73df;">₹{fmt_curr_eq}</p>
                        </div>
                        <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.02); border: 1px solid rgba(78,115,223,0.1); padding: 15px; border-radius: 12px;">
                            <p style="font-size: 0.75rem; color: #858796; margin: 0; text-transform: uppercase;">Total Equity P&L</p>
                            <div style="display: flex; align-items: baseline; gap: 8px; margin-top: 5px;">
                                <span style="font-size: 1.4rem; font-weight: 700;" class="{eq_pnl_class}">₹{fmt_pnl_eq}</span>
                                <span style="font-size: 0.85rem; font-weight: 600; background: rgba(0,0,0,0.05); padding: 2px 8px; border-radius: 10px;" class="{eq_pnl_class}">{total_pnl_pct:+.2f}%</span>
                            </div>
                        </div>
                    </div>
                    """

                    st.markdown(equity_html, unsafe_allow_html=True)

                    # --- ADD THIS BEFORE SECTORAL ANALYSIS IN TAB 1 ---
                    st.markdown("### 📋 Detailed Equity Holdings")

                    # 1. Prepare and Clean Data
                    df_holdings = df_eq.copy()
                    df_holdings = df_holdings[['tradingsymbol', 'quantity', 'average_price', 'last_price', 'invested_value', 'current_value']]

                    # Calculations
                    df_holdings['P&L'] = df_holdings['current_value'] - df_holdings['invested_value']
                    df_holdings['P&L %'] = (df_holdings['P&L'] / df_holdings['invested_value']) * 100
                    df_holdings['Weight %'] = (df_holdings['current_value'] / df_holdings['current_value'].sum()) * 100

                    # Sort by highest current value
                    df_holdings = df_holdings.sort_values(by='current_value', ascending=False).reset_index(drop=True)

                    # 2. Rename columns for display
                    rename_map = {
                        'tradingsymbol': 'Stock', 'quantity': 'Qty', 'average_price': 'Avg Price',
                        'last_price': 'LTP', 'invested_value': 'Invested', 'current_value': 'Current',
                        'P&L': 'P&L', 'P&L %': 'P&L %', 'Weight %': 'Weight %'
                    }
                    df_display = df_holdings.rename(columns=rename_map)

                    # 3. Create formatting lambdas for 0 decimals and 2 decimals
                    # format_indian_currency is the function we created earlier
                    fmt_0d = lambda x: f"₹{ut.format_indian_currency(x).split('.')[0]}"
                    fmt_2d = lambda x: f"₹{ut.format_indian_currency(x)}"
                    fmt_qty = lambda x: ut.format_indian_currency(x).split('.')[0] # No ₹ for quantity

                    # 4. Create the Styled Object
                    styled_final = df_display.style.applymap(ut.color_values, subset=['P&L', 'P&L %']) \
                        .format({
                            'Qty': fmt_qty,
                            'Avg Price': fmt_2d,
                            'LTP': fmt_2d,
                            'Invested': fmt_0d,
                            'Current': fmt_0d,
                            'P&L': fmt_0d,
                            'P&L %': '{:+.2f}%',
                            'Weight %': '{:.1f}%'
                        })

                    # 6. Render
                    html = ut.apply_holdings_style(styled_final).hide(axis='index').to_html()
                    st.markdown(html, unsafe_allow_html=True)
                    st.write("<br>", unsafe_allow_html=True)

                    #Sector-wise Allocation sunburnt chart
                    st.markdown("### 🏭 Sectoral Exposure & Summary")

                    with st.spinner("Analyzing Sectoral Weights..."):
                        # 1. Fetch Sector Info and Build Data
                        sector_map = ut.get_sector_info(df_eq['tradingsymbol'].tolist())
                        df_sector_full = df_eq.copy()
                        df_sector_full['Sector'] = df_sector_full['tradingsymbol'].map(sector_map)
                        
                        # Pre-calculate formatted strings for Sunburst hover (0 decimals)
                        df_sector_full['fmt_current_val'] = df_sector_full['current_value'].apply(
                            lambda x: ut.format_indian_currency(x).split('.')[0]
                        )

                        # Aggregate Summary
                        df_sector_summary = df_sector_full.groupby('Sector').agg({
                            'invested_value': 'sum',
                            'current_value': 'sum'
                        }).reset_index()
                        
                        df_sector_summary['P&L'] = df_sector_summary['current_value'] - df_sector_summary['invested_value']
                        df_sector_summary['Weight %'] = (df_sector_summary['current_value'] / df_sector_summary['current_value'].sum()) * 100
                        df_sector_summary = df_sector_summary.sort_values(by='current_value', ascending=False)

                        # UI Layout
                        col_chart, col_table = st.columns([1.2, 1])

                        with col_chart:
                            # 1. Create a dictionary that maps BOTH Sector names and Stock names to their Indian-formatted values
                            # This ensures Plotly has a value for every 'label' it encounters in the sunburst path
                            sector_totals = df_sector_full.groupby('Sector')['current_value'].sum().to_dict()
                            stock_values = df_sector_full.set_index('tradingsymbol')['current_value'].to_dict()

                            # Merge them into one lookup dictionary
                            all_label_values = {**sector_totals, **stock_values}

                            # 2. Create the custom data list based on the actual path used in the chart
                            # We need to format the values to 0 decimals for the inner labels
                            df_sector_full['fmt_val_0d'] = df_sector_full['current_value'].apply(lambda x: ut.format_indian_currency(x).split('.')[0])

                            fig_sect = px.sunburst(
                                df_sector_full, 
                                path=['Sector', 'tradingsymbol'], 
                                values='current_value',
                                height=450,
                                color='Sector',
                                color_discrete_sequence=px.colors.qualitative.Prism
                            )

                            # 3. Use a Lambda/Function in update_traces to pull from our mapped totals
                            # This replaces the '?' by manually providing the text for each slice
                            formatted_labels = []
                            for i, row in df_sector_full.iterrows():
                                # Plotly's sunburst can be tricky with customdata on hierarchies. 
                                # A more robust way is to set 'text' directly.
                                pass

                            # Easiest Fix: Update the traces to use the 'value' but override the formatting
                            fig_sect.update_traces(
                                # Internal text: label name + the value formatted with commas and 0 decimals
                                texttemplate="<b>%{label}</b><br>₹%{value:,.0f}",
                                
                                # Hover text: Now uses %{value} to match the internal calculation
                                hovertemplate="<b>%{label}</b><br>Value: ₹%{value:,.0f}<extra></extra>",
                                
                                textinfo="label+value",
                                insidetextorientation='radial'
                            )
                            
                            fig_sect.update_layout(
                                margin=dict(t=0, l=0, r=0, b=0),
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                extendsunburstcolors=True,
                                # IMPORTANT: This tells Plotly to use Indian grouping style (commas)
                                # It changes the decimal and thousand separators globally for this chart
                                separators='.,' 
                            )
                            st.plotly_chart(fig_sect, use_container_width=True)

                        with col_table:
                            df_clean = df_sector_summary.reset_index(drop=True)
                            df_clean.columns = [col.replace('_', ' ').title() for col in df_clean.columns]

                            # Define the Indian Numbering Lambda with 0 Decimals
                            fmt_indian_0d = lambda x: f"₹{ut.format_indian_currency(x).split('.')[0]}"

                            # Apply Professional Styling and Formatting
                            styled_sector = df_clean.style.applymap(ut.color_pnl_custom, subset=['P&L']) \
                                .format({
                                    'Invested Value': fmt_indian_0d,
                                    'Current Value': fmt_indian_0d,
                                    'P&L': fmt_indian_0d,
                                    'Weight %': '{:.0f}%' # Zero decimals for weight as requested
                                })

                            st.markdown("#### Sector Breakdown")
                            html_sector = ut.apply_sector_style(styled_sector).hide(axis='index').to_html()
                            st.markdown(html_sector, unsafe_allow_html=True)

                    # --- STEP D: HISTORICAL PERFORMANCE & FUNDAMENTALS ---
                    st.write("<br>", unsafe_allow_html=True)
                    st.markdown("### 🛰️ Stock Deep Scan")

                    # 1. Selection Header (Full width for stock selection)
                    stock_list = sorted(df_eq['tradingsymbol'].unique().tolist())
                    selected_stock = st.selectbox("Select stock to analyze:", stock_list, key="stock_selector_main")

                    # 2. Fetch Data from yFinance
                    yf_symbol = f"{selected_stock}.NS"
                    ticker_obj = yf.Ticker(yf_symbol)

                    with st.spinner(f"Analyzing {selected_stock}..."):
                        info = ticker_obj.info

                        # 2. Fetch all data points
                        # (Existing data preparation logic remains the same)
                        sector = info.get('sector', 'N/A')
                        raw_mcap_cr = info.get('marketCap', 0) / 10**7
                        mcap_val = f"₹{ut.format_indian_currency(raw_mcap_cr).split('.')[0]} Cr"
                        pe_val = f"{info.get('trailingPE', 0):.2f}"
                        pb_val = f"{info.get('priceToBook', 0):.2f}"
                        roe_val = f"{info.get('returnOnEquity', 0) * 100:.2f}%"
                        npm_val = f"{info.get('profitMargins', 0) * 100:.2f}%"
                        de_val = f"{info.get('debtToEquity', 0)/100:.2f}"
                        div_val = f"{info.get('dividendYield', 0) :.2f}%"

                        # 3. Create Row 1
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("SECTOR", sector)
                        col2.metric("MARKET CAP", mcap_val)
                        col3.metric("P/E RATIO", pe_val)
                        col4.metric("P/B RATIO", pb_val)

                        # 4. Create Row 2
                        col5, col6, col7, col8 = st.columns(4)
                        col5.metric("ROE", roe_val)
                        col6.metric("PROFIT MARGIN", npm_val)
                        col7.metric("DEBT TO EQUITY", de_val)
                        col8.metric("DIV. YIELD", div_val)

                        st.write("<br>", unsafe_allow_html=True)
                        # --- NEW: TIME PERIOD TOGGLE (Between Fundamentals and Chart) ---

                        # --- 2. DISPLAY BELOW CHART ---
                        st.markdown("### 📈 Historical Price Analysis")
                        time_period = st.radio(
                            "Select Timeframe:",
                            options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
                            index=3, # Default to '1y'
                            horizontal=True,
                            key="stock_time_toggle"
                        )

                        # --- 6. Historical Chart Logic ---
                        hist_data = yf.download(yf_symbol, period=time_period, interval="1d", progress=False, auto_adjust=True)

                        if not hist_data.empty:
                            if isinstance(hist_data.columns, pd.MultiIndex):
                                hist_data.columns = hist_data.columns.get_level_values(0)
                            
                            # --- CALCULATE RETURNS ---
                            start_price = float(hist_data['Close'].iloc[0])
                            end_price = float(hist_data['Close'].iloc[-1])
                            abs_return = ((end_price - start_price) / start_price) * 100
                            
                            days = (hist_data.index[-1] - hist_data.index[0]).days
                            years = days / 365.25
                            
                            if years >= 1:
                                cagr = ((end_price / start_price) ** (1 / years) - 1) * 100
                                return_text = f"{abs_return:+.2f}% Abs | {cagr:.2f}% CAGR"
                            else:
                                return_text = f"{abs_return:+.2f}% Abs Return"

                            perf_color = "#22c55e" if abs_return >= 0 else "#ef4444"
                            avg_buy = float(df_eq[df_eq['tradingsymbol'] == selected_stock]['average_price'].iloc[0])
                            
                            line_color = "#22c55e" if end_price >= avg_buy else "#ef4444"
                            fill_color = "rgba(34, 197, 94, 0.1)" if end_price >= avg_buy else "rgba(239, 68, 68, 0.1)"

                            # --- UPDATED MODERN HEADER ---
                            # Using a professional font-weight and separating the name from the return
                            chart_title = (
                                f"<span style='font-size:22px; font-weight:700; color:white;'>{selected_stock}</span> "
                                f"<span style='font-size:14px; color:#858796;'> Historical Price</span><br>"
                                f"<span style='font-size:18px; font-weight:500; color:{perf_color};'>{return_text} ({time_period.upper()})</span>"
                            )

                            fig_hist = px.area(hist_data, y='Close', title=chart_title, template="plotly_dark")
                            
                            # Styling
                            fig_hist.update_traces(
                                line_color=line_color, line_width=2.5, fillcolor=fill_color,
                                hovertemplate="<b>Date:</b> %{x}<br><b>Price:</b> ₹%{y:,.2f}<extra></extra>"
                            )

                            fig_hist.add_hline(
                                y=avg_buy, line_dash="dot", line_color="#f6c23e", line_width=1.5,
                                annotation_text=f"Your Avg: ₹{avg_buy:,.2f}", 
                                annotation_position="bottom right",
                                annotation_font=dict(color="#f6c23e")
                            )

                            fig_hist.update_layout(
                                hovermode="x unified",
                                # FIX: Increased top margin (t=80) so the header isn't cut off
                                margin=dict(t=80, l=10, r=40, b=10), 
                                height=500,
                                paper_bgcolor='rgba(0,0,0,0)', 
                                plot_bgcolor='rgba(0,0,0,0)',
                                xaxis=dict(showgrid=False, title="", tickfont=dict(color="#858796")),
                                yaxis=dict(
                                    showgrid=True, 
                                    gridcolor="rgba(255,255,255,0.05)", 
                                    title=None, 
                                    side="right", 
                                    tickfont=dict(color="#858796"),
                                    tickprefix="₹",
                                    zeroline=False
                                ),
                                # Ensures the title is positioned properly within the margin
                                title_x=0.01,
                                title_y=0.92
                            )

                            st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})

                            st.write("<br>", unsafe_allow_html=True)

                        # --- 1. CALCULATIONS ---
                        # RSI (Relative Strength Index)
                        rsi_io = RSIIndicator(close=hist_data['Close'], window=14)
                        hist_data['RSI'] = rsi_io.rsi()

                        # Moving Averages
                        sma20_io = SMAIndicator(close=hist_data['Close'], window=20)
                        hist_data['SMA20'] = sma20_io.sma_indicator()

                        sma50_io = SMAIndicator(close=hist_data['Close'], window=50)
                        hist_data['SMA50'] = sma50_io.sma_indicator()

                        # Get latest values for the display
                        current_price = hist_data['Close'].iloc[-1]
                        current_rsi = hist_data['RSI'].iloc[-1]
                        val_sma20 = hist_data['SMA20'].iloc[-1]
                        val_sma50 = hist_data['SMA50'].iloc[-1]

                        # --- 2. DISPLAY BELOW CHART ---
                        st.markdown("### ⚡ Technical Momentum")
                        t_col1, t_col2, t_col3, t_col4 = st.columns(4)

                        with t_col1:
                            # Set the status and color based on the RSI value
                            if current_rsi > 70:
                                rsi_label = "Overbought"
                                rsi_delta = f"- {rsi_label}" # Red Up Arrow
                                rsi_col = "normal"
                            elif current_rsi < 30:
                                rsi_label = "Oversold"
                                rsi_delta = f"+ {rsi_label}" # Green Down Arrow
                                rsi_col = "normal"
                            else:
                                rsi_label = "Neutral"
                                rsi_delta = f"{rsi_label}" # No arrow, just text
                                rsi_col = "off" # Gray color for neutral
                            
                            st.metric(
                                label="RSI (14)", 
                                value=f"{current_rsi:.1f}", 
                                delta=f"{rsi_delta}", 
                                delta_color=rsi_col
                            )

                        with t_col2:
                            dist_sma20 = ((current_price - val_sma20) / val_sma20) * 100
                            st.metric("20 Day SMA", f"₹{val_sma20:,.2f}", delta=f"{dist_sma20:+.1f}% vs Price")

                        with t_col3:
                            is_bullish = current_price > val_sma20
                            # --- THE FIX ---
                            # Instead of just text, we provide a value that Streamlit MUST treat as negative
                            # We use a formatted string that starts with the minus sign
                            status_text = "Bullish" if is_bullish else "Bearish"
                            delta_label = f"{'+' if is_bullish else '-'} Below SMA20" if not is_bullish else "Above SMA20"
                            
                            st.metric(
                                label="Trend (Short-term)", 
                                value=status_text, 
                                delta=delta_label,
                                delta_color="normal" # 'normal' + '-' sign = RED; 'normal' + '+' sign = GREEN
                            )

                        with t_col4:
                            day_change = ((current_price - hist_data['Close'].iloc[-2]) / hist_data['Close'].iloc[-2]) * 100
                            st.metric("Daily Momentum", f"₹{current_price:,.2f}", delta=f"{day_change:+.2f}%")
  

                    # --- STEP E: FINANCIAL GROWTH (REVENUE vs PROFIT TOGGLE) ---

                    st.write("<br>", unsafe_allow_html=True)

                    # 1. CSS for the Boxed Card, Custom Tabs, and Pill Toggle
                    st.markdown("""
                    <style>
                        /* Main card housing with border */
                        .stElementContainer:has(div.financial-card) {
                            border: 1px solid #e6e9ef;
                            border-radius: 12px;
                            padding: 20px;
                            background-color: white;
                        }
                        
                        /* REMOVE default gray line under the tab list */
                        [data-testid="stBaseButton-tablist"] {
                            border-bottom: none !important;
                            gap: 30px;
                        }

                        /* Style for Revenue/Profit Tabs */
                        [data-testid="stBaseButton-tab"] {
                            color: #7d8592 !important;
                            font-weight: 600 !important;
                            padding-bottom: 10px !important;
                        }
                        [data-testid="stBaseButton-tab"][aria-selected="true"] {
                            color: #00b18d !important;
                            border-bottom: 3px solid #00b18d !important;
                        }

                        /* Pill-Shaped Toggle for Quarterly/Yearly */
                        div[data-testid="stSegmentedControl"] {
                            background-color: #f1f8f6; /* Very light teal background */
                            border-radius: 30px;
                            padding: 4px;
                            width: fit-content;
                        }
                        div[data-testid="stSegmentedControl"] button {
                            border: none !important;
                            border-radius: 25px !important;
                            background-color: transparent !important;
                            color: #7d8592 !important;
                        }
                        div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
                            background-color: white !important; /* White pill on light background */
                            color: #00b18d !important;
                            font-weight: bold !important;
                            box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
                        }
                    </style>
                    """, unsafe_allow_html=True)

                    # 3. Main Dashboard Section
                    st.markdown("### 🚀 Financial Growth Analysis")

                    # Use columns to keep the box to half the page width
                    col_chart, col_spacer = st.columns([1.1, 0.9])

                    with col_chart:
                        # Main card container
                        with st.container(border=True): 
                            # Metric selection tabs
                            tab_revenue, tab_profit = st.tabs(["Revenue", "Profit"])
                            
                            metrics = {"Revenue": "Total Revenue", "Profit": "Net Income"}
                            
                            for tab, label in zip([tab_revenue, tab_profit], ["Revenue", "Profit"]):
                                with tab:
                                    # Layout containers
                                    chart_area = st.container()
                                    footer_container = st.container()
                                    
                                    # Bottom Row: Pill-shaped toggle
                                    with footer_container:
                                        view_choice = st.segmented_control(
                                            f"toggle_{label}",
                                            options=["Quarterly", "Yearly"],
                                            default="Yearly",
                                            label_visibility="collapsed"
                                        )

                                    # Data Logic and Visualization
                                    with chart_area:
                                        data_key = metrics[label]
                                        source_df = ticker_obj.financials if view_choice == "Yearly" else ticker_obj.quarterly_financials
                                        
                                        if not source_df.empty and data_key in source_df.index:
                                            # 1. Data Cleaning and Chronology
                                            df = source_df.loc[data_key].dropna().head(5).reset_index()
                                            df.columns = ['Label', 'Value']
                                            df['Label'] = df['Label'].dt.strftime('%Y' if view_choice == "Yearly" else '%b %y')
                                            
                                            if view_choice == "Yearly": 
                                                df = df.sort_values('Label')
                                            else: 
                                                df = df.iloc[::-1]
                                            
                                            # 2. Indian Numbering Logic
                                            # Scale to Crores
                                            df['Value_Cr'] = df['Value'] / 10**7 
                                            
                                            # Pre-format Indian currency string with 0 decimals
                                            df['fmt_val'] = df['Value_Cr'].apply(
                                                lambda x: f"₹{ut.format_indian_currency(x).split('.')[0]} Cr"
                                            )
                                            
                                            # 3. Create Bar Chart
                                            fig = px.bar(
                                                df, 
                                                x='Label', 
                                                y='Value_Cr',
                                                custom_data=['fmt_val'] # Attach Indian string to the bars
                                            )
                                            
                                            # 4. Apply Your Custom Styling Function
                                            # IMPORTANT: We do this BEFORE the trace update to avoid overrides
                                            styled_fig = ut.style_financial_chart(fig, df['Value_Cr'])
                                            
                                            # 5. Force Indian Labels (Override Everything Else)
                                            styled_fig.update_traces(
                                                # Uses the customdata string: e.g., ₹1,72,985 Cr
                                                texttemplate="<b>%{customdata[0]}</b>",
                                                textposition="outside",
                                                # Syncs hover tooltip to use the same format
                                                hovertemplate="<b>%{x}</b><br>Amount: %{customdata[0]}<extra></extra>",
                                                marker_color='#00b18d'
                                            )
                                            
                                            # 6. Final Layout Polish
                                            styled_fig.update_layout(
                                                separators='.,', # Proper Indian comma/dot placement
                                                margin=dict(t=50, b=10, l=10, r=10), # Extra top room for the ₹ labels
                                                yaxis_tickformat=None, # Prevents auto-scaling on the side axis
                                            )
                                            
                                            st.plotly_chart(styled_fig, use_container_width=True, config={'displayModeBar': False})
                                        else:
                                            st.info(f"{view_choice} {label.lower()} data not available.")

                else:
                    st.info("No Equity holdings found.")

            with tab2:
                if not df_mf.empty:
                    # Calculations for Tab 2 (already simulated in Step A)
                    df_mf['pnl'] = df_mf['current_value'] - df_mf['invested_value']
                    df_mf['pnl_pct'] = (df_mf['pnl'] / df_mf['invested_value']) * 100
                    df_mf = df_mf.sort_values(by='current_value', ascending=False).reset_index(drop=True)
                    df_mf.index = df_mf.index + 1
                    
                    # --- MUTUAL FUND CALCULATIONS ---
                    total_inv_mf = df_mf['invested_value'].sum()
                    current_val_mf = df_mf['current_value'].sum()
                    total_pnl_mf = current_val_mf - total_inv_mf
                    total_pnl_pct_mf = (total_pnl_mf / total_inv_mf) * 100 if total_inv_mf != 0 else 0

                    # --- PREPARE INDIAN FORMATTED STRINGS ---
                    # Reusing the format_indian_currency function defined earlier
                    fmt_inv_mf = ut.format_indian_currency(total_inv_mf)
                    fmt_curr_mf = ut.format_indian_currency(current_val_mf)
                    fmt_pnl_mf = ut.format_indian_currency(total_pnl_mf)

                    # 1. Prepare dynamic variables
                    mf_pnl_class = "pnl-positive" if total_pnl_mf >= 0 else "pnl-negative"
                    mf_sim_glow = "border: 1px solid #f6c23e;" if simulation_pct != 0 else "border: 1px solid rgba(78,115,223,0.1);"
                    mf_curr_label = "Current Value" if simulation_pct == 0 else f"Simulated ({simulation_pct:+.0f}%)"

                    # 2. Use dedent to strip leading whitespace from the string
                    mf_summary_html = textwrap.dedent(f"""
                        <div style="display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; width: 100%;">
                            <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.02); border: 1px solid rgba(78,115,223,0.1); padding: 15px; border-radius: 12px;">
                                <p style="font-size: 0.75rem; color: #858796; margin: 0; text-transform: uppercase;">MF Investment</p>
                                <p style="font-size: 1.4rem; font-weight: 700; margin: 5px 0 0 0;">₹{fmt_inv_mf}</p>
                            </div>
                            <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.02); {mf_sim_glow} padding: 15px; border-radius: 12px;">
                                <p style="font-size: 0.75rem; color: #858796; margin: 0; text-transform: uppercase;">{mf_curr_label}</p>
                                <p style="font-size: 1.4rem; font-weight: 700; margin: 5px 0 0 0; color: #4e73df;">₹{fmt_curr_mf}</p>
                            </div>
                            <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.02); border: 1px solid rgba(78,115,223,0.1); padding: 15px; border-radius: 12px;">
                                <p style="font-size: 0.75rem; color: #858796; margin: 0; text-transform: uppercase;">MF P&L</p>
                                <div style="display: flex; align-items: baseline; gap: 8px; margin-top: 5px;">
                                    <span style="font-size: 1.4rem; font-weight: 700;" class="{mf_pnl_class}">₹{fmt_pnl_mf}</span>
                                    <span style="font-size: 0.85rem; font-weight: 600; background: rgba(0,0,0,0.05); padding: 2px 8px; border-radius: 10px;" class="{mf_pnl_class}">{total_pnl_pct_mf:+.2f}%</span>
                                </div>
                            </div>
                        </div>
                    """).strip()

                    # 3. Render
                    st.markdown(mf_summary_html, unsafe_allow_html=True)

                    st.markdown("### 📜 Detailed Mutual Fund Holdings")

                    # 1. Prepare Data
                    disp_mf = df_mf[['fund', 'quantity', 'average_price', 'invested_value', 'last_price', 'current_value', 'pnl', 'pnl_pct']].copy()
                    disp_mf.columns = ['Fund Name', 'Units', 'Avg. NAV', 'Invested', 'Current NAV', 'Current Value', 'P&L', 'P&L %']

                    # --- Define Indian Numbering Formatters ---
                    # Formatter for 2 decimals (Units, Avg. NAV, Current NAV)
                    fmt_indian_2d = lambda x: f"₹{ut.format_indian_currency(x)}" if isinstance(x, (int, float)) else x
                    fmt_units_2d = lambda x: f"{ut.format_indian_currency(x)}" if isinstance(x, (int, float)) else x

                    # Formatter for 0 decimals (Invested, Current Value, P&L)
                    fmt_indian_0d = lambda x: f"₹{ut.format_indian_currency(x).split('.')[0]}" if isinstance(x, (int, float)) else x
                    # 3. Create the Styled Object
                    styled_mf = disp_mf.style.applymap(ut.color_pnl_custom, subset=['P&L', 'P&L %']) \
                        .format({
                            'Units': fmt_units_2d,          # 2 decimals Indian format
                            'Avg. NAV': fmt_indian_2d,     # 2 decimals Indian format
                            'Current NAV': fmt_indian_2d, # 2 decimals Indian format
                            'Invested': fmt_indian_0d,      # 0 decimals Indian format
                            'Current Value': fmt_indian_0d, # 0 decimals Indian format
                            'P&L': fmt_indian_0d,           # 0 decimals Indian format
                            'P&L %': '{:+.2f}%'             # Standard % formatting
                        })

                    # 5. Render to HTML
                    html_mf = ut.apply_mf_style(styled_mf).hide(axis='index').to_html()
                    st.markdown(html_mf, unsafe_allow_html=True)
                    st.write("<br>", unsafe_allow_html=True)
                    
                    
                    # --- Beautified NAV Performance Logic ---
                    st.markdown("### 📈 Historical NAV Performance")

                    available_funds = list(MY_FUNDS.keys())
                    selected_fund_name = st.selectbox("Select Fund to view History:", available_funds, key="mf_history_selector")
                    scheme_code = MY_FUNDS[selected_fund_name]

                    # 1. NEW: Add the Period Selector above the chart
                    # This variable 'time_range' is what makes the CAGR dynamic
                    time_range = st.radio(
                        "Select Range:", 
                        ["6M", "1Y", "3Y", "5Y", "MAX"], 
                        horizontal=True, 
                        key="nav_range_selector")

                    with st.spinner(f"Fetching NAV history..."):
                        try:
                            url = f"https://api.mfapi.in/mf/{scheme_code}"
                            response = requests.get(url)
                            data_json = response.json()

                            if "data" in data_json and len(data_json["data"]) > 0:
                                df_nav = pd.DataFrame(data_json["data"])
                                df_nav['nav'] = pd.to_numeric(df_nav['nav'])
                                df_nav['date'] = pd.to_datetime(df_nav['date'], dayfirst=True)
                                df_nav = df_nav.sort_values('date')

                                # 2. NEW: Filter the dataframe based on the radio button choice
                                end_date = df_nav['date'].max()
                                if time_range == "6M":
                                    start_date = end_date - pd.DateOffset(months=6)
                                elif time_range == "1Y":
                                    start_date = end_date - pd.DateOffset(years=1)
                                elif time_range == "3Y":
                                    start_date = end_date - pd.DateOffset(years=3)
                                elif time_range == "5Y":
                                    start_date = end_date - pd.DateOffset(years=5)
                                else:
                                    start_date = df_nav['date'].min()

                                # Filter the data
                                df_filtered = df_nav[df_nav['date'] >= start_date].copy()

                                # 3. NEW: Calculate returns based ONLY on the filtered data
                                start_val = df_filtered['nav'].iloc[0]
                                end_val = df_filtered['nav'].iloc[-1]
                                
                                abs_return = ((end_val - start_val) / start_val) * 100
                                
                                # Calculate years for CAGR
                                days_diff = (df_filtered['date'].iloc[-1] - df_filtered['date'].iloc[0]).days
                                years_diff = days_diff / 365.25
                                
                                if years_diff >= 1:
                                    cagr = ((end_val / start_val) ** (1 / years_diff) - 1) * 100
                                    return_html = f"<span style='color:#22c55e;'>Abs: {abs_return:+.2f}% | CAGR: {cagr:.2f}%</span>"
                                else:
                                    return_html = f"<span style='color:#22c55e;'>Abs Return: {abs_return:+.2f}%</span>"

                                # 4. Create Area Chart using df_filtered
                                fig_nav = px.area(
                                    df_filtered, 
                                    x='date', 
                                    y='nav',
                                    title=f"<b>{selected_fund_name}</b><br>{return_html}",
                                    template="plotly_dark"
                                )

                                # 5. Styling (Note: I removed the rangeselector buttons from here)
                                fig_nav.update_traces(
                                    line_color='#4e73df',
                                    line_width=2,
                                    fillcolor='rgba(78, 115, 223, 0.1)',
                                    hovertemplate="<b>Date:</b> %{x}<br><b>NAV:</b> ₹%{y:.2f}<extra></extra>"
                                )

                                fig_nav.update_layout(
                                    hovermode="x unified",
                                    margin=dict(t=100, l=0, r=0, b=0),
                                    height=450,
                                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="", side="right"),
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)',
                                )

                                st.plotly_chart(fig_nav, use_container_width=True)
                                
                            else:
                                st.warning("No historical data found.")
                        except Exception as e:
                            st.error(f"Error: {e}")

                else:
                    st.info("No Mutual Fund holdings found.")
            
            with tab3:
                if mf_sips:
                    df_sip = pd.DataFrame(mf_sips)
                    df_sip['instalment_day'] = pd.to_numeric(df_sip['instalment_day'])
                    active_sips = df_sip[df_sip['status'] == 'ACTIVE'].copy()
                    
                    # 1. Calculations
                    total_sip_monthly = active_sips['instalment_amount'].sum()
                    active_count = len(active_sips)
                    today_day = datetime.now().day
                    formatted_full_date = datetime.now().strftime("%d %b %Y")
                    
                    # Calculate Outflow Progress
                    remaining_cash = active_sips[active_sips['instalment_day'] >= today_day]['instalment_amount'].sum()
                    paid_so_far = total_sip_monthly - remaining_cash
                    progress_pct = float(paid_so_far / total_sip_monthly) if total_sip_monthly > 0 else 0.0

                    # 2. Glass Card Summary Ribbon
                    sip_summary_html = f"""
            <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.03); border: 1px solid rgba(78,115,223,0.15); padding: 18px; border-radius: 15px;">
                    <p style="font-size: 0.8rem; color: #858796; margin: 0; text-transform: uppercase; letter-spacing: 1px;">Monthly Commitment</p>
                    <p style="font-size: 1.5rem; font-weight: 700; margin: 5px 0 0 0; color: #4e73df;">₹{total_sip_monthly:,.0f}</p>
                </div>
                <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.03); border: 1px solid rgba(78,115,223,0.15); padding: 18px; border-radius: 15px;">
                    <p style="font-size: 0.8rem; color: #858796; margin: 0; text-transform: uppercase; letter-spacing: 1px;">Active Mandates</p>
                    <p style="font-size: 1.5rem; font-weight: 700; margin: 5px 0 0 0; color: #4e73df;">{active_count} <span style="font-size: 0.8rem; font-weight: 400; color: #1cc88a;">● Running</span></p>
                </div>
                <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.03); border: 1px solid rgba(231,74,59,0.15); padding: 18px; border-radius: 15px;">
                    <p style="font-size: 0.8rem; color: #e74a3b; margin: 0; text-transform: uppercase; letter-spacing: 1px;">Upcoming Outflow</p>
                    <p style="font-size: 1.5rem; font-weight: 700; margin: 5px 0 0 0;">₹{remaining_cash:,.0f}</p>
                </div>
            </div>
            """
                    st.markdown(sip_summary_html, unsafe_allow_html=True)

                    # 3. Visual Cash-Flow Progress Bar (FIXED FORMATTING)
                    st.write(f"**Monthly Outflow Progress: {progress_pct:.0%} complete**")
                    st.progress(progress_pct)
                    st.caption(f"📅 Today: **{formatted_full_date}** | Invested: **₹{paid_so_far:,.0f}** | Remaining: **₹{remaining_cash:,.0f}**")
                    
                    st.write("<br>", unsafe_allow_html=True)

                    # --- 7-Day Lookahead with Next Instalment Date ---
                    # 1. Ensure 'next_instalment' is in datetime format
                    active_sips['next_instalment'] = pd.to_datetime(active_sips['next_instalment'], errors='coerce')

                    # 2. Filter for dates within the next 7 days from today
                    today_dt = datetime.now()
                    next_week_dt = today_dt + timedelta(days=7)

                    upcoming_7_days = active_sips[
                        (active_sips['next_instalment'] >= today_dt) & 
                        (active_sips['next_instalment'] <= next_week_dt)
                    ].copy()

                    if not upcoming_7_days.empty:
                        # Sort by the actual date
                        upcoming_7_days = upcoming_7_days.sort_values('next_instalment')
                        
                        # Create the columns first
                        u_col1, u_col2 = st.columns([1, 2.5])

                        with u_col1:
                            st.markdown("#### 🔔 Attention: Upcoming SIPs")
                            
                            total_due = upcoming_7_days['instalment_amount'].sum()
                            
                            # Custom CSS to style the metric box border to match the table
                            st.markdown(
                                f"""
                                <style>
                                    div[data-testid="stMetric"] {{
                                        background-color: #ffffff;
                                        border: 2px solid #99f6e4; /* Matches table border color */
                                        padding: 15px;
                                        border-radius: 10px;
                                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                                    }}
                                </style>
                                """,
                                unsafe_allow_html=True
                            )

                            st.metric(
                                label="Liquidity Needed", 
                                value=f"₹{total_due:,.0f}",
                                help="Total amount due in the next 7 days"
                            )
                            st.caption("Please ensure sufficient bank balance.")

                        with u_col2:
                            # 2. Header for the table also INSIDE the column
                            st.markdown("#### 📅 Upcoming SIPs (Next 7 Days)")

                            # Prepare Data
                            disp_upcoming = upcoming_7_days[['fund', 'instalment_amount', 'next_instalment']].copy()
                            disp_upcoming.columns = ['Fund Name', 'Amount', 'Due Date']

                            # Format columns
                            styled_upcoming = disp_upcoming.style.format({
                                'Amount': '₹{:,.0f}',
                                'Due Date': lambda x: x.strftime('%d %b %Y') if hasattr(x, 'strftime') else str(x)
                            })

                            # Render Table
                            html_upcoming = ut.apply_upcoming_style(styled_upcoming).hide(axis='index').to_html()
                            st.markdown(html_upcoming, unsafe_allow_html=True)
                    else:
                        st.info("✨ Your cash flow looks clear for the next 7 days. No SIPs due.")
                    
                    st.write("<br>", unsafe_allow_html=True)    

                    # 1. Clean and Prepare Data
                    # Sorting by instalment_day if available, then resetting index
                    disp_sip = df_sip.sort_values(by='instalment_day').reset_index(drop=True)
                    disp_sip = disp_sip[['fund', 'status', 'instalment_amount', 'next_instalment']].copy()
                    disp_sip.columns = ['Fund Name', 'Status', 'Amount', 'Next Date']

                    # 3. Create Styled Object
                    # We format Amount as whole numbers and clean the Date format
                    styled_sip_full = disp_sip.style.applymap(ut.color_status_all, subset=['Status']) \
                        .format({
                            'Amount': '₹{:,.0f}',
                            'Next Date': lambda x: x.strftime('%d %b %Y') if hasattr(x, 'strftime') else str(x)
                        })

                    # 5. Render
                    st.markdown("### ⏱️ Complete SIP Schedule")
                    html_sip_full = ut.apply_sip_full_style(styled_sip_full).hide(axis='index').to_html()
                    st.markdown(html_sip_full, unsafe_allow_html=True)
                else:
                    st.info("No Mutual Fund SIPs found.")

        else:
            st.error("Request token not found in URL.")
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please complete the sidebar configuration and login to view your dashboard.")