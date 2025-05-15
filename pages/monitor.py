
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
        
        # Get latest update status for each indicator
        cursor.execute("""
            WITH RankedUpdates AS (
                SELECT 
                    indicator,
                    status,
                    timestamp,
                    message,
                    ROW_NUMBER() OVER (PARTITION BY indicator ORDER BY timestamp DESC) as rn
                FROM indicator_updates
            )
            SELECT indicator, status, timestamp, message
            FROM RankedUpdates
            WHERE rn = 1
            ORDER BY timestamp DESC
        """)
        updates = cursor.fetchall()
        
        # Get latest entries for each indicator
        data = {
            'MAG7 vs BTC': cursor.execute("SELECT date, data FROM mag7_btc ORDER BY id DESC LIMIT 1").fetchone(),
            'Pi Cycle': cursor.execute("SELECT date, data FROM pi_cycle ORDER BY id DESC LIMIT 1").fetchone(),
            'Coinbase Rank': cursor.execute("SELECT date, data FROM coinbase_rank ORDER BY id DESC LIMIT 1").fetchone(),
            'CBBI Score': cursor.execute("SELECT date, score, timestamp FROM daily_cbbi_scores ORDER BY id DESC LIMIT 1").fetchone(),
            'Halving Cycle': cursor.execute("SELECT date, data FROM halving ORDER BY id DESC LIMIT 1").fetchone()
        }
        
        conn.close()
        return data, updates
    except Exception as e:
        st.error(f"Error accessing database: {str(e)}")
        return None, None

# Get the data
monitor_data, updates = get_monitor_data()

if monitor_data and updates:
    # Create status table
    status_data = []
    
    # Process updates into status data
    update_dict = {update[0]: update for update in updates}
    
    for indicator, data in monitor_data.items():
        update = update_dict.get(indicator)
        
        if update:
            indicator, status, timestamp, message = update
            status_entry = {
                'Indicator': indicator,
                'Last Update': timestamp,
                'Status': status,
                'Value': 'Available' if status == 'Success' else (message or 'N/A')
            }
            
            # Special handling for CBBI
            if indicator == 'CBBI Score' and data:
                date, score, _ = data
                status_entry['Value'] = f"{score * 100:.1f}" if score is not None else 'N/A'
                if score == 0.76:
                    status_entry['Status'] = 'Using fixed value (0.76)'
            
            status_data.append(status_entry)
    
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
    styled_df = df.style.map(color_status, subset=['Status'])
    
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
