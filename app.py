import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import os

# Import custom modules for indicators
from utils.mag7_btc import get_mag7_btc_data
from utils.pi_cycle import get_pi_cycle_data
from utils.app_store import get_coinbase_ranking
from utils.cbbi import get_cbbi_data
from utils.halving_tracker import get_halving_data
from data_manager import update_database, get_latest_data

# Page configuration
st.set_page_config(
    page_title="Crypto Market Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dashboard title and description
st.title("Crypto Market Events Tracker")
st.markdown("""
This dashboard tracks multiple crypto market indicators to help determine optimal entry and exit points.
Data is updated daily and provides signals based on historical patterns.
""")

# Sidebar for navigation and settings
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Indicator",
    ["Dashboard Overview", "MAG7 vs Bitcoin", "Pi Cycle", "Coinbase App Ranking", "CBBI Score", "Halving Cycle"]
)

# Update data button in sidebar
if st.sidebar.button("Update All Data"):
    with st.spinner("Updating data from sources..."):
        update_database()
    st.sidebar.success("Data updated successfully!")

# Get the latest data for all indicators
data = get_latest_data()

# Function to create indicator status
def get_indicator_status(name, value, thresholds):
    """Returns the status and color for an indicator based on thresholds"""
    if value is None:
        return "Unknown", "gray"
    
    if name == "MAG7 vs BTC":
        # For MAG7-BTC index, interpret based on moving averages
        ma100 = thresholds[0]
        ma200 = thresholds[1]
        
        # Check if we have valid MA values
        if ma100 is None or ma200 is None:
            return "Unknown", "gray"
            
        if value > ma100:  # Above 100-day MA
            return "Bullish", "green"
        elif value < ma200:  # Below 200-day MA
            return "Bearish", "red"
        else:
            return "Neutral", "yellow"
    
    elif name == "Pi Cycle":
        # For Pi cycle, interpret based on crossovers
        if value > 0.98:  # Near crossover
            return "Top Signal", "red"
        elif value < 0.8:
            return "Normal", "green"
        else:
            return "Warning", "yellow"
    
    elif name == "Coinbase Rank":
        # For Coinbase ranking, interpret based on app store rank
        # Handle "200+" string format
        if isinstance(value, str) and "+" in value:
            # If rank is "200+" or similar, it's outside the top 200
            return "Normal Interest", "green"
        
        # Convert to numeric if needed
        try:
            numeric_value = float(value) if isinstance(value, str) else value
            if numeric_value <= 10:  # Top 10 in App Store
                return "Market Euphoria", "red"
            elif numeric_value <= 50:
                return "Growing Interest", "yellow"
            else:
                return "Normal Interest", "green"
        except (ValueError, TypeError):
            # If conversion fails, assume a high rank (low interest)
            return "Normal Interest", "green"
    
    elif name == "CBBI Score":
        # For CBBI Score, interpret based on score value
        if value > 0.8:
            return "Near Top", "red"
        elif value > 0.6:
            return "Caution", "yellow"
        else:
            return "Accumulation", "green"
    
    elif name == "Halving Cycle":
        # For Halving Cycle, interpret based on days after halving
        # Value is percentage through expected 520-day cycle
        if value > 0.8:
            return "Late Cycle", "red"
        elif value > 0.5:
            return "Mid Cycle", "yellow"
        else:
            return "Early Cycle", "green"
    
    return "Unknown", "gray"

