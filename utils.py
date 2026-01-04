import streamlit as st
import yfinance as yf
import pandas as pd
from kiteconnect import KiteConnect
from urllib.parse import urlparse, parse_qs
from ta.trend import MACD

@st.fragment(run_every=10)
def show_live_benchmarks():
    st.markdown("### 🏛️ Market Watch (Live)")
    indices = {
        "Nifty 50": "^NSEI", 
        "Nifty Next 50": "^NSMIDCP", 
        "Nifty Midcap 150": "NIFTYMIDCAP150.NS"
    }
    
    symbols = list(indices.values())
    data = yf.download(symbols, period="1d", interval="1m", progress=False, auto_adjust=True)
    
    cols = st.columns(len(indices))
    
    for i, (name, symbol) in enumerate(indices.items()):
        with cols[i]:
            try:
                # Handle both Single and Multi-index DataFrames from yfinance
                if isinstance(data['Close'], pd.DataFrame):
                    prices = data['Close'][symbol].dropna()
                else:
                    prices = data['Close'].dropna()
                
                current_price = prices.iloc[-1]
                prev_close = prices.iloc[0]
                
                change = current_price - prev_close
                pct_change = (change / prev_close) * 100
                
                st.metric(
                    label=name,
                    value=f"{current_price:,.2f}",
                    delta=f"{change:+.2f} ({pct_change:+.2f}%)"
                )
            except Exception:
                st.error(f"Error loading {name}")

def handle_kite_auth():
    """Renders the Kite Configuration UI. Call this ONLY on Dashboard."""
    api_key = "e53bh9l0p0haf9wl"
    api_secret = "4k4ft0rn9xb23dxeqt9nsb6gtonrsg3z"
    
    # Initialize session state for persistent login
    if "kite" not in st.session_state:
        st.session_state.kite = None
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    with st.sidebar:
        st.header("⚙️ Configurations")
        
        if st.session_state.authenticated:
            st.success("✅ Kite Connected")
            if st.button("Log Out"):
                st.session_state.authenticated = False
                st.session_state.kite = None
                st.rerun()
        else:
            kite_obj = KiteConnect(api_key=api_key)
            st.write("1. Authorize App:")
            if st.button("🚀 Get Login URL"):
                st.link_button("Login to Kite", kite_obj.login_url())
            
            redirect_url = st.text_input("2. Paste Redirect URL here:")
            if redirect_url:
                try:
                    parsed_url = urlparse(redirect_url)
                    request_token = parse_qs(parsed_url.query).get("request_token", [None])[0]
                    if request_token:
                        data = kite_obj.generate_session(request_token, api_secret=api_secret)
                        kite_obj.set_access_token(data["access_token"])
                        st.session_state.kite = kite_obj
                        st.session_state.authenticated = True
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

def handle_what_if_sidebar():
    """Renders the What-If Analysis UI. Call this on Dashboard and/or Screener."""
    with st.sidebar:
        st.divider()
        st.markdown("### 🧪 What-If Analysis")
        
        if 'sim_val' not in st.session_state:
            st.session_state.sim_val = 0

        if st.button("🔄 Reset to 0%"):
            st.session_state.sim_val = 0
            st.rerun()

        simulation_pct = st.slider(
            "Simulate Market Change (%)",
            min_value=-50, max_value=50, step=1,
            key="sim_val"
        )
        
        if simulation_pct != 0:
            st.warning(f"Simulating a {simulation_pct}% {'gain' if simulation_pct > 0 else 'drop'}")
        
        return simulation_pct

def get_index_tickers(index_name):
    urls = {
        "NIFTY 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
        "NIFTY NEXT 50": "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
        "NIFTY BANK": "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv",
        "NIFTY MIDCAP 150": "https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv"
    }
    
    try:
        url = urls.get(index_name)
        headers = {'User-Agent': 'Mozilla/5.0'}
        df = pd.read_csv(url)
        
        # --- CLEANING STEP ---
        # 1. Remove specific known dummy symbols
        blacklist = ["DUMMYHDLVR"]
        df = df[~df['Symbol'].isin(blacklist)]
        
        # 2. General filter: Remove anything starting with or containing 'DUMMY'
        df = df[~df['Symbol'].str.contains('DUMMY', case=False, na=False)]
        
        # Create a dictionary { 'RELIANCE': 'Reliance Industries Ltd.', ... }
        # Note: NSE CSV column name for Company Name is usually 'Company Name'
        stock_dict = dict(zip(df['Symbol'], df['Company Name']))
        
        return stock_dict
        
    except Exception as e:
        st.error(f"Error fetching {index_name} list: {e}")
        return []
    
