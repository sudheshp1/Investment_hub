import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import utils as ut
from styles import apply_custom_css
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD

# --- 1. INITIALIZE SESSION STATE ---
if 'confirmed' not in st.session_state:
    st.session_state.confirmed = False
if 'last_selected_symbol' not in st.session_state:
    st.session_state.last_selected_symbol = ""
if 'last_selected_index' not in st.session_state:
    st.session_state.last_selected_index = ""
if 'scan_active' not in st.session_state:
    st.session_state.scan_active = False 

# Must be the first streamlit command
st.set_page_config(page_title="Stock Screener", page_icon="🔍", layout="wide")
apply_custom_css()

# --- TITLE & BENCHMARKS ---
st.markdown('<h1 class="main-title">🔍 Market Opportunities Screener</h1>', unsafe_allow_html=True)
ut.show_live_benchmarks()

# --- SELECTION BAR ---
# Adjusted ratios to prevent the index selector from stretching too wide on Cloud
col_idx, _ = st.columns([1.5, 3.5])
with col_idx:
    st.markdown('<p style="font-weight: 600; font-size: 1.1rem; margin-bottom: 5px;">📂 1. Choose Target Index</p>', unsafe_allow_html=True)
    index_choice = st.selectbox(
        "Index", 
        ["NIFTY 50", "NIFTY NEXT 50"], 
        label_visibility="collapsed",
        key="main_index_choice"
    )

stock_mapping = ut.get_index_tickers(index_choice)

# --- STOCK SELECTION FORM ---
with st.form("stock_selection_form"):
    # KEY FIX: vertical_alignment="bottom" ensures the button and selectbox share the same baseline
    col_stock, col_btn = st.columns([2, 1], vertical_alignment="bottom")
    
    with col_stock:
        st.markdown('<p style="font-weight: 600; font-size: 1.1rem; margin-bottom: 5px;">🎯 2. Select Company</p>', unsafe_allow_html=True)
        selected_symbol = st.selectbox(
            "Company",
            options=list(stock_mapping.keys()), 
            format_func=lambda sym: f"{stock_mapping[sym]}",
            label_visibility="collapsed"
        )
    
    with col_btn:
        # Removed the hacky <div> spacer and replaced with native vertical alignment
        confirm_btn = st.form_submit_button("✅ Confirm Selection", use_container_width=True)

# --- ACTION LOGIC ---
if confirm_btn:
    st.session_state.confirmed = True
    st.session_state.last_selected_symbol = selected_symbol
    st.session_state.last_selected_index = index_choice
    st.session_state.scan_active = False 

st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

