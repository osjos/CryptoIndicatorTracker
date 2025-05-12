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

def get_mag7_btc_data(from_database=None):
    """
    Get MAG7 vs Bitcoin index data, either from database or by calculating it directly.
    
    Args:
        from_database: Optional database data to use instead of fetching new data
        
    Returns:
        Dictionary containing the MAG7-BTC index data
    """
    try:
        # If database data is provided, use it instead of recalculating
        if from_database is not None:
            logger.info("Using MAG7-BTC data from database")
            return from_database
            
        logger.info("Fetching MAG7-BTC data from Yahoo Finance")
        
        # Define timeframe (4 years of data should be sufficient)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=4*365)
        
        # Define ticker symbols
        tickers = ['BTC-USD', 'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA']
        
        # Fetch data
        data = yf.download(tickers, start=start_date, end=end_date)['Adj Close']
        
        # Handle any missing data
        data.dropna(how='all', inplace=True)
        
        # Filter out data before all stocks/BTC have values
        valid_start_date = data[['BTC-USD', 'TSLA']].dropna().index.min()
        data = data[data.index >= valid_start_date]
        
        # Forward-fill missing values
        data.fillna(method='ffill', inplace=True)
        
        # Normalize prices to start at 100
        normalized_data = data / data.iloc[0] * 100
        
        # Apply weights
        weights = {
            'BTC-USD': 0.5,
            'MSFT': 0.1,
            'AAPL': 0.1,
            'GOOGL': 0.1,
            'AMZN': 0.1,
            'META': 0.05,
            'NVDA': 0.05
        }
        
        # Create the index
        index_data = pd.DataFrame(index=data.index)
        index_data['BTC_Mag7_Index'] = (normalized_data * pd.Series(weights)).sum(axis=1)
        
        # Smooth with a 7-day moving average
        index_data['Smoothed_Index'] = index_data['BTC_Mag7_Index'].rolling(window=7).mean()
        
        # Calculate moving averages
        index_data['MA200'] = index_data['Smoothed_Index'].rolling(window=200).mean()
        index_data['MA150'] = index_data['Smoothed_Index'].rolling(window=150).mean()
        index_data['MA100'] = index_data['Smoothed_Index'].rolling(window=100).mean()
        
        # Calculate EMAs
        index_data['EMA200'] = index_data['Smoothed_Index'].ewm(span=200, adjust=False).mean()
        index_data['EMA150'] = index_data['Smoothed_Index'].ewm(span=150, adjust=False).mean()
        index_data['EMA100'] = index_data['Smoothed_Index'].ewm(span=100, adjust=False).mean()
        
        # Drop rows with NaN in critical columns
        index_data.dropna(subset=['Smoothed_Index'], inplace=True)
        
        # Build response data
        response = {
            'dates': index_data.index.strftime('%Y-%m-%d').tolist(),
            'index_values': index_data['Smoothed_Index'].tolist(),
            'ma200': index_data['MA200'].tolist(),
            'ma150': index_data['MA150'].tolist(),
            'ma100': index_data['MA100'].tolist(),
            'ema200': index_data['EMA200'].tolist(),
            'ema150': index_data['EMA150'].tolist(),
            'ema100': index_data['EMA100'].tolist(),
            'current_value': index_data['Smoothed_Index'].iloc[-1],
            'ma100': index_data['MA100'].iloc[-1],
            'ma200': index_data['MA200'].iloc[-1]
        }
        
        # Add known BTC tops/bottoms
        cycle_tops = ['2017-12-17', '2021-11-10']
        cycle_bottoms = ['2018-12-15', '2022-06-18']
        
        response['tops'] = []
        for top in cycle_tops:
            if top in index_data.index.strftime('%Y-%m-%d').tolist():
                idx = index_data.index.strftime('%Y-%m-%d').tolist().index(top)
                response['tops'].append({
                    'date': top,
                    'value': index_data['BTC_Mag7_Index'].iloc[idx]
                })
        
        response['bottoms'] = []
        for bottom in cycle_bottoms:
            if bottom in index_data.index.strftime('%Y-%m-%d').tolist():
                idx = index_data.index.strftime('%Y-%m-%d').tolist().index(bottom)
                response['bottoms'].append({
                    'date': bottom,
                    'value': index_data['BTC_Mag7_Index'].iloc[idx]
                })
        
        logger.info("MAG7-BTC data processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in get_mag7_btc_data: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the function
    data = get_mag7_btc_data()
    print(json.dumps(data, indent=2))