def analyze_stock(info, hist_data):
    pros = []
    cons = []
    score = 0
    
    # 1. VALUATION METRICS
    pe = info.get('forwardPE')
    if pe:
        if pe < 25:
            pros.append(f"Low Forward PE ({pe:.1f}): Stock appears undervalued.")
            score += 2
        elif pe > 45:
            cons.append(f"High Forward PE ({pe:.1f}): Stock is trading at a premium.")
    
    book_value = info.get('bookValue')
    current_price = info.get('currentPrice', 0)
    if book_value and current_price:
        pb_ratio = current_price / book_value
        if pb_ratio < 5:
            pros.append(f"Low P/B Ratio ({pb_ratio:.2f}): Trading close to book value.")
            score += 1
        elif pb_ratio > 10:
            cons.append(f"High P/B Ratio ({pb_ratio:.2f}): Price is much higher than asset value.")

    # 2. PROFITABILITY & RISK
    roe = info.get('returnOnEquity')
    if roe:
        if roe > 0.15:
            pros.append(f"Strong ROE ({roe*100:.1f}%): Efficiently generating profit.")
            score += 2
        else:
            cons.append(f"Weak ROE ({roe*100:.1f}%): Lower than ideal profitability.")
            
    # 1. ROCE Analysis (New)
    roce = info.get('returnOnAssets') 
    
    # Benchmark: > 15% is generally considered good
    if roce and roce > 0.12:
        pros.append(f"Strong Capital Efficiency: Efficiently generating returns on all capital employed.")
        score += 2
    elif roce and roce < 0.05:
        cons.append(f"Poor Capital Efficiency: Low returns on invested capital.")
            
    # 1. DEBT TO EQUITY RATIO (New)
    # Standard benchmark: < 1 is healthy, > 2 is risky
    de_ratio = info.get('debtToEquity') 
    if de_ratio is not None:
        # Note: yfinance often returns D/E as a percentage (e.g., 50.0 for 0.5)
        # We normalize it here if it's > 5 to assume it's a percentage
        norm_de = de_ratio / 100
        
        if norm_de < 1.0:
            pros.append(f"Low Debt-to-Equity ({norm_de:.2f}): Strong balance sheet with low leverage.")
            score += 1
        elif norm_de > 2.0:
            cons.append(f"High Debt-to-Equity ({norm_de:.2f}): High financial leverage; potentially risky.")
        else:
            # Neutral case - no points added, but no con listed
            pass
            
    # 1. DIVIDEND YIELD (New)
    div_yield = info.get('dividendYield')
    if div_yield and div_yield > 2:
        # Benchmark: > 2% is generally considered attractive for floor support
        pros.append(f"Dividend Support (Yield: {div_yield:.1f}%): Provides a valuation floor for conservative investors.")
        score += 1

    # 3. TECHNICAL MOMENTUM
    rsi = hist_data['RSI'].iloc[-1]
    if rsi < 35:
        pros.append(f"RSI Oversold ({rsi:.1f}): Potential for price reversal upwards.")
        score += 2
    elif rsi > 70:
        cons.append(f"RSI Overbought ({rsi:.1f}): Stock may be due for a correction.")

    curr_price = hist_data['Close'].iloc[-1]
    sma200 = hist_data['SMA50'].iloc[-1]
    sma50 = hist_data['SMA200'].iloc[-1]
    if not pd.isna(sma200):
        if curr_price > sma200:
            pros.append("Above 200 SMA: Long-term trend is bullish.")
            score += 2
        else:
            cons.append("Below 200 SMA: Long-term trend is bearish.")

    # 1. TREND: GOLDEN CROSS SETUP (New)
    if curr_price > sma50 > sma200:
        pros.append("Golden Cross Setup: Price > SMA50 > SMA200 indicating a strong structural uptrend.")
        score += 2
    elif curr_price < sma50 < sma200:
        cons.append("Death Cross Setup: Price < SMA50 < SMA200 indicating a structural downtrend.")
        
    # 2. 52-WEEK HIGH DISTANCE (New)
    high_52w = info.get('fiftyTwoWeekHigh')
    if high_52w:
        dist_from_high = ((high_52w - curr_price) / high_52w) * 100
        if dist_from_high <= 10:
            pros.append(f"Relative Strength: Trading within {dist_from_high:.1f}% of 52-week high.")
            score += 1
        elif dist_from_high >= 40:
            cons.append(f"Falling Knife Alert: Down {dist_from_high:.1f}% from 52-week high; high downward momentum.")
            
    # 4. MACD Signal
    # MACD
    macd_io = MACD(close=hist_data['Close'])
    curr_macd = macd_io.macd().iloc[-1]
    curr_signal = macd_io.macd_signal().iloc[-1]
    if curr_macd > curr_signal:
        pros.append("MACD Bullish Cross: Short-term momentum is positive.")
        score += 1
    else:
        cons.append("MACD Bearish Cross: Short-term momentum is slowing.")

    return pros, cons, score