# --- FOCUS AREA (THE ANALYSIS CARD & DETAILS) ---
if st.session_state.confirmed:
    curr_sym = st.session_state.last_selected_symbol
    curr_idx = st.session_state.last_selected_index
    
    if curr_sym in stock_mapping:
        company_name = stock_mapping[curr_sym]
        ticker = yf.Ticker(f"{curr_sym}.NS")
        
        # Fetch Data
        try:
            fast_info = ticker.fast_info
            live_price = fast_info.last_price
            prev_close = fast_info.previous_close
            pct_change = ((live_price - prev_close) / prev_close) * 100
            price_color = "#1cc88a" if pct_change >= 0 else "#e74a3b"
            arrow = "▲" if pct_change >= 0 else "▼"
        except:
            live_price, pct_change, price_color, arrow = 0.0, 0.0, "#858796", ""

        # 1. Main Teal Analysis Card
        st.markdown(f"""
            <div style="text-align: center; background: linear-gradient(135deg, rgba(54, 185, 204, 0.05) 0%, rgba(255, 255, 255, 0.9) 100%);
                padding: 30px 20px; border-radius: 15px; border: 1px solid rgba(54, 185, 204, 0.2); width: 80%; margin: auto;">
                <p style="text-transform: uppercase; letter-spacing: 2px; color: #258391; font-weight: 700; font-size: 0.7rem; margin-bottom: 15px;">Market Analysis Focus</p>
                <div style="display: flex; justify-content: center; align-items: baseline; gap: 15px; margin-bottom: 15px;">
                    <h2 style="margin:0; font-weight: 800; color: #1a202c; font-size: 2rem;">{company_name}</h2>
                    <span style="font-size: 1.8rem; font-weight: 400; color: #1a202c;">₹{live_price:,.2f}</span>
                    <span style="font-size: 1.1rem; font-weight: 700; color: {price_color};">{arrow} {abs(pct_change):.2f}%</span>
                </div>
                <div style="display: inline-block; padding: 5px 20px; background: #36b9cc; border-radius: 50px;">
                    <span style="color: white; font-weight: 700; font-size: 0.85rem;">{curr_sym} | {curr_idx}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 2. Position the Button directly below the text but inside the flow
        st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True) # Adjust spacing
        _, btn_col, _ = st.columns([1, 1.5, 1])
        with btn_col:
            if st.button("🚀 Initialize Deep Scan", use_container_width=True, type="primary"):
                st.session_state.scan_active = True # This triggers the tabs below

        # 3. Conditional Tabs: Only show if scan_active is True
        if st.session_state.scan_active:
        # 2. Detailed Research Tabs
            st.markdown("### 🔍 Detailed Research")
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance", "📑 Fundamentals", "⚙️ Technicals", "🎯 Recommendation"])

            with tab1:
                st.subheader("📈 Historical Price Analysis")
                
                # 1. Create columns for Timeframe and Metrics
                tf_col, abs_ret_col, cagr_col = st.columns([2, 1, 1])
                
                with tf_col:
                    timeframe = st.radio(
                        "Select Timeframe:",
                        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
                        index=3, 
                        horizontal=True,
                        key="tf_selector" # Unique key to prevent state conflicts
                    )
                
                # Fetch data based on timeframe
                hist = ticker.history(period=timeframe)
                
                if not hist.empty:
                    # --- 2. PERFORMANCE CALCULATIONS ---
                    start_price = hist['Close'].iloc[0]
                    end_price = hist['Close'].iloc[-1]
                    
                    # Absolute Return
                    abs_return = ((end_price - start_price) / start_price) * 100
                    
                    # CAGR Calculation
                    # Calculate number of years between start and end date
                    days = (hist.index[-1] - hist.index[0]).days
                    years = days / 365.25
                    
                    if years > 0:
                        # CAGR Formula: [(End/Start)^(1/Years) - 1] * 100
                        cagr = (((end_price / start_price) ** (1 / years)) - 1) * 100
                    else:
                        cagr = 0.0

                    # --- 3. DISPLAY METRICS ---
                    with abs_ret_col:
                        st.metric("Absolute Return", f"{abs_return:.2f}%")
                    
                    with cagr_col:
                        # Show CAGR only if period is 1 year or more, else show N/A
                        if timeframe in ["1mo", "3mo", "6mo"]:
                            st.metric("CAGR", "N/A", help="CAGR is typically for 1Y+ periods")
                        else:
                            st.metric("CAGR", f"{cagr:.2f}%")

                    # --- 4. RENDER CHART ---
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hist.index, 
                        y=hist['Close'], 
                        name="Close", 
                        line=dict(color='#36b9cc', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(54, 185, 204, 0.1)'
                    ))
                    
                    fig.update_layout(
                        template="plotly_white", 
                        height=450, 
                        margin=dict(l=60, r=20, t=10, b=50), # Adjusted left margin for Y-axis labels
                        xaxis_title="Date", 
                        yaxis_title="Price (₹)",
                        hovermode="x unified",
                        yaxis=dict(
                            autorange=True,
                            fixedrange=False,
                            zeroline=False,
                            tickformat=',.0f' # Added comma formatting for thousands
                        ),
                        xaxis=dict(showgrid=False)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"No historical data found for '{timeframe}'.")

            with tab2:
                st.subheader("🧮 Key Financial Metrics")
                info = ticker.info
    
                # --- 1. Top-Level Metrics (4 Column Layout) ---
                col1, col2, col3, col4 = st.columns(4)

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
                
                # Column 1: Valuation
                #col1.metric("Market Cap", ut.format_val(info.get('marketCap'), prefix="₹", suffix=" Cr", decimals=0, is_crore=True))
                # Calculation: Divide by 10^7 to get raw Crores
                mcap_raw = info.get('marketCap', 0) / 10**7

                # Formatting: Apply Indian grouping and strip decimals
                mcap_formatted = f"₹{ut.format_indian_currency(mcap_raw).split('.')[0]} Cr"

                # Display
                col1.metric("Market Cap", mcap_formatted)
                col1.metric("P/E Ratio", ut.format_val(info.get('trailingPE')))
                col1.metric("PEG Ratio", ut.format_val(info.get('pegRatio')))

                # Column 2: Price Performance
                col2.metric("52W High", ut.format_val(info.get('fiftyTwoWeekHigh'), prefix="₹"))
                col2.metric("52W Low", ut.format_val(info.get('fiftyTwoWeekLow'), prefix="₹"))
                col2.metric("Price to Book", ut.format_val(info.get('priceToBook')))

                # Column 3: Profitability
                col3.metric("ROE (%)", ut.format_val(info.get('returnOnEquity', 0) * 100, suffix="%"))
                # ROCE proxy using ROA if direct ROCE is unavailable in info
                col3.metric("ROCE/ROA (%)", ut.format_val(info.get('returnOnAssets', 0) * 100, suffix="%"))
                col3.metric("Div. Yield", ut.format_val(info.get('dividendYield', 0), suffix="%"))

                # Column 4: Health & Earnings
                col4.metric("Trailing EPS", ut.format_val(info.get('trailingEps'), prefix="₹"))
                # debtToEquity is often returned as a percentage-base (e.g. 40.0 for 0.4)
                d_e_raw = info.get('debtToEquity')
                d_e_val = d_e_raw / 100 if isinstance(d_e_raw, (int, float)) else None
                col4.metric("Debt to Equity", ut.format_val(d_e_val))

                #st.markdown("---")
                
                # 2. View Toggle
                view_col, _ = st.columns([1, 2])
                with view_col:
                    finance_view = st.radio("Financial View:", ["Annual", "Quarterly"], horizontal=True, key="fin_view_extended")

                st.subheader(f"📊 {finance_view} Performance & Growth")

                try:
                    df_fin = ticker.financials if finance_view == "Annual" else ticker.quarterly_financials

                    if not df_fin.empty:
                        # 3. Data Selection & Calculation
                        target_rows = ['Total Revenue', 'Gross Profit', 'EBITDA', 'Operating Income', 'Net Income']
                        available_rows = [r for r in target_rows if r in df_fin.index]
                        
                        financial_table = df_fin.loc[available_rows].iloc[:, :5].copy()
                        
                        # Growth Calculations (keep as raw numbers for now)
                        rev_series = financial_table.loc['Total Revenue']
                        rev_growth = ((rev_series - rev_series.shift(-1)) / rev_series.shift(-1)) * 100
                        
                        prof_series = financial_table.loc['Net Income']
                        prof_growth = ((prof_series - prof_series.shift(-1)) / prof_series.shift(-1)) * 100
                        
                        # Convert financial values to Crores
                        financial_table = financial_table / 10**7
                        
                        # 4. Define Labels & Build Final Table
                        g_suffix = "YOY" if finance_view == "Annual" else "QOQ"
                        rev_g_label = f"{g_suffix} Revenue Growth (%)"
                        prof_g_label = f"{g_suffix} Profit Growth (%)"
                        
                        financial_table.loc[rev_g_label] = rev_growth
                        financial_table.loc[prof_g_label] = prof_growth
                        
                        new_order = [
                            'Total Revenue', rev_g_label, 
                            'Gross Profit', 'EBITDA', 'Operating Income', 
                            'Net Income', prof_g_label
                        ]
                        final_order = [r for r in new_order if r in financial_table.index]
                        final_table = financial_table.loc[final_order].iloc[:, :4]
                        
                        rename_map = {
                            'Total Revenue': 'Revenue (Cr)', 
                            'Gross Profit': 'Gross Profit (Cr)',
                            'EBITDA': 'EBITDA (Cr)',
                            'Operating Income': 'Operating Profit (Cr)',
                            'Net Income': 'Net Profit (Cr)'
                        }
                        final_table.rename(index=rename_map, inplace=True)
                        final_table.columns = [col.strftime('%Y' if finance_view == "Annual" else '%b %y') for col in final_table.columns]

                        def format_fin_table(val, row_name):
                            # 1. Handle Nulls, NaNs, or missing data
                            if pd.isna(val) or val is None:
                                return "N/A"
                            
                            # 2. Format Growth Percentages
                            if "Growth (%)" in row_name:
                                # Check for +nan% specifically as seen in your image
                                if np.isinf(val): return "N/A"
                                return f"{val:+.2f}%"
                            
                            # 3. Format Currency Rows with Indian Numbering
                            try:
                                # Apply Indian grouping and remove decimals for Crore values
                                formatted_val = ut.format_indian_currency(val).split('.')[0]
                                return f"₹{formatted_val}"
                            except:
                                return "N/A"

                        # Apply custom formatting across the dataframe rows
                        styled_df = final_table.apply(lambda x: [format_fin_table(v, x.name) for v in x], axis=1, result_type='expand')

                        # Maintain original column and index names after apply
                        styled_df.columns = final_table.columns
                        styled_df.index = final_table.index

                        # Render full width table using HTML
                        html = ut.apply_custom_style(styled_df.style).to_html()
                        st.markdown(html, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.caption(f"All figures are in ₹ Crores and rounded to the nearest whole number. Data sourced from Yahoo Finance.")
                    else:
                        st.info(f"No {finance_view.lower()} data available.")
                        
                except Exception as e:
                    st.error(f"Error rendering financial table: {e}")

            with tab3:
                st.subheader("⚡ Technical Analysis Indicators")
                
                # 1. Fetch historical data (2 year needed for SMA 200)
                hist_data = ticker.history(period="2y")

                if not hist_data.empty:
                    try:
                        # 2. CALCULATIONS
                        # RSI
                        rsi_io = RSIIndicator(close=hist_data['Close'], window=14)
                        hist_data['RSI'] = rsi_io.rsi()

                        # MACD
                        macd_io = MACD(close=hist_data['Close'])
                        curr_macd = macd_io.macd().iloc[-1]
                        curr_signal = macd_io.macd_signal().iloc[-1]

                        # Moving Averages: 20, 50, and 200
                        sma20_io = SMAIndicator(close=hist_data['Close'], window=20)
                        hist_data['SMA20'] = sma20_io.sma_indicator()

                        sma50_io = SMAIndicator(close=hist_data['Close'], window=50)
                        hist_data['SMA50'] = sma50_io.sma_indicator()

                        sma200_io = SMAIndicator(close=hist_data['Close'], window=200)
                        hist_data['SMA200'] = sma200_io.sma_indicator()

                        # Get latest values for the display
                        current_price = hist_data['Close'].iloc[-1]
                        current_rsi = hist_data['RSI'].iloc[-1]
                        val_sma20 = hist_data['SMA20'].iloc[-1]
                        val_sma50 = hist_data['SMA50'].iloc[-1]
                        val_sma200 = hist_data['SMA200'].iloc[-1]
                        beta = ticker.info.get('beta', 'N/A')

                        # --- ROW 1: Momentum & Risk (3 Columns) ---
                        r1_col1, r1_col2, r1_col3 = st.columns(3)

                        with r1_col1:
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

                        with r1_col2:
                            # Beta
                            if isinstance(beta, (int, float)):
                                beta_label = "High Volatility" if beta > 1.2 else "Low Volatility" if beta < 0.8 else "Market Linked"
                                beta_delta_label = f"+ {beta_label}" if beta > 1.2 else f"- {beta_label}" if beta < 0.8 else f"{beta_label}"
                                st.metric(label="Beta (Risk)", value=f"{beta:.2f}", delta=beta_delta_label, delta_color="normal")
                            else:
                                st.metric(label="Beta (Risk)", value="N/A")

                        with r1_col3:
                            # --- FINAL MACD COLOR & ARROW FIX ---
                            is_bullish = curr_macd > curr_signal
                            macd_label = "Bullish Cross" if is_bullish else "Bearish Cross"
                            
                            # Using +/- at the start forces Streamlit to show ONE arrow.
                            # We use 'normal' color because Streamlit understands:
                            # (+) with 'normal' = Green Up Arrow
                            # (-) with 'normal' = Red Down Arrow
                            macd_delta_val = f"+ {macd_label}" if is_bullish else f"- {macd_label}"

                            st.metric(
                                label="MACD (12,26)", 
                                value=f"{curr_macd:.2f}", 
                                delta=macd_delta_val, 
                                delta_color="normal" 
                            )

                        st.write("") # Spacer

                        # --- ROW 2: Trend / SMAs (3 Columns) ---
                        r2_col1, r2_col2, r2_col3 = st.columns(3)

                        with r2_col1:
                            dist_20 = ((current_price - val_sma20) / val_sma20) * 100
                            st.metric(label="20 Day SMA", value=f"₹{val_sma20:,.2f}", 
                                    delta=f"{dist_20:+.1f}% vs Price")

                        with r2_col2:
                            dist_50 = ((current_price - val_sma50) / val_sma50) * 100
                            st.metric(label="50 Day SMA", value=f"₹{val_sma50:,.2f}", 
                                    delta=f"{dist_50:+.1f}% vs Price")

                        with r2_col3:
                            if not pd.isna(val_sma200):
                                dist_200 = ((current_price - val_sma200) / val_sma200) * 100
                                st.metric(label="200 Day SMA", value=f"₹{val_sma200:,.2f}", 
                                        delta=f"{dist_200:+.1f}% vs Price")
                            else:
                                st.metric("200 Day SMA", "N/A", delta="Insufficient Data")

                        st.write("<br>", unsafe_allow_html=True)
                        # --- 5. INTERACTIVE TECHNICAL CHART ---
                        st.write("#### 📈 Price vs Moving Averages (Last 200 Days)")
                        
                        try:

                            # Filter data to the last 200 days for clarity
                            plot_data = hist_data.tail(200)

                            fig = go.Figure()

                            # Add Closing Price
                            fig.add_trace(go.Scatter(
                                x=plot_data.index, y=plot_data['Close'],
                                mode='lines', name='Close Price',
                                line=dict(color='#1f77b4', width=2)
                            ))

                            # Add SMA 20
                            fig.add_trace(go.Scatter(
                                x=plot_data.index, y=plot_data['SMA20'],
                                mode='lines', name='20 SMA',
                                line=dict(color='#ff7f0e', width=1.5, dash='dot')
                            ))

                            # Add SMA 50
                            fig.add_trace(go.Scatter(
                                x=plot_data.index, y=plot_data['SMA50'],
                                mode='lines', name='50 SMA',
                                line=dict(color='#2ca02c', width=1.5, dash='dash')
                            ))

                            # Add SMA 200
                            fig.add_trace(go.Scatter(
                                x=plot_data.index, y=plot_data['SMA200'],
                                mode='lines', name='200 SMA',
                                line=dict(color='#d62728', width=2)
                            ))

                            # Update Layout for a professional look
                            fig.update_layout(
                            template="plotly_white",
                            height=500,
                            margin=dict(l=20, r=20, t=20, b=20),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            hovermode="x unified",
                            # X-Axis settings: Grid removed
                            xaxis=dict(
                                showgrid=False, 
                                showline=True, 
                                linecolor='black',
                                linewidth=1
                            ),
                            # Y-Axis settings: Grid removed
                            yaxis=dict(
                                showgrid=False, 
                                showline=True, 
                                linecolor='black',
                                linewidth=1,
                                tickprefix="₹"
                            )
                        )

                            st.plotly_chart(fig, use_container_width=True)

                        except Exception as chart_err:
                            st.error(f"Could not render chart: {chart_err}")

                    except Exception as e:
                        st.error(f"Error calculating technicals: {e}")
                else:
                    st.warning("No historical data available for this ticker.")

            with tab4:
                st.subheader("🧭 Investment Recommendation Engine")
                info = ticker.info
                # 1. Fetch historical data (2 year needed for SMA 200)
                hist_data = ticker.history(period="2y")
                
                # RSI
                rsi_io = RSIIndicator(close=hist_data['Close'], window=14)
                hist_data['RSI'] = rsi_io.rsi()

                # Moving Averages: 20, 50, and 200
                sma20_io = SMAIndicator(close=hist_data['Close'], window=20)
                hist_data['SMA20'] = sma20_io.sma_indicator()

                sma50_io = SMAIndicator(close=hist_data['Close'], window=50)
                hist_data['SMA50'] = sma50_io.sma_indicator()

                sma200_io = SMAIndicator(close=hist_data['Close'], window=200)
                hist_data['SMA200'] = sma200_io.sma_indicator()
                
                # Calculate scores
                pros, cons, total_score = ut.analyze_stock(ticker.info, hist_data)
                max_score = 17
                
                # 1. Logic to define the label and theme keys
                if total_score >= 13:
                    rec_text, theme_key = "STRONG BUY", "STRONG BUY"
                elif total_score >= 9:
                    rec_text, theme_key = "BUY", "BUY"
                elif total_score >= 5:
                    rec_text, theme_key = "HOLD", "HOLD"
                else:
                    rec_text, theme_key = "SELL / AVOID", "SELL / AVOID"

                # 2. Refined Aesthetic Theme Map
                theme_map = {
                    "STRONG BUY": ("#E7F4E8", "#1E4620", "#2E7D32"),    # Greens
                    "BUY": ("#F1F8E9", "#33691E", "#558B2F"),           # Light Greens
                    "HOLD": ("#FFF3E0", "#E65100", "#EF6C00"),          # Oranges
                    "SELL / AVOID": ("#FFEBEE", "#B71C1C", "#C62828")   # Reds
                }

                bg, border, text = theme_map.get(theme_key)

                # 3. Smaller, Aesthetic HTML Card
                st.markdown(f"""
                    <div style="
                        background: linear-gradient(to right, {bg}, #ffffff, {bg});
                        border: 1px solid {border};
                        padding: 15px 30px;
                        border-radius: 20px;
                        text-align: center;
                        max-width: 600px;
                        margin: 20px auto;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                    ">
                        <h2 style="
                            color: {text};
                            margin: 0;
                            font-size: 1.8rem;
                            font-weight: 700;
                            letter-spacing: 1.5px;
                            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                        ">
                            {rec_text}
                        </h2>
                        <p style="
                            color: {text};
                            margin: 5px 0 0 0;
                            font-size: 0.9rem;
                            font-weight: 500;
                            opacity: 0.8;
                        ">
                            Score: {total_score} / 17 ({(total_score/17)*100:.1f}%)
                        </p>
                    </div>
                """, unsafe_allow_html=True)

                st.write("<br>", unsafe_allow_html=True)

                # Create columns with a specified gap
                p_col, spacer, c_col = st.columns([1, 0.1, 1]) 

                with p_col:
                    st.markdown("### ✅ Strengths (Pros)")
                    if pros:
                        for p in pros: 
                            st.success(p)
                    else:
                        st.info("No significant strengths identified based on current metrics.")

                # The 'spacer' column creates the visual gap you requested

                with c_col:
                    st.markdown("### ⚠️ Weaknesses (Cons)")
                    if cons:
                        for c in cons: 
                            st.error(c)
                    else:
                        st.info("No significant weaknesses identified based on current metrics.")
    else:
        st.info("Selection changed. Please click 'Confirm Selection' to refresh.")
else:

    st.info("Please select an index and stock, then click 'Confirm Selection'.")
