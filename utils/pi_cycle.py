#!/usr/bin/env python

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_pi_cycle_data(from_database=None):
    """
    Calculate the Pi Cycle Top Indicator for Bitcoin.
    This indicator uses the 111-day MA and 350-day MA × 2.
    A crossover of these MAs has historically indicated market tops.
    
    Args:
        from_database: Optional database data to use instead of fetching new data
        
    Returns:
        Dictionary containing the Pi Cycle data
    """
    try:
        # If database data is provided, use it instead of recalculating
        if from_database is not None:
            logger.info("Using Pi Cycle data from database")
            return from_database
            
        logger.info("Calculating Pi Cycle indicator for Bitcoin")
        
        # Define timeframe (4 years of data should be sufficient)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=4*365)  # Need enough data for 350-day MA
        
        # Fetch Bitcoin data
        btc_data = yf.download('BTC-USD', start=start_date, end=end_date)
        
        # Calculate MAs
        btc_data['MA111'] = btc_data['Close'].rolling(window=111).mean()
        btc_data['MA350'] = btc_data['Close'].rolling(window=350).mean()
        btc_data['MA350x2'] = btc_data['MA350'] * 2
        
        # Calculate the ratio (should approach 1.0 at market tops)
        btc_data['Ratio'] = btc_data['MA111'] / btc_data['MA350x2']
        
        # Remove rows with NaN values
        btc_data.dropna(inplace=True)
        
        # Detect crossovers (where MA111 crosses above MA350x2)
        btc_data['Crossover'] = (
            (btc_data['MA111'].shift(1) < btc_data['MA350x2'].shift(1)) & 
            (btc_data['MA111'] >= btc_data['MA350x2'])
        )
        
        # Build response data
        response = {
            'dates': btc_data.index.strftime('%Y-%m-%d').tolist(),
            'btc_price': btc_data['Close'].tolist(),
            'ma111_values': btc_data['MA111'].tolist(),
            'ma350x2_values': btc_data['MA350x2'].tolist(),
            'ratio_values': btc_data['Ratio'].tolist(),
            'current_btc_price': btc_data['Close'].iloc[-1],
            'ma111': btc_data['MA111'].iloc[-1],
            'ma350x2': btc_data['MA350x2'].iloc[-1],
            'ratio': btc_data['Ratio'].iloc[-1]
        }
        
        # Add crossover points
        crossovers = btc_data[btc_data['Crossover'] == True]
        response['crossovers'] = [
            {'date': date.strftime('%Y-%m-%d'), 'price': price}
            for date, price in zip(crossovers.index, crossovers['Close'])
        ]
        
        logger.info("Pi Cycle data calculated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in get_pi_cycle_data: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the function
    data = get_pi_cycle_data()
    print(json.dumps(data, indent=2))