# Dashboard Overview
if page == "Dashboard Overview":
    st.header("Market Indicators Dashboard")
    
    # Add description about what this dashboard shows
    st.markdown("""
    This dashboard displays the current status of multiple market indicators that can help identify:
    - **Market Tops**: When multiple indicators signal caution or bearish conditions
    - **Accumulation Zones**: When indicators suggest favorable entry points
    - **Overall Market Health**: A quick overview of market sentiment across indicators
    """)
    
    # Create indicator grid
    col1, col2, col3 = st.columns(3)
    
    # MAG7-BTC Index
    with col1:
        st.subheader("MAG7 vs Bitcoin")
        if 'mag7_btc' in data and data['mag7_btc'] is not None:
            current_value = data['mag7_btc'].get('current_value')
            ma100 = data['mag7_btc'].get('current_ma100')
            ma200 = data['mag7_btc'].get('current_ma200')
            status, color = get_indicator_status("MAG7 vs BTC", current_value, [ma100, ma200])
            
            st.metric(
                label="Index Value", 
                value=f"{current_value:.2f}" if current_value else "N/A",
                delta=f"{(current_value - ma100):.2f}" if current_value is not None and ma100 is not None else None
            )
            st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
        else:
            st.warning("MAG7-BTC data not available")
    
    # Pi Cycle
    with col2:
        st.subheader("Pi Cycle Indicator")
        if 'pi_cycle' in data and data['pi_cycle'] is not None:
            pi_ratio = data['pi_cycle'].get('ratio')
            status, color = get_indicator_status("Pi Cycle", pi_ratio, [0.95, 0.8])
            
            st.metric(
                label="Pi Cycle Ratio", 
                value=f"{pi_ratio:.2f}" if pi_ratio else "N/A"
            )
            st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
        else:
            st.warning("Pi Cycle data not available")
    
    # Coinbase Ranking
    with col3:
        st.subheader("Coinbase App Ranking")
        if 'coinbase_rank' in data and data['coinbase_rank'] is not None:
            rank = data['coinbase_rank'].get('rank')
            status, color = get_indicator_status("Coinbase Rank", rank, [5, 50])
            
            # Format the rank display properly (handling string values like "200+")
            if isinstance(rank, str) and "+" in rank:
                # Already formatted with + sign
                display_rank = f"#{rank}"
            else:
                display_rank = f"#{rank}" if rank else "N/A"
                
            st.metric(
                label="App Store Rank", 
                value=display_rank
            )
            st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
        else:
            st.warning("Coinbase ranking data not available")
    
    # Second row
    col1, col2 = st.columns(2)
    
    # CBBI Score
    with col1:
        st.subheader("CBBI Score")
        if 'cbbi' in data and data['cbbi'] is not None:
            score = data['cbbi'].get('score')
            status, color = get_indicator_status("CBBI Score", score, [0.8, 0.5])
            
            st.metric(
                label="Current Score", 
                value=f"{score:.2f}" if score else "N/A"
            )
            st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
        else:
            st.warning("CBBI Score data not available")
    
    # Halving Cycle
    with col2:
        st.subheader("BTC Halving Cycle")
        if 'halving' in data and data['halving'] is not None:
            days_since = data['halving'].get('days_since_halving')
            percentage = days_since / 520 if days_since is not None else None
            remaining_days = 520 - days_since if days_since is not None else None
            
            status, color = get_indicator_status("Halving Cycle", percentage, [0.8, 0.5])
            
            st.metric(
                label="Days Since Halving", 
                value=f"{days_since}" if days_since is not None else "N/A",
                delta=f"{remaining_days} days until projected top" if remaining_days is not None else None
            )
            st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
        else:
            st.warning("Halving cycle data not available")
    
    # Combined Analysis
    st.header("Combined Market Analysis")
    
    # Count indicators by status
    if data:
        indicators = []
        
        # MAG7 vs BTC
        if 'mag7_btc' in data and data['mag7_btc'] is not None:
            current_value = data['mag7_btc'].get('current_value')
            ma100 = data['mag7_btc'].get('current_ma100')
            ma200 = data['mag7_btc'].get('current_ma200')
            status, _ = get_indicator_status("MAG7 vs BTC", current_value, [ma100, ma200])
            indicators.append(status)
        
        # Pi Cycle
        if 'pi_cycle' in data and data['pi_cycle'] is not None:
            pi_ratio = data['pi_cycle'].get('ratio')
            status, _ = get_indicator_status("Pi Cycle", pi_ratio, [0.95, 0.8])
            indicators.append(status)
        
        # Coinbase Ranking
        if 'coinbase_rank' in data and data['coinbase_rank'] is not None:
            rank = data['coinbase_rank'].get('rank')
            status, _ = get_indicator_status("Coinbase Rank", rank, [5, 50])
            indicators.append(status)
        
        # CBBI Score
        if 'cbbi' in data and data['cbbi'] is not None:
            score = data['cbbi'].get('score')
            status, _ = get_indicator_status("CBBI Score", score, [0.8, 0.5])
            indicators.append(status)
        
        # Halving Cycle
        if 'halving' in data and data['halving'] is not None:
            days_since = data['halving'].get('days_since_halving')
            percentage = days_since / 520 if days_since is not None else None
            status, _ = get_indicator_status("Halving Cycle", percentage, [0.8, 0.5])
            indicators.append(status)
        
        # Count each status type
        bullish_count = indicators.count("Bullish") + indicators.count("Normal") + indicators.count("Accumulation") + indicators.count("Early Cycle")
        neutral_count = indicators.count("Neutral") + indicators.count("Warning") + indicators.count("Growing Interest") + indicators.count("Caution") + indicators.count("Mid Cycle")
        bearish_count = indicators.count("Bearish") + indicators.count("Top Signal") + indicators.count("Market Euphoria") + indicators.count("Near Top") + indicators.count("Late Cycle")
        
        # Create a pie chart 
        fig = px.pie(
            values=[bullish_count, neutral_count, bearish_count],
            names=["Bullish/Accumulation", "Neutral/Warning", "Bearish/Top Signals"],
            color=["Bullish/Accumulation", "Neutral/Warning", "Bearish/Top Signals"],
            color_discrete_map={"Bullish/Accumulation": "green", "Neutral/Warning": "yellow", "Bearish/Top Signals": "red"},
            title="Overall Market Sentiment"
        )
        st.plotly_chart(fig)
        
        # Market summary
        if bearish_count >= 3:
            st.error("⚠️ Multiple indicators showing top signals - consider reducing exposure")
        elif bearish_count >= 2:
            st.warning("🔍 Some top indicators active - monitor closely and consider taking profits")
        elif bullish_count >= 3:
            st.success("✅ Most indicators in accumulation phase - favorable for long-term entry")
        else:
            st.info("🔄 Mixed market signals - maintain balanced exposure")

# MAG7 vs Bitcoin page
elif page == "MAG7 vs Bitcoin":
    st.header("MAG7 vs Bitcoin Index")
    
    # Description
    st.markdown("""
    This index tracks the performance of Bitcoin against the MAG7 stocks (Microsoft, Apple, Google, Amazon, Meta, Tesla, Nvidia).
    The index is weighted with 50% Bitcoin and 50% distributed among the MAG7 stocks.
    """)
    
    # Description
    st.markdown("""
    This page shows the relationship between Bitcoin and major tech stocks (MAG7).
    The index is weighted with 50% Bitcoin and 50% distributed among the MAG7 stocks.
    """)
    
    # Get MAG7 vs BTC data
    if 'mag7_btc' in data and data['mag7_btc'] is not None:
        # Display current values
        col1, col2, col3 = st.columns(3)
        with col1:
            current_value = data['mag7_btc'].get('current_value')
            st.metric(
                label="Current Index Value", 
                value=f"{current_value:.2f}" if current_value else "N/A"
            )
        
        with col2:
            ma150 = data['mag7_btc'].get('current_ma150', None)
            st.metric(
                label="150-day MA", 
                value=f"{ma150:.2f}" if ma150 else "N/A",
                delta=f"{(current_value - ma150):.2f}" if current_value and ma150 else None
            )
        
        with col3:
            ma200 = data['mag7_btc'].get('current_ma200')
            st.metric(
                label="200-day MA", 
                value=f"{ma200:.2f}" if ma200 else "N/A",
                delta=f"{(current_value - ma200):.2f}" if current_value and ma200 else None
            )
        
        # Create the chart
        fig = go.Figure()
        
        # Add the main index line
        fig.add_trace(go.Scatter(
            x=data['mag7_btc']['dates'],
            y=data['mag7_btc']['index_values'],
            name="BTC-MAG7 Index",
            line=dict(color='blue', width=2),
            mode='lines'  # Ensure we're using line mode only
        ))
        
        # Add the MAs
        # Only showing MA200 (removed MA100 as requested)
        fig.add_trace(go.Scatter(
            x=data['mag7_btc']['dates'],
            y=data['mag7_btc']['ma200'],
            name="MA200",
            line=dict(color='red', width=1.5),
            mode='lines'
        ))
        
        # Only showing EMA200 (removed EMA100 as requested)
        
        fig.add_trace(go.Scatter(
            x=data['mag7_btc']['dates'],
            y=data['mag7_btc']['ema200'],
            name="EMA200",
            line=dict(color='green', width=1.5, dash='dot'),
            mode='lines'
        ))
        
        # Add cycle tops and bottoms if available
        if 'tops' in data['mag7_btc']:
            top_dates = [item['date'] for item in data['mag7_btc']['tops']]
            top_values = [item['value'] for item in data['mag7_btc']['tops']]
            
            fig.add_trace(go.Scatter(
                x=top_dates,
                y=top_values,
                mode='markers',
                marker=dict(color='red', size=12, symbol='triangle-down'),
                name="Cycle Tops"
            ))
        
        if 'bottoms' in data['mag7_btc']:
            bottom_dates = [item['date'] for item in data['mag7_btc']['bottoms']]
            bottom_values = [item['value'] for item in data['mag7_btc']['bottoms']]
            
            fig.add_trace(go.Scatter(
                x=bottom_dates,
                y=bottom_values,
                mode='markers',
                marker=dict(color='green', size=12, symbol='triangle-up'),
                name="Cycle Bottoms"
            ))
        
        # Layout
        fig.update_layout(
            title="MAG7 vs Bitcoin Index",
            xaxis_title="Date",
            yaxis_title="Index Value (Normalized)",
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Analysis
        st.subheader("Current Analysis")
        if current_value > ma100 and current_value > ma200:
            st.success("✅ The index is above both the 100-day and 200-day moving averages, indicating a bullish trend.")
        elif current_value < ma100 and current_value < ma200:
            st.error("⚠️ The index is below both the 100-day and 200-day moving averages, indicating a bearish trend.")
        else:
            st.warning("🔍 The index is between the 100-day and 200-day moving averages, indicating a mixed or transitioning market.")
    else:
        st.warning("MAG7-BTC data not available. Please update the data.")

# Pi Cycle page
elif page == "Pi Cycle":
    st.header("Pi Cycle Top/Bottom Indicator")
    
    # Description
    st.markdown("""
    The Pi Cycle Top Indicator has historically been effective at detecting periods where Bitcoin reaches a market top. 
    It uses the 111-day moving average (111DMA) and the 350-day moving average multiplied by 2 (350DMA×2).
    
    When these two moving averages cross, it has historically signaled a market top.
    """)
    
    # Featured image
    # Additional description
    st.markdown("""
    When the 111-day MA crosses above the 350-day MA × 2, it has historically signaled market tops.
    This indicator has been reliable across multiple Bitcoin cycles.
    """)
    
    # Get Pi Cycle data
    if 'pi_cycle' in data and data['pi_cycle'] is not None:
        # Display current values
        col1, col2, col3 = st.columns(3)
        with col1:
            pi_ratio = data['pi_cycle'].get('ratio')
            status, color = get_indicator_status("Pi Cycle", pi_ratio, [0.95, 0.8])
            
            st.metric(
                label="Current Ratio (111DMA / 350DMA×2)", 
                value=f"{pi_ratio:.3f}" if pi_ratio else "N/A"
            )
            st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
        
        with col2:
            ma111 = data['pi_cycle'].get('ma111')
            st.metric(
                label="111-day MA", 
                value=f"${ma111:,.0f}" if ma111 else "N/A"
            )
        
        with col3:
            ma350x2 = data['pi_cycle'].get('ma350x2')
            st.metric(
                label="350-day MA × 2", 
                value=f"${ma350x2:,.0f}" if ma350x2 else "N/A"
            )
        
        # Create the chart
        fig = go.Figure()
        
        # Add Bitcoin price
        fig.add_trace(go.Scatter(
            x=data['pi_cycle']['dates'],
            y=data['pi_cycle']['btc_price'],
            name="Bitcoin Price",
            line=dict(color='blue', width=2)
        ))
        
        # Add the 111 DMA
        fig.add_trace(go.Scatter(
            x=data['pi_cycle']['dates'],
            y=data['pi_cycle']['ma111_values'],
            name="111-day MA",
            line=dict(color='orange', width=1.5)
        ))
        
        # Add the 350 DMA x 2
        fig.add_trace(go.Scatter(
            x=data['pi_cycle']['dates'],
            y=data['pi_cycle']['ma350x2_values'],
            name="350-day MA × 2",
            line=dict(color='red', width=1.5)
        ))
        
        # Add crossover points if available
        if 'crossovers' in data['pi_cycle']:
            crossover_dates = [item['date'] for item in data['pi_cycle']['crossovers']]
            crossover_values = [item['price'] for item in data['pi_cycle']['crossovers']]
            
            fig.add_trace(go.Scatter(
                x=crossover_dates,
                y=crossover_values,
                mode='markers',
                marker=dict(color='red', size=12, symbol='x'),
                name="Crossover Points"
            ))
        
        # Layout
        fig.update_layout(
            title="Pi Cycle Indicator",
            xaxis_title="Date",
            yaxis_title="Bitcoin Price (USD)",
            height=600,
            yaxis_type="log",  # Log scale for price
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Ratio chart
        if 'ratio_values' in data['pi_cycle']:
            fig2 = go.Figure()
            
            # Add ratio line
            fig2.add_trace(go.Scatter(
                x=data['pi_cycle']['dates'],
                y=data['pi_cycle']['ratio_values'],
                name="111DMA / 350DMA×2 Ratio",
                line=dict(color='purple', width=2)
            ))
            
            # Add threshold line at 0.98
            fig2.add_shape(
                type="line",
                x0=min(data['pi_cycle']['dates']),
                y0=0.98,
                x1=max(data['pi_cycle']['dates']),
                y1=0.98,
                line=dict(color="red", width=2, dash="dash")
            )
            
            # Add threshold line at 0.8
            fig2.add_shape(
                type="line",
                x0=min(data['pi_cycle']['dates']),
                y0=0.8,
                x1=max(data['pi_cycle']['dates']),
                y1=0.8,
                line=dict(color="green", width=2, dash="dash")
            )
            
            # Layout
            fig2.update_layout(
                title="Pi Cycle Ratio (Values above 0.98 historically signal market tops)",
                xaxis_title="Date",
                yaxis_title="Ratio Value",
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        # Analysis
        st.subheader("Current Analysis")
        if pi_ratio > 0.98:
            st.error("⚠️ The Pi Cycle ratio is very close to or above 1, suggesting a potential market top is forming.")
        elif pi_ratio > 0.9:
            st.warning("🔍 The Pi Cycle ratio is approaching the critical threshold. Increased caution is warranted.")
        else:
            st.success("✅ The Pi Cycle ratio is well below the danger level, suggesting no imminent market top.")
    else:
        st.warning("Pi Cycle data not available. Please update the data.")

# Coinbase App Ranking page
elif page == "Coinbase App Ranking":
    st.header("Coinbase App Store Ranking")
    
    # Description
    st.markdown("""
    This indicator tracks Coinbase's position in the App Store rankings. Historically, when Coinbase rises to the top 10 
    or #1 position in the App Store, it has correlated with local peaks in cryptocurrency market interest and often price.
    
    When many new users rush to download crypto trading apps, it often signals peak retail interest.
    """)
    
    # Additional context
    st.markdown("""
    Note: This indicator specifically tracks the Coinbase app position in the free iPhone apps 
    ranking in the US App Store. Rankings are updated daily.
    """)
    
    # Embed the professional chart from The Block
    st.subheader("Crypto Apps Ranking (Data from The Block)")
    
    st.components.v1.iframe(
        src="https://www.theblock.co/data/alternative-crypto-metrics/app-usage/crypto-apps-ranking-on-the-app-store-in-the-us/embed",
        height=450,
        scrolling=False
    )
    
    st.markdown("""
    *Chart source: [The Block](https://www.theblock.co/data/alternative-crypto-metrics/app-usage/crypto-apps-ranking-on-the-app-store-in-the-us)*
    """)
    
    # Add a divider
    st.markdown("---")
    
    # Get Coinbase Ranking data from our own scraper (as a backup/additional data point)
    st.subheader("Additional Data")
    
    if 'coinbase_rank' in data and data['coinbase_rank'] is not None:
        # Display current rank
        rank = data['coinbase_rank'].get('rank')
        status, color = get_indicator_status("Coinbase Rank", rank, [5, 50])
        
        col1, col2 = st.columns(2)
        with col1:
            # Format the rank display properly (handling string values like "200+")
            if isinstance(rank, str) and "+" in rank:
                # Already formatted with + sign
                display_rank = f"#{rank}"
            else:
                display_rank = f"#{rank}" if rank else "N/A"
                
            st.metric(
                label="Current App Store Rank", 
                value=display_rank
            )
            st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
        
        with col2:
            last_updated = data['coinbase_rank'].get('last_updated')
            st.metric(
                label="Last Updated", 
                value=last_updated
            )
        
        # Analysis
        st.subheader("Current Analysis")
        
        # Check if rank is a string with "+" (like "200+")
        if isinstance(rank, str) and "+" in rank:
            st.success("✅ Coinbase app ranking is outside the top charts (200+), suggesting no excessive retail interest or market euphoria.")
        else:
            # Convert to numeric for comparison if it's a string number
            try:
                numeric_rank = float(rank) if isinstance(rank, str) else rank
                if numeric_rank <= 10:
                    st.error("⚠️ Coinbase is in the top 10 apps, which historically has coincided with market tops. This suggests extreme retail interest.")
                elif numeric_rank <= 50:
                    st.warning("🔍 Coinbase ranking shows elevated retail interest. Monitor closely as it might signal increasing market euphoria.")
                else:
                    st.success("✅ Coinbase app ranking is at a normal level, suggesting no excessive retail interest or market euphoria.")
            except (ValueError, TypeError):
                # If conversion fails, assume it's a high rank
                st.success("✅ Coinbase app ranking appears to be at a normal level, suggesting no excessive retail interest or market euphoria.")
    else:
        # Even if our scraper fails, we still have The Block's chart
        st.info("Our internal data collector couldn't retrieve the current Coinbase app rank. Please refer to The Block's chart above for the most current data.")

# CBBI Score page
elif page == "CBBI Score":
    st.header("CBBI (Colin Talks Crypto Bitcoin Index) Score")
    
    # Description
    st.markdown("""
    The CBBI Score combines multiple technical indicators to create a single metric for estimating Bitcoin market tops.
    It includes indicators like Pi Cycle, Puell Multiple, 2-Year MA Multiplier, and others.
    
    Values closer to 1 suggest market euphoria and potential tops, while values closer to 0 suggest bear markets and accumulation opportunities.
    """)
    
    # Technical details
    st.markdown("""
    CBBI score ranges from 0 to 1:
    - Score > 0.8: Potential market top, consider reducing exposure
    - Score 0.6-0.8: Caution zone, monitor closely
    - Score < 0.6: Accumulation phase, favorable for long-term entry
    """)
    
    # Get CBBI data
    if 'cbbi' in data and data['cbbi'] is not None:
        # Display current score
        score = data['cbbi'].get('score')
        status, color = get_indicator_status("CBBI Score", score, [0.8, 0.5])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Current CBBI Score", 
                value=f"{score:.2f}" if score else "N/A"
            )
            st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
        
        with col2:
            last_updated = data['cbbi'].get('last_updated')
            st.metric(
                label="Last Updated", 
                value=last_updated
            )
        
        # Create the chart
        if 'history' in data['cbbi'] and data['cbbi']['history']:
            history = data['cbbi']['history']
            dates = [item['date'] for item in history]
            scores = [item['score'] for item in history]
            btc_prices = [item['btc_price'] for item in history]
            
            # Main CBBI chart
            fig = go.Figure()
            
            # Add score line
            fig.add_trace(go.Scatter(
                x=dates,
                y=scores,
                name="CBBI Score",
                line=dict(color='blue', width=2)
            ))
            
            # Add threshold lines
            fig.add_shape(
                type="line",
                x0=min(dates),
                y0=0.8,
                x1=max(dates),
                y1=0.8,
                line=dict(color="red", width=2, dash="dash")
            )
            
            fig.add_shape(
                type="line",
                x0=min(dates),
                y0=0.2,
                x1=max(dates),
                y1=0.2,
                line=dict(color="green", width=2, dash="dash")
            )
            
            # Layout
            fig.update_layout(
                title="CBBI Score Over Time",
                xaxis_title="Date",
                yaxis_title="CBBI Score",
                height=500,
                yaxis=dict(
                    range=[0, 1],
                    tickmode="linear",
                    tick0=0,
                    dtick=0.1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # BTC price with CBBI overlays
            fig2 = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add BTC price
            fig2.add_trace(
                go.Scatter(
                    x=dates,
                    y=btc_prices,
                    name="Bitcoin Price",
                    line=dict(color='orange', width=2)
                ),
                secondary_y=False
            )
            
            # Add CBBI score
            fig2.add_trace(
                go.Scatter(
                    x=dates,
                    y=scores,
                    name="CBBI Score",
                    line=dict(color='blue', width=2)
                ),
                secondary_y=True
            )
            
            # Layout
            fig2.update_layout(
                title="Bitcoin Price vs CBBI Score",
                xaxis_title="Date",
                height=500
            )
            
            fig2.update_yaxes(title_text="Bitcoin Price (USD)", secondary_y=False)
            fig2.update_yaxes(
                title_text="CBBI Score", 
                secondary_y=True,
                range=[0, 1],
                tickmode="linear",
                tick0=0,
                dtick=0.1
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Analysis
            st.subheader("Current Analysis")
            if score > 0.8:
                st.error("⚠️ CBBI Score indicates market euphoria. Historically, scores above 0.8 have been seen near market tops.")
            elif score > 0.6:
                st.warning("🔍 CBBI Score shows increasing market optimism. Consider taking partial profits if the trend continues.")
            elif score < 0.3:
                st.success("✅ CBBI Score suggests a potential accumulation phase. Historically favorable for long-term entry.")
            else:
                st.info("🔄 CBBI Score is in the neutral range. The market is neither in fear nor greed territory.")
        else:
            st.warning("Historical CBBI data not available.")
    else:
        st.warning("CBBI data not available. Please update the data.")

# Halving Cycle page
elif page == "Halving Cycle":
    st.header("Bitcoin Halving Cycle Analysis")
    
    # Description
    st.markdown("""
    Bitcoin follows a 4-year cycle centered around the "halving" event, where mining rewards are cut in half.
    
    Historically, Bitcoin reaches its cycle top approximately 12-18 months after a halving event.
    This tracker monitors the days since the most recent halving and projects the potential timeframe for a market cycle top.
    """)
    
    # Technical details
    st.markdown("""
    This indicator measures the progression through the ~520-day period after halving.
    Each halving creates a similar price movement pattern, with potential market tops typically 
    occurring 12-18 months (360-540 days) after each halving event.
    """)
    
    # Get Halving Cycle data
    if 'halving' in data and data['halving'] is not None:
        # Display current values
        last_halving = data['halving'].get('last_halving_date')
        days_since = data['halving'].get('days_since_halving')
        next_halving = data['halving'].get('next_halving_date')
        days_until_next = data['halving'].get('days_until_next_halving')
        
        # Progress bar for current cycle
        percentage_complete = days_since / (days_since + days_until_next) * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Last Halving Date", 
                value=last_halving
            )
            st.metric(
                label="Days Since Halving", 
                value=days_since
            )
        
        with col2:
            st.metric(
                label="Next Halving (Estimated)", 
                value=next_halving
            )
            st.metric(
                label="Days Until Next Halving", 
                value=days_until_next
            )
        
        st.progress(percentage_complete / 100)
        st.text(f"Current halving cycle: {percentage_complete:.1f}% complete")
        
        # Display 520-day marker
        if 'projected_top_date' in data['halving']:
            projected_date = data['halving'].get('projected_top_date')
            days_until_projected = data['halving'].get('days_until_projected_top')
            
            st.subheader("Projected Cycle Top")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="Projected Top Date (520 days after halving)", 
                    value=projected_date
                )
            
            with col2:
                st.metric(
                    label="Days Until Projected Top", 
                    value=days_until_projected,
                    delta=f"{'-' if days_until_projected < 0 else ''}{abs(days_until_projected)} days {' past' if days_until_projected < 0 else 'remaining'}"
                )
            
            # Calculate 520-day range (historically tops occur 12-18 months after halving)
            early_range = datetime.strptime(projected_date, "%Y-%m-%d") - timedelta(days=90)
            late_range = datetime.strptime(projected_date, "%Y-%m-%d") + timedelta(days=90)
            
            st.info(f"🔍 Historical cycle tops occur within a range of 12-18 months after halving. The projected range for this cycle's top is from {early_range.strftime('%Y-%m-%d')} to {late_range.strftime('%Y-%m-%d')}.")
        
        # Chart with previous halving cycles
        if 'previous_cycles' in data['halving'] and data['halving']['previous_cycles']:
            st.subheader("Previous Halving Cycles Performance")
            
            cycles = data['halving']['previous_cycles']
            
            # Create figure
            fig = go.Figure()
            
            # Add each cycle
            for cycle in cycles:
                fig.add_trace(go.Scatter(
                    x=[i for i in range(len(cycle['normalized_prices']))],
                    y=cycle['normalized_prices'],
                    name=f"Cycle {cycle['halving_date']}",
                    line=dict(width=2)
                ))
            
            # Add current cycle if available
            if 'current_cycle' in data['halving']:
                current = data['halving']['current_cycle']
                fig.add_trace(go.Scatter(
                    x=[i for i in range(len(current['normalized_prices']))],
                    y=current['normalized_prices'],
                    name="Current Cycle",
                    line=dict(color='black', width=3)
                ))
            
            # Add vertical line at day 520
            fig.add_shape(
                type="line",
                x0=520,
                y0=0,
                x1=520,
                y1=1000,  # Arbitrary high value
                line=dict(color="red", width=2, dash="dash")
            )
            
            # Layout
            fig.update_layout(
                title="Bitcoin Performance After Halving (Normalized to 100 at Halving Date)",
                xaxis_title="Days Since Halving",
                yaxis_title="Normalized Price (Halving Day = 100)",
                height=600,
                yaxis_type="log"  # Log scale for better visualization
            )
            
            # Add annotation for 520-day marker
            fig.add_annotation(
                x=520,
                y=fig.data[0].y[-1] if len(fig.data) > 0 and len(fig.data[0].y) > 520 else 500,
                text="Historical Top Range (520 days)",
                showarrow=True,
                arrowhead=1
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Analysis
            st.subheader("Current Analysis")
            
            if days_since < 200:
                st.success("✅ Early in the halving cycle. Historically, this has been an accumulation phase.")
            elif days_since < 400:
                st.info("🔄 Mid-cycle. Typically a period of steady growth following the halving.")
            elif days_since < 550:
                st.warning("🔍 Approaching the historical top range. Increased caution is warranted.")
            else:
                st.error("⚠️ Beyond the typical cycle top timeframe. Historical patterns suggest increased risk.")
        else:
            st.warning("Historical cycle data not available.")
    else:
        st.warning("Halving cycle data not available. Please update the data.")

# Footer
st.markdown("---")
st.caption("Crypto Market Events Tracker - Data updated daily - Not financial advice")
