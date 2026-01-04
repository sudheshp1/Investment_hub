import streamlit as st
from styles import apply_custom_css

st.set_page_config(
    page_title="Investment Hub",
    page_icon="💰",
    layout="wide"
)

# Apply your existing styles
apply_custom_css()

# Create 3 columns: [Gap, Content, Gap]
# Adjust the ratios [1, 2, 1] to [1, 3, 1] if you want the center wider
left_co, cent_co, last_co = st.columns([1, 2, 1])

with cent_co:
    st.markdown('<h1 class="main-title">Welcome to your Investment Hub</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center;">
        <p>Use the sidebar on the left to switch between:</p>
    </div>
    """, unsafe_allow_html=True)

    # Creating a nice centered card-like layout for the options
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**📊 Portfolio Dashboard**\n\nView your current holdings, P&L, fundamental & technical analysis")
        
    with col2:
        st.success("**🔍 Stock Screener**\n\nDiscover new opportunities based on fundamental & technical analysis")