# --- OPTIMIZED SECTOR FETCHING (Add this outside your main loop) ---
@st.cache_data(ttl=86400) # Cache for 24 hours
def get_sector_info(symbols):
    data = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            data[symbol] = ticker.info.get('sector', 'Others')
        except:
            data[symbol] = "Others"
    return data

# 3. Helper Function for P&L Coloring
def color_values(val):
    if isinstance(val, (int, float)):
        color = '#22c55e' if val >= 0 else '#ef4444' # Green for positive, Red for negative
        return f'color: {color}; font-weight: bold;'
    return ''

# 5. Define CSS for the HTML Table
def apply_holdings_style(styler):
    styler.set_table_styles([
        {'selector': '', 'props': [('width', '100%'), ('table-layout', 'fixed'), ('border-collapse', 'collapse')]},
        {'selector': 'th', 'props': [
            ('background-color', '#f0f2f6'), ('color', '#1f77b4'), ('font-weight', 'bold'), 
            ('text-align', 'center'), ('padding', '10px'), ('font-size', '14px'), ('border-bottom', '2px solid #e6e9ef')
        ]},
        {'selector': 'td', 'props': [
            ('padding', '8px'), ('border-bottom', '1px solid #e6e9ef'), ('text-align', 'center'),
            ('font-size', '14px'), ('font-weight', '500')
        ]},
        {'selector': 'td:first-child', 'props': [
            ('text-align', 'left'), ('font-weight', 'bold'), ('color', '#1f77b4'), ('padding-left', '15px')
        ]},
        {'selector': 'th:first-child', 'props': [('text-align', 'left'), ('padding-left', '15px')]},
        {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#fafafa')]}
    ])
    return styler

# 2. Helper Function for P&L Coloring
def color_pnl_custom(val):
    if isinstance(val, (int, float)):
        # Positive Green, Negative Red
        color = '#22c55e' if val >= 0 else '#ef4444'
        return f'color: {color}; font-weight: bold;'
    return ''

# 4. Define Table CSS (Subtle Slate/Charcoal Header)
def apply_sector_style(styler):
    styler.set_table_styles([
        # Table Layout
        {'selector': '', 'props': [
            ('width', '100%'), 
            ('table-layout', 'fixed'), 
            ('border-collapse', 'collapse')
        ]},
        # Header Styling (Subtle Slate Gray)
        {'selector': 'th', 'props': [
            ('background-color', '#475569'), # Slate Gray
            ('color', 'white'), 
            ('font-weight', '600'), 
            ('text-align', 'center'), 
            ('padding', '10px'),
            ('font-size', '13px')
        ]},
        # Cell Styling
        {'selector': 'td', 'props': [
            ('padding', '8px'), 
            ('border-bottom', '1px solid #e2e8f0'), 
            ('text-align', 'center'),
            ('font-size', '13px')
        ]},
        # First Column (Sector Names) - Left Aligned
        {'selector': 'td:first-child', 'props': [
            ('text-align', 'left'), 
            ('font-weight', 'bold'), 
            ('color', '#334155'),
            ('padding-left', '12px')
        ]},
        {'selector': 'th:first-child', 'props': [('text-align', 'left'), ('padding-left', '12px')]},
        # Alternating Row Colors
        {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f8fafc')]}
    ])
    return styler

# 4. Apply the Equity Holdings Style with Single-Line Row Adjustment
def apply_mf_style(styler):
    styler.set_table_styles([
        {'selector': '', 'props': [
            ('width', '100%'), 
            ('table-layout', 'fixed'), 
            ('border-collapse', 'collapse')
        ]},
        # Header Styling
        {'selector': 'th', 'props': [
            ('background-color', '#f0f2f6'), 
            ('color', '#1f77b4'), 
            ('font-weight', 'bold'), 
            ('text-align', 'center'), 
            ('padding', '8px 4px'), 
            ('font-size', '14px'), 
            ('border-bottom', '2px solid #e6e9ef')
        ]},
        # Default Cell Styling
        {'selector': 'td', 'props': [
            ('padding', '6px 4px'), 
            ('border-bottom', '1px solid #e6e9ef'), 
            ('text-align', 'center'),
            ('font-size', '14px'), 
            ('font-weight', '500'),
            ('white-space', 'nowrap'), 
            ('overflow', 'hidden'), 
            ('text-overflow', 'ellipsis')
        ]},
        # Specific Adjustment for Fund Name Column (Blue Color)
        {'selector': 'td:first-child', 'props': [
            ('text-align', 'left'), 
            ('font-weight', 'bold'), 
            ('color', '#1f77b4'), # This sets the Blue color
            ('padding-left', '15px'),
            ('width', '30%')
        ]},
        # Header for Fund Name (Alignment)
        {'selector': 'th:first-child', 'props': [
            ('text-align', 'left'), 
            ('padding-left', '15px'),
            ('width', '35%')
        ]},
        # Set uniform width for all numeric columns
        {'selector': 'td:not(:first-child), th:not(:first-child)', 'props': [
            ('width', '10%') 
        ]},
        {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#fafafa')]}
        ])
    return styler

def apply_upcoming_style(styler):
    styler.set_table_styles([
        # Table Container: Added border-bottom to create the final closing line
        {'selector': '', 'props': [
            ('width', '100%'), 
            ('table-layout', 'fixed'), 
            ('border-collapse', 'collapse'),
            ('border-bottom', '2px solid #99f6e4') # The missing bottom border
        ]},
        # Header Styling
        {'selector': 'th', 'props': [
            ('background-color', '#f0fdfa'), 
            ('color', '#0f766e'), 
            ('font-weight', 'bold'), 
            ('text-align', 'center'), 
            ('padding', '8px 4px'), 
            ('font-size', '14px'), 
            ('border-bottom', '2px solid #99f6e4')
        ]},
        # Cell Styling
        {'selector': 'td', 'props': [
            ('padding', '6px 4px'), 
            ('border-bottom', '1px solid #f0fdfa'), 
            ('text-align', 'center'),
            ('font-size', '14px'), 
            ('font-weight', '500'), 
            ('white-space', 'nowrap'),
            ('overflow', 'hidden'), 
            ('text-overflow', 'ellipsis')
        ]},
        # First Column (Fund Name)
        {'selector': 'td:first-child', 'props': [
            ('text-align', 'left'), 
            ('font-weight', 'bold'), 
            ('color', '#0f766e'), 
            ('padding-left', '15px'), 
            ('width', '55%')
        ]},
        {'selector': 'th:first-child', 'props': [
            ('text-align', 'left'), 
            ('padding-left', '15px'), 
            ('width', '50%')
        ]},
        # Numeric Columns
        {'selector': 'td:not(:first-child), th:not(:first-child)', 'props': [
            ('width', '25%')
        ]},
        # Alternating Row Colors
        {'selector': 'tr:nth-child(even)', 'props': [
            ('background-color', '#f9fafb')
        ]}
    ])
    return styler

# 2. Helper Function for Status Coloring
def color_status_all(val):
    if str(val).upper() == 'ACTIVE':
        return 'color: #16a34a; font-weight: bold;' # Green
    elif str(val).upper() == 'PAUSED':
        return 'color: #d97706; font-weight: bold;' # Orange
    return ''

# 4. Define Table CSS (Slate/Charcoal Theme)
def apply_sip_full_style(styler):
    styler.set_table_styles([
        {'selector': '', 'props': [
            ('width', '100%'), 
            ('table-layout', 'fixed'), 
            ('border-collapse', 'collapse'),
            ('border-bottom', '2px solid #475569') # Solid floor border
        ]},
        # Header Styling (Slate Gray)
        {'selector': 'th', 'props': [
            ('background-color', '#475569'), 
            ('color', 'white'), 
            ('font-weight', 'bold'), 
            ('text-align', 'center'), 
            ('padding', '10px 4px'), 
            ('font-size', '14px'),
            ('border-bottom', '2px solid #334155')
        ]},
        # Cell Styling
        {'selector': 'td', 'props': [
            ('padding', '8px 4px'), 
            ('border-bottom', '1px solid #e2e8f0'), 
            ('text-align', 'center'),
            ('font-size', '14px'), 
            ('font-weight', 'bold'),
            ('white-space', 'nowrap'),
            ('overflow', 'hidden'), 
            ('text-overflow', 'ellipsis')
        ]},
        # Fund Name Column (Slate Text & Wide)
        {'selector': 'td:first-child', 'props': [
            ('text-align', 'left'), 
            ('font-weight', 'bold'), 
            ('color', '#334155'), 
            ('padding-left', '15px'),
            ('width', '40%') 
        ]},
        {'selector': 'th:first-child', 'props': [('text-align', 'left'), ('padding-left', '15px'), ('width', '45%')]},
        # Uniform widths for remaining columns
        {'selector': 'td:not(:first-child), th:not(:first-child)', 'props': [('width', '18.3%')]},
        {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f8fafc')]}
    ])
    return styler

# 5. Formatting Logic
def format_values(row):
    formatted = []
    for x in row:
        if pd.isnull(x): formatted.append("N/A")
        elif "Growth" in row.name: formatted.append(f"{x:.2f}%")
        else: formatted.append(f"₹{int(round(x, 0)):,}")
    return pd.Series(formatted, index=row.index)

# --- Helper Function for Null Handling ---
def format_val(val, prefix="", suffix="", decimals=2, is_crore=False):
    if val is None or (isinstance(val, float) and pd.isna(val)) or val == 0:
        # Check for 0 specifically for metrics where 0 is effectively missing data
        return "N/A"
    
    processed_val = val / 10**7 if is_crore else val
    
    if isinstance(processed_val, (int, float)):
        if decimals == 0:
            return f"{prefix}{int(round(processed_val, 0)):,}{suffix}"
        return f"{prefix}{processed_val:,.{decimals}f}{suffix}"
    return "N/A"

# 6. Compact Full-Width CSS with Equal Column Widths
def apply_custom_style(styler):
    styler.set_table_styles([
        # Force table to 100% width and set fixed layout for equal columns
        {'selector': '', 'props': [
            ('width', '100%'), 
            ('table-layout', 'fixed'), # This is key for equal widths
            ('border-collapse', 'collapse')
        ]},
                                
        # Headers
        {'selector': 'th', 'props': [
            ('background-color', '#f0f2f6'), 
            ('color', '#1f77b4'), 
            ('font-weight', 'bold'), 
            ('text-align', 'center'), 
            ('padding', '8px'),
            ('font-size', '14px'),
            ('width', '20%') # Sets equal width for 5 columns (1 label + 4 data)
        ]},
                                
        # Cells
        {'selector': 'td', 'props': [
            ('padding', '6px'), 
            ('border-bottom', '1px solid #e6e9ef'), 
            ('text-align', 'center'),
            ('font-size', '13px'),
            ('font-weight', 'bold'),
            ('overflow', 'hidden'), # Prevents text from breaking layout
            ('text-overflow', 'ellipsis')
        ]},
                                
        {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#fafafa')]},
                                
        # Align first column text to the left but keep its width same as others
        {'selector': 'td:first-child', 'props': [
            ('text-align', 'left'), 
            ('font-weight', 'bold'), 
            ('color', '#1f77b4'),
            ('padding-left', '10px')
        ]},
        {'selector': 'th:first-child', 'props': [
            ('text-align', 'left'), 
            ('padding-left', '10px')
        ]}
    ])
    return styler

# 2. Refined Styling Function
def style_financial_chart(fig, df_values):
    # Dynamic range calculation to avoid label cutoff
    y_max = df_values.max() * 1.3 if not df_values.empty else 100
    
    fig.update_traces(
        marker_color="#00b18d", 
        texttemplate='%{y:,.0f}',
        textposition='outside',
        cliponaxis=False,
        width=0.4
    )
    fig.update_layout(
        margin=dict(t=70, l=10, r=10, b=10),
        height=380,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(type='category', showgrid=False, title=None, tickfont=dict(color='#7d8592')),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, y_max], title=None)
        # annotations=[dict(
        #     x=1, y=1.15, xref="paper", yref="paper",
        #     text="*All values are in Rs. Cr", showarrow=False,
        #     font=dict(size=11, color="#7d8592")
        # )]
    )
    return fig

# Helper function for Indian Numbering System
def format_indian_currency(number):
    """Formats a number into Indian Lakhs/Crores style."""
    s = f"{number:.2f}"
    main, fraction = s.split(".")
    last_three = main[-3:]
    other = main[:-3]
    if other:
        # Group digits in pairs for everything before the last 3 digits
        import re
        other = re.sub(r"(\d)(?=(\d{2})+(?!\d))", r"\1,", other)
        return f"{other},{last_three}.{fraction}"
    return f"{last_three}.{fraction}"