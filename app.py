import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sqlite3
import os
import atexit

# Import custom modules for indicators
from utils.mag7_btc import get_mag7_btc_data
from utils.pi_cycle import get_pi_cycle_data
from utils.app_store import fetch_coinbase_rank_df
from utils.cbbi import get_cbbi_data
from utils.halving_tracker import get_halving_data
from data_manager import update_database, get_latest_data, get_historical_coinbase_rankings, get_historical_cbbi_scores, ensure_cbbi_and_rank_seed
from scheduler import start_scheduler, stop_scheduler

# Initialize and seed normalized tables if needed
ensure_cbbi_and_rank_seed()

# Start the background scheduler to keep data updated
start_scheduler()
# Register a function to stop the scheduler when the application exits
atexit.register(stop_scheduler)

# Page configuration
st.set_page_config(
    page_title="Crypto Market Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for navigation and settings
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Indicator",
    ["Dashboard Overview", "MAG7 vs Bitcoin", "Pi Cycle", "Coinbase App Ranking", "CBBI Score", "Halving Cycle"]
)

# Only show title and description on the main dashboard page
if page == "Dashboard Overview":
    st.title("Crypto Market Events Tracker")
    st.markdown("""
    This dashboard tracks multiple crypto market indicators to help determine optimal entry and exit points.
    Data is updated daily and provides signals based on historical patterns.
    """)

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
        ma150 = thresholds[0]
        ma200 = thresholds[1]
        
        # Check if we have valid MA values
        if ma150 is None or ma200 is None:
            return "Unknown", "gray"
            
        if value > ma150:  # Above 150-day MA
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
        # For CBBI Score - handle both decimal (0-1) and percentage (0-100) formats
        high_threshold = thresholds[0]
        low_threshold = thresholds[1]
        
        if value > high_threshold:  # Above 80% or 0.8
            return "Extreme Greed", "red"
        elif value < low_threshold:  # Below 50% or 0.5
            return "Fear", "green"
        else:
            return "Greed", "yellow"
    
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
            ma150 = data['mag7_btc'].get('current_ma150')
            ma200 = data['mag7_btc'].get('current_ma200')
            status, color = get_indicator_status("MAG7 vs BTC", current_value, [ma150, ma200])
            
            st.metric(
                label="Index Value", 
                value=f"{current_value:.2f}" if current_value else "N/A",
                delta=f"{(current_value - ma150):.2f}" if current_value is not None and ma150 is not None else None
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
            # Handle both dict and DataFrame data structures
            if isinstance(data['coinbase_rank'], dict):
                rank = data['coinbase_rank'].get('rank')
            else:
                # If it's a DataFrame or Series, extract the first value
                rank = data['coinbase_rank']['rank'].iloc[0] if hasattr(data['coinbase_rank'], 'iloc') else data['coinbase_rank'].get('rank')
            
            # Convert to scalar value if it's still a Series
            if hasattr(rank, 'item'):
                rank = rank.item()
            
            status, color = get_indicator_status("Coinbase Rank", rank, [5, 50])
            
            # Format the rank display properly (handling string values like "200+")
            if isinstance(rank, str) and "+" in rank:
                # Already formatted with + sign
                display_rank = f"#{rank}"
            elif rank is not None and rank != "N/A":
                display_rank = f"#{rank}"
            else:
                display_rank = "N/A"
                
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
            # Adjust thresholds based on whether score is in decimal (0-1) or percentage (0-100) format
            if score is not None and score > 1:
                # Score is in percentage format (0-100)
                status, color = get_indicator_status("CBBI Score", score, [80, 50])
            else:
                # Score is in decimal format (0-1)
                status, color = get_indicator_status("CBBI Score", score, [0.8, 0.5])
            
            # Display as whole number - check if score is already in percentage format
            if score is not None:
                # If score is greater than 1, it's already in percentage format (0-100)
                if score > 1:
                    display_score = f"{int(score)}"
                else:
                    # If score is 0-1, convert to percentage
                    display_score = f"{int(score*100)}"
            else:
                display_score = "N/A"
            
            st.metric(
                label="Current Score", 
                value=display_score
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
        if current_value > ma150 and current_value > ma200:
            st.success("✅ The index is above both the 150-day and 200-day moving averages, indicating a bullish trend.")
        elif current_value < ma150 and current_value < ma200:
            st.error("⚠️ The index is below both the 150-day and 200-day moving averages, indicating a bearish trend.")
        else:
            st.warning("🔍 The index is between the 150-day and 200-day moving averages, indicating a mixed or transitioning market.")
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
    
    # Embed the professional chart from The Block
    st.subheader("Crypto Apps Ranking (Data from The Block)")
    
    # Create a custom HTML/JS solution to try to focus on Coinbase
    # We'll include the iframe but add a message to help users focus on Coinbase
    st.markdown("""
    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin-bottom: 10px; background-color: #f8f9fa;">
        <p><strong>⭐ Tip:</strong> In the chart below, click on the other crypto apps in the legend to hide them, 
        leaving only Coinbase visible for clearer analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create chart options with AppFigures integration - making Live AppFigures the default tab
    tab3, tab2, tab1 = st.tabs(["Live AppFigures Rankings", "Coinbase Only", "All Crypto Apps"])
    
    with tab1:
        # Regular iframe with all data
        components.iframe(
            src="https://www.theblock.co/data/alternative-crypto-metrics/app-usage/crypto-apps-ranking-on-the-app-store-in-the-us/embed",
            height=450,
            scrolling=False
        )
    
    with tab2:
        # Create a simplified custom chart focused only on Coinbase
        st.markdown("#### Coinbase App Store Ranking Over Time")
        
        # Get historical Coinbase rankings from our database
        historical_rankings = get_historical_coinbase_rankings()
        
        if historical_rankings:
            # Extract the dates and ranks into lists for plotting
            dates = [entry['date'] for entry in historical_rankings]
            rankings = [entry['rank'] for entry in historical_rankings]
            
            # Create a figure
            fig = go.Figure()
            
            # Add the Coinbase ranking line (inverted Y axis to make lower ranks appear higher on chart)
            fig.add_trace(go.Scatter(
                x=dates,
                y=rankings,
                mode='lines+markers',
                name='Coinbase Rank',
                line=dict(color='#0052FF', width=3),  # Coinbase blue
                marker=dict(size=8)
            ))
            
            # Set the Y-axis to be reversed (lower ranks at top of chart)
            fig.update_layout(
                title='Coinbase US App Store Ranking History',
                xaxis_title='Date',
                yaxis_title='App Store Rank',
                yaxis=dict(
                    autorange='reversed',  # This makes rank #1 at the top
                    tickmode='array',
                    tickvals=[1, 10, 50, 100, 150, 200],
                    ticktext=['#1', '#10', '#50', '#100', '#150', '#200+']
                ),
                height=500,
                hovermode='x unified'
            )
            
            if len(dates) > 0:
                # Add specific threshold lines for interpretation
                fig.add_shape(type="line", x0=dates[0], x1=dates[-1], y0=10, y1=10,
                              line=dict(color="red", width=1, dash="dash"),
                              name="Extreme Interest")
                
                fig.add_shape(type="line", x0=dates[0], x1=dates[-1], y0=50, y1=50,
                              line=dict(color="orange", width=1, dash="dash"),
                              name="High Interest")
                              
                fig.add_shape(type="line", x0=dates[0], x1=dates[-1], y0=150, y1=150,
                              line=dict(color="green", width=1, dash="dash"),
                              name="Moderate Interest")
                
                # Add annotations for the thresholds
                fig.add_annotation(x=dates[-1], y=5, text="Extreme Market Euphoria",
                                  font=dict(color="red"), showarrow=False, xshift=10)
                
                fig.add_annotation(x=dates[-1], y=30, text="High Retail Interest",
                                  font=dict(color="orange"), showarrow=False, xshift=10)
                                  
                fig.add_annotation(x=dates[-1], y=100, text="Moderate Interest",
                                  font=dict(color="green"), showarrow=False, xshift=10)
                                  
                fig.add_annotation(x=dates[-1], y=175, text="Low Interest (Accumulation)",
                                  font=dict(color="blue"), showarrow=False, xshift=10)
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Add interpretation text
            st.markdown("""
            #### Interpretation:
            
            This chart tracks Coinbase's ranking in the US App Store for free iPhone apps over time. 
            
            - **Top 10 (#1-10)**: Extreme retail interest, often indicating market euphoria and potential tops
            - **Top 50 (#11-50)**: High retail interest, usually associated with strong bull markets
            - **Top 150 (#51-150)**: Moderate interest, typically seen during normal bull market conditions
            - **Below 150 (#150+)**: Low retail interest, often present during accumulation phases
            
            The Coinbase app ranking is a useful contrarian indicator as extreme retail interest often 
            coincides with market tops, while very low interest can indicate good accumulation opportunities.
            """)
        else:
            st.info("No historical Coinbase ranking data available yet. Data will accumulate over time as the tracker runs.")
            st.info("Try updating the data using the button on the main dashboard, or visit again tomorrow.")
    

    
    with tab3:
        # Create a section for live AppFigures data
        st.subheader("Live App Store Rankings")
        
        # Display the current Coinbase ranking from our scraper
        if 'coinbase_rank' in data and data['coinbase_rank'] is not None:
            rank = data['coinbase_rank'].get('rank')
            last_updated = data['coinbase_rank'].get('last_updated')
            source = data['coinbase_rank'].get('source', 'AppFigures.com - US iPhone Free Apps')
            
            # Create metrics display
            st.subheader("Coinbase Current Ranking")
            col1, col2 = st.columns(2)
            
            with col1:
                # Format the rank display properly
                if isinstance(rank, str) and "+" in rank:
                    display_rank = f"#{rank}"
                else:
                    display_rank = f"#{rank}" if rank else "N/A"
                
                st.metric(
                    label="Current App Store Rank", 
                    value=display_rank
                )
            
            with col2:
                st.metric(
                    label="Last Updated", 
                    value=last_updated if last_updated else "Unknown"
                )
            
            # Add source info
            st.caption(f"Source: {source}")
            
            # Display ranking interpretation
            if isinstance(rank, str) and "+" in rank:
                st.success("✅ Coinbase is currently outside the top 200 apps, suggesting very low retail interest in cryptocurrency at the moment.")
            elif isinstance(rank, int):
                if rank <= 10:
                    st.error("🚨 Coinbase is in the top 10 apps, which historically indicates extreme market euphoria and possible market tops!")
                elif rank <= 50:
                    st.warning("⚠️ Coinbase is in the top 50 apps, showing high retail interest that often precedes local market tops.")
                elif rank <= 150:
                    st.info("ℹ️ Coinbase is in the top 150 apps, indicating moderate retail interest in cryptocurrency.")
                else:
                    st.success("✅ Coinbase is outside the top 150 apps, suggesting low retail interest typical of accumulation phases.")
            
            # Add the AppFigures iframe
            st.markdown("### Browse Live App Store Rankings")
            st.info("The iframe below shows real-time data from AppFigures.com. You can browse through the rankings to manually verify Coinbase's position.")
            
            # Embedded iframe with live AppFigures data
            st.markdown("""
            <iframe src="https://appfigures.com/top-apps/ios-app-store/united-states/iphone/top-free" 
                    width="100%" height="600" frameborder="0"></iframe>
            """, unsafe_allow_html=True)
            
        else:
            st.warning("Could not retrieve current Coinbase ranking data. Please try updating the data.")
            
            # Still show the AppFigures embed even if our scraper failed
            st.markdown("### Browse Live App Store Rankings")
            st.info("The iframe below shows real-time data from AppFigures.com. You can browse to manually check Coinbase's position.")
            
            # Add the AppFigures iframe
            st.markdown("""
            <iframe src="https://appfigures.com/top-apps/ios-app-store/united-states/iphone/top-free" 
                    width="100%" height="600" frameborder="0"></iframe>
            """, unsafe_allow_html=True)
            
            # Add explanation at the bottom
            st.markdown("""
            ### About App Store Rankings
            
            This tab shows real-time data from AppFigures.com, tracking free iPhone apps in the US App Store.
            If Coinbase appears in the top charts, it indicates significant retail interest in cryptocurrency.
            
            Historically, Coinbase's App Store ranking has been a useful indicator of market cycles:
            - **Top 10 ranking**: Often coincides with market euphoria and potential tops
            - **Top 10-50**: Shows elevated retail interest, may indicate local tops
            - **Outside top 150**: Typically seen during accumulation phases
            """)
        

        
        # Get historical Coinbase rankings from our database
        historical_rankings = get_historical_coinbase_rankings()
        
        if historical_rankings:
            # Extract the dates and ranks into lists for plotting
            dates = [entry['date'] for entry in historical_rankings]
            rankings = [entry['rank'] for entry in historical_rankings]
            
            # Color code for market interpretation
            colors = []
            for rank in rankings:
                if rank <= 10:  # Top 10 = market top warning (extreme FOMO)
                    colors.append('red')
                elif rank <= 50:  # Top 50 = high retail interest
                    colors.append('orange')
                elif rank <= 150:  # Top 150 = moderate interest
                    colors.append('yellow')
                else:  # > 150 = low retail interest
                    colors.append('green')
        
            # Create the chart
            fig = go.Figure()
            
            # Add ranking line
            fig.add_trace(go.Scatter(
                x=dates,
                y=rankings,
                mode='lines+markers',
                name='Coinbase Ranking',
                line=dict(color='#0052FF', width=3),  # Coinbase blue
                marker=dict(
                    size=8,
                    color=colors,
                    line=dict(
                        color='DarkSlateGrey',
                        width=1
                    )
                )
            ))
        
            # Add horizontal zones for context
            # Red zone (top 10)
            fig.add_shape(
                type="rect",
                x0=min(dates),
                x1=max(dates),
                y0=0,
                y1=10,
                fillcolor="rgba(255,0,0,0.1)",
                line=dict(width=0),
                layer="below"
            )
            # Orange zone (top 11-50)
            fig.add_shape(
                type="rect",
                x0=min(dates),
                x1=max(dates),
                y0=10,
                y1=50,
                fillcolor="rgba(255,165,0,0.1)",
                line=dict(width=0),
                layer="below"
            )
            # Yellow zone (top 51-150)
            fig.add_shape(
                type="rect",
                x0=min(dates),
                x1=max(dates),
                y0=50,
                y1=150,
                fillcolor="rgba(255,255,0,0.1)",
                line=dict(width=0),
                layer="below"
            )
            # Green zone (>150)
            fig.add_shape(
                type="rect",
                x0=min(dates),
                x1=max(dates),
                y0=150,
                y1=300,
                fillcolor="rgba(0,255,0,0.05)",
                line=dict(width=0),
                layer="below"
            )
            
            # Customize chart layout
            fig.update_layout(
                title="Coinbase App Store Ranking (Simplified Approximation)",
                xaxis_title="Date",
                yaxis_title="App Store Ranking",
                yaxis=dict(
                    autorange="reversed",  # Lower number = better ranking
                    tickvals=[1, 10, 50, 100, 150, 200, 250, 300],
                    ticktext=["#1", "#10", "#50", "#100", "#150", "#200", "#250", "#300"],
                ),
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                annotations=[
                    dict(
                        x=0.5,
                        y=-0.15,
                        showarrow=False,
                        text="Note: This is a simplified approximation for illustration purposes only",
                        xref="paper",
                        yref="paper",
                        font=dict(size=10, color="gray")
                    )
                ]
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Add explanation about the visualization
            st.markdown("""
            **Chart Interpretation:**
            - 🔴 **Red zone (Top 10)**: Extreme retail FOMO, often coincides with market cycle tops
            - 🟠 **Orange zone (Top 50)**: Very high retail interest, potential local tops
            - 🟡 **Yellow zone (Top 50-150)**: Moderate retail interest, increasing momentum
            - 🟢 **Green zone (>150)**: Low retail interest, potential accumulation periods
            
            **Current status (rank ~255)**: Low retail interest in the green zone, suggesting the market 
            may be in an accumulation phase rather than at a cycle top.
            
            This visualization demonstrates how Coinbase's App Store ranking typically correlates with market 
            sentiment and cycle positioning.
        """)
    
    # Add a custom Coinbase-focused analysis section
    st.markdown("""
    ### Coinbase Ranking Explanation
    
    This tracker monitors Coinbase's position in the US App Store free iPhone apps rankings. 
    When Coinbase appears in the top charts (especially top 10-50), it indicates significant 
    retail interest in cryptocurrency, which has historically coincided with market cycle peaks.
    
    The chart above from The Block shows App Store rankings for major crypto apps including Coinbase. 
    Historically, when Coinbase rises to the top positions (ranks 1-10), it often coincides with 
    local market peaks and heightened retail interest.
    
    *Chart source: [The Block](https://www.theblock.co/data/alternative-crypto-metrics/app-usage/crypto-apps-ranking-on-the-app-store-in-the-us)*
    """)
    
    # Add a divider
    st.markdown("---")

# CBBI Score page
elif page == "CBBI Score":
    st.header("CBBI (Colin Talks Crypto Bitcoin Index) Score")
    
    # Get CBBI data
    if 'cbbi' in data and data['cbbi'] is not None:
        # Display current score
        score = data['cbbi'].get('score')
        status, color = get_indicator_status("CBBI Score", score, [0.8, 0.5])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Current CBBI Score", 
                value=f"{int(score*100)}" if score else "N/A"
            )
            st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
        
        with col2:
            last_updated = data['cbbi'].get('last_updated')
            st.metric(
                label="Last Updated", 
                value=last_updated
            )
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Daily Recorded CBBI", "Historical CBBI Chart", "CBBI vs BTC Price", "Official CBBI Chart"])
        
        with tab1:
            # Retrieve historical daily CBBI scores from our database
            st.subheader("Daily CBBI Score History")
            
            # Get recorded data from database
            historical_scores = get_historical_cbbi_scores(days=90)  # Default to 90 days
            
            if historical_scores:
                # Convert dates and scores for plotting
                dates = []
                for item in historical_scores:
                    # Ensure dates are in proper datetime format
                    if isinstance(item['date'], str):
                        try:
                            # Parse the date string to datetime object
                            date_obj = datetime.strptime(item['date'], '%Y-%m-%d')
                            dates.append(date_obj)
                        except ValueError:
                            # If parsing fails, just use the string
                            dates.append(item['date'])
                    else:
                        dates.append(item['date'])
                
                scores = [item['score'] * 100 for item in historical_scores]
                
                # Sort by date (oldest first for the chart)
                dates_scores = sorted(zip(dates, scores), key=lambda x: x[0])
                dates = [d for d, s in dates_scores]
                scores = [s for d, s in dates_scores]
                
                # Create CBBI daily history chart
                fig_daily = go.Figure()
                
                # Format dates for display if they're datetime objects
                display_dates = []
                for date in dates:
                    if isinstance(date, datetime):
                        display_dates.append(date.strftime('%Y-%m-%d'))
                    else:
                        display_dates.append(date)
                
                # Add score line
                fig_daily.add_trace(go.Scatter(
                    x=display_dates,
                    y=scores,
                    name="Daily CBBI Score",
                    line=dict(color='blue', width=2)
                ))
                
                # Add threshold lines if we have data
                if display_dates:
                    fig_daily.add_shape(
                        type="line",
                        x0=min(display_dates),
                        y0=80,
                        x1=max(display_dates),
                        y1=80,
                        line=dict(color="red", width=2, dash="dash")
                    )
                    
                    fig_daily.add_shape(
                        type="line",
                        x0=min(display_dates),
                        y0=20,
                        x1=max(display_dates),
                        y1=20,
                        line=dict(color="green", width=2, dash="dash")
                    )
                
                # Layout
                fig_daily.update_layout(
                    title="Daily CBBI Score Tracking (May 2025)",
                    xaxis_title="Date",
                    yaxis_title="CBBI Score",
                    height=500,
                    yaxis=dict(
                        range=[0, 100],
                        tickmode="linear",
                        tick0=0,
                        dtick=10
                    ),
                    # Improve date formatting on x-axis
                    xaxis=dict(
                        tickformat="%Y-%m-%d",
                        title_font=dict(size=12),
                        tickfont=dict(size=10)
                    )
                )
                
                st.plotly_chart(fig_daily, use_container_width=True)
                
                # Data table
                st.subheader("Recent CBBI Score Data")
                df = pd.DataFrame(historical_scores)
                
                # First ensure we have date in correct format
                df['date'] = pd.to_datetime(df['date'])
                
                # Sort by date (descending for table display)
                df = df.sort_values(by='date', ascending=False)
                
                # Format for display - check if score is already in percentage format
                if not df.empty:
                    # Check if scores are already in percentage format (0-100) or decimal (0-1)
                    sample_score = df['score'].iloc[0] if len(df) > 0 else 0
                    if sample_score <= 1:
                        # Score is in decimal format, convert to percentage
                        df['score'] = df['score'] * 100
                    # If score > 1, it's already in percentage format, don't multiply
                    df['score'] = df['score'].round(2)  # Round to 2 decimal places
                
                # Format the date column to show May dates clearly
                df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                
                # Rename columns for display
                df = df.rename(columns={'date': 'Date', 'score': 'CBBI Score'})
                
                # Display the table
                st.dataframe(df, use_container_width=True)
                
                st.info("This data is automatically collected and stored daily at 6 AM Stockholm time.")
            else:
                st.warning("No daily CBBI score history is available yet. Data will accumulate as the scheduler collects daily readings.")
                
        with tab2:
            # Create the chart with historical data from the CBBI module
            if 'history' in data['cbbi'] and data['cbbi']['history']:
                history = data['cbbi']['history']
                dates = [item['date'] for item in history]
                # Handle different possible key names for the score
                scores = []
                btc_prices = []
                for item in history:
                    if 'score' in item:
                        # Check if score is already in percentage format (0-100) or decimal (0-1)
                        score_value = item['score']
                        if score_value > 1:
                            scores.append(score_value)  # Already in percentage format
                        else:
                            scores.append(score_value * 100)  # Convert decimal to percentage
                    elif 'cbbi' in item:
                        score_value = item['cbbi']
                        if score_value > 1:
                            scores.append(score_value)  # Already in percentage format
                        else:
                            scores.append(score_value * 100)  # Convert decimal to percentage
                    else:
                        scores.append(0)  # fallback
                    
                    if 'btc_price' in item:
                        btc_prices.append(item['btc_price'])
                    else:
                        btc_prices.append(0)  # fallback
                
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
                    y0=80,
                    x1=max(dates),
                    y1=80,
                    line=dict(color="red", width=2, dash="dash")
                )
                
                fig.add_shape(
                    type="line",
                    x0=min(dates),
                    y0=20,
                    x1=max(dates),
                    y1=20,
                    line=dict(color="green", width=2, dash="dash")
                )
                
                # Layout
                fig.update_layout(
                    title="CBBI Score Over Time",
                    xaxis_title="Date",
                    yaxis_title="CBBI Score",
                    height=500,
                    yaxis=dict(
                        range=[0, 100],
                        tickmode="linear",
                        tick0=0,
                        dtick=10
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Historical CBBI data not available.")
        
        with tab3:
            # BTC price vs CBBI chart
            if 'history' in data['cbbi'] and data['cbbi']['history']:
                history = data['cbbi']['history']
                dates = [item['date'] for item in history]
                # Handle different possible key names for the score
                scores = []
                btc_prices = []
                for item in history:
                    if 'score' in item:
                        # Check if score is already in percentage format (0-100) or decimal (0-1)
                        score_value = item['score']
                        if score_value > 1:
                            scores.append(score_value)  # Already in percentage format
                        else:
                            scores.append(score_value * 100)  # Convert decimal to percentage
                    elif 'cbbi' in item:
                        score_value = item['cbbi']
                        if score_value > 1:
                            scores.append(score_value)  # Already in percentage format
                        else:
                            scores.append(score_value * 100)  # Convert decimal to percentage
                    else:
                        scores.append(0)  # fallback
                    
                    if 'btc_price' in item:
                        btc_prices.append(item['btc_price'])
                    else:
                        btc_prices.append(0)  # fallback
                
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
                    range=[0, 100],
                    tickmode="linear",
                    tick0=0,
                    dtick=10
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("Historical BTC price and CBBI data not available.")
        
        with tab4:
            st.subheader("Official CBBI Chart from Colin Talks Crypto")
            
            # Embed the official CBBI chart from the website
            components.iframe(
                src="https://colintalkscrypto.com/cbbi/",
                height=600,
                scrolling=True
            )
            
            # Attribution moved to the bottom
            st.markdown("*Source: [Colin Talks Crypto Bitcoin Bull Run Index](https://colintalkscrypto.com/cbbi/)*")
            
            # The explanatory text moved to the bottom per user request
            st.markdown("""
            #### About CBBI
            
            The Colin Talks Crypto Bitcoin Bull Run Index combines multiple indicators to estimate the current 
            market cycle position. The CBBI chart represents a normalized score from 0 to 100, where:
            
            - Values close to 100 indicate potential market tops (typically above 80)
            - Values close to 0 indicate potential market bottoms (typically below 20)
            - Values in between suggest the market is in transition
            """)
            
            # Add attribution and explanation
            st.info("The official CBBI combines 8 different indicators to create a comprehensive view of the market cycle.")
        
        # Analysis
        st.subheader("Current Analysis")
        current_score_display = int(score*100) if score else 0
        
        if score > 0.8:
            st.error(f"⚠️ CBBI Score of {current_score_display} indicates increasing market optimism. Historically, scores above 80 have been seen near market tops.")
        elif score > 0.6:
            st.warning(f"🔍 CBBI Score of {current_score_display} shows increasing market optimism. Consider taking partial profits if the trend continues.")
        elif score < 0.3:
            st.success(f"✅ CBBI Score of {current_score_display} suggests we're in mid-cycle. Historically, scores below 30 are favorable for long-term entry.")
        else:
            st.info(f"🔄 CBBI Score of {current_score_display} is in the neutral range. The market is neither in fear nor greed territory.")
    else:
        st.warning("CBBI data not available. Please update the data.")
        
    # Add explanatory text at the bottom of the page
    st.markdown("---")
    st.subheader("About CBBI Score")
    st.markdown("""
    The CBBI (Colin Talks Crypto Bitcoin Index) Score combines multiple technical indicators to create a single metric for estimating Bitcoin market tops.
    It includes indicators like Pi Cycle, Puell Multiple, 2-Year MA Multiplier, and others.
    
    CBBI score ranges from 0 to 100:
    - Score > 80: Potential market top, consider reducing exposure
    - Score 60-80: Caution zone, monitor closely
    - Score < 60: Accumulation phase, favorable for long-term entry
    
    Values closer to 100 suggest market euphoria and potential tops, while values closer to 0 suggest bear markets and accumulation opportunities.
    
    The CBBI is a useful tool for:
    - Identifying potential market tops and bottoms
    - Gauging overall market sentiment
    - Supporting longer-term investment decisions
    - Creating a combined view across multiple indicators
    """)

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
