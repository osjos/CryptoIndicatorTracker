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

def get_halving_data(from_database=None):
    """
    Track Bitcoin halving cycles and project the 520-day post-halving range.
    Historically, Bitcoin has reached cycle tops approximately 12-18 months after halving events.
    
    Args:
        from_database: Optional database data to use instead of fetching new data
        
    Returns:
        Dictionary containing halving cycle data
    """
    try:
        # If database data is provided, use it instead of recalculating
        if from_database is not None:
            logger.info("Using halving cycle data from database")
            return from_database
            
        logger.info("Calculating Bitcoin halving cycle data")
        
        # Bitcoin halving dates (historical and projected)
        halving_dates = [
            '2012-11-28',  # First halving
            '2016-07-09',  # Second halving
            '2020-05-11',  # Third halving
            '2024-04-20',  # Fourth halving (projected)
        ]
        
        # Current date
        current_date = datetime.now()
        
        # Find the most recent halving
        last_halving = None
        for date in halving_dates:
            halving_date = datetime.strptime(date, '%Y-%m-%d')
            if halving_date <= current_date:
                last_halving = date
        
        # If we have a recent halving, calculate days since
        if last_halving:
            last_halving_date = datetime.strptime(last_halving, '%Y-%m-%d')
            days_since_halving = (current_date - last_halving_date).days
            
            # Find the next halving
            next_halving = None
            for date in halving_dates:
                halving_date = datetime.strptime(date, '%Y-%m-%d')
                if halving_date > current_date:
                    next_halving = date
                    break
            
            # If next halving is known, calculate days until
            if next_halving:
                next_halving_date = datetime.strptime(next_halving, '%Y-%m-%d')
                days_until_next_halving = (next_halving_date - current_date).days
            else:
                # If not in dataset, estimate 4 years after the last halving
                next_halving_date = last_halving_date + timedelta(days=4*365)
                next_halving = next_halving_date.strftime('%Y-%m-%d')
                days_until_next_halving = (next_halving_date - current_date).days
            
            # Calculate projected top date (520 days after halving)
            projected_top_date = last_halving_date + timedelta(days=520)
            days_until_projected_top = (projected_top_date - current_date).days
            
            # Response data
            response_data = {
                'last_halving_date': last_halving,
                'days_since_halving': days_since_halving,
                'next_halving_date': next_halving,
                'days_until_next_halving': days_until_next_halving,
                'projected_top_date': projected_top_date.strftime('%Y-%m-%d'),
                'days_until_projected_top': days_until_projected_top
            }
            
            # Fetch historical Bitcoin price data
            # First get data for the current cycle
            current_cycle_start = last_halving_date - timedelta(days=30)  # Include some pre-halving data
            btc_current = yf.download('BTC-USD', start=current_cycle_start, end=current_date)
            
            # Align on halving date
            current_cycle_data = {
                'halving_date': last_halving,
                'normalized_prices': []
            }
            
            if not btc_current.empty:
                # Find the price on halving day (or closest day)
                halving_day_price = None
                closest_date = None
                min_days_diff = float('inf')
                
                for date in btc_current.index:
                    days_diff = abs((date - last_halving_date).days)
                    if days_diff < min_days_diff:
                        min_days_diff = days_diff
                        closest_date = date
                
                if closest_date is not None:
                    halving_day_price = btc_current.loc[closest_date, 'Close']
                    
                    # Normalize prices to 100 at halving day
                    normalized_prices = (btc_current['Close'] / halving_day_price * 100).tolist()
                    current_cycle_data['normalized_prices'] = normalized_prices
            
            response_data['current_cycle'] = current_cycle_data
            
            # Get data for previous cycles
            previous_cycles = []
            
            for i in range(len(halving_dates) - 2):  # Skip the latest halving and projected halving
                cycle_start = datetime.strptime(halving_dates[i], '%Y-%m-%d')
                cycle_end = datetime.strptime(halving_dates[i+1], '%Y-%m-%d')
                
                # Get data for this cycle
                btc_cycle = yf.download('BTC-USD', start=cycle_start, end=cycle_end)
                
                if not btc_cycle.empty:
                    # Find the price on halving day
                    halving_day_price = None
                    closest_date = None
                    min_days_diff = float('inf')
                    
                    for date in btc_cycle.index:
                        days_diff = abs((date - cycle_start).days)
                        if days_diff < min_days_diff:
                            min_days_diff = days_diff
                            closest_date = date
                    
                    if closest_date is not None:
                        halving_day_price = btc_cycle.loc[closest_date, 'Close']
                        
                        # Normalize prices to 100 at halving day
                        normalized_prices = (btc_cycle['Close'] / halving_day_price * 100).tolist()
                        
                        previous_cycles.append({
                            'halving_date': halving_dates[i],
                            'next_halving': halving_dates[i+1],
                            'normalized_prices': normalized_prices
                        })
            
            response_data['previous_cycles'] = previous_cycles
            
            logger.info("Halving cycle data calculated successfully")
            return response_data
        else:
            logger.error("Could not determine the most recent Bitcoin halving date")
            return None
            
    except Exception as e:
        logger.error(f"Error in get_halving_data: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the function
    data = get_halving_data()
    print(json.dumps(data, indent=2))
