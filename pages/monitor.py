
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Indicator Monitor",
    page_icon="🔍",
    layout="wide"
)

st.title("Indicator Status Monitor")

# Connect to database
def get_monitor_data():
    try:
        conn = sqlite3.connect('crypto_tracker.db')
        cursor = conn.cursor()
        
        # Get latest entries for each indicator
        data = {
            'MAG7 vs BTC': cursor.execute("SELECT date, data FROM mag7_btc ORDER BY id DESC LIMIT 1").fetchone(),
            'Pi Cycle': cursor.execute("SELECT date, data FROM pi_cycle ORDER BY id DESC LIMIT 1").fetchone(),
            'Coinbase Rank': cursor.execute("SELECT date, data FROM coinbase_rank ORDER BY id DESC LIMIT 1").fetchone(),
            'CBBI Score': cursor.execute("SELECT date, score, timestamp FROM daily_cbbi_scores ORDER BY id DESC LIMIT 1").fetchone(),
            'Halving Cycle': cursor.execute("SELECT date, data FROM halving ORDER BY id DESC LIMIT 1").fetchone()
        }
        
        conn.close()
        return data
    except Exception as e:
        st.error(f"Error accessing database: {str(e)}")
        return None

# Get the data
monitor_data = get_monitor_data()

if monitor_data:
    # Create status table
    status_data = []
    
    for indicator, data in monitor_data.items():
        if data:
            if indicator == 'CBBI Score':
                # Special handling for CBBI which has a different structure
                date, score, timestamp = data
                status = {
                    'Indicator': indicator,
                    'Last Update': timestamp,
                    'Status': 'Using fixed value (0.76)' if score == 0.76 else 'Success',
                    'Value': f"{score * 100:.1f}" if score is not None else 'N/A'
                }
            else:
                date, data_str = data
                status = {
                    'Indicator': indicator,
                    'Last Update': date,
                    'Status': 'Success',
                    'Value': 'Available'
                }
        else:
            status = {
                'Indicator': indicator,
                'Last Update': 'Never',
                'Status': 'Failed',
                'Value': 'N/A'
            }
        status_data.append(status)
    
    # Convert to DataFrame for display
    df = pd.DataFrame(status_data)
    
    # Style the dataframe
    def color_status(val):
        if val == 'Success':
            return 'background-color: #90EE90'
        elif 'fixed value' in val.lower():
            return 'background-color: #FFE5B4'
        else:
            return 'background-color: #FFB6C1'
    
    # Apply styling
    styled_df = df.style.applymap(color_status, subset=['Status'])
    
    # Display the table
    st.dataframe(styled_df, use_container_width=True)
    
    # Add explanations
    st.markdown("""
    ### Status Explanations:
    - 🟢 **Success**: Data was fetched and updated successfully
    - 🟡 **Using fixed value**: Could not fetch live data, using fallback value
    - 🔴 **Failed**: Data update failed
    
    ### Update Schedule:
    - All indicators are updated daily at 6 AM Stockholm time
    - Manual updates can be triggered from the main dashboard
    """)
else:
    st.error("Could not retrieve monitoring data. Database may be unavailable.")
