#!/usr/bin/env python

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
import numpy as np
from bs4 import BeautifulSoup
import yfinance as yf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cbbi_data(from_database=None):
    """
    Get CBBI (Colin Talks Crypto Bitcoin Index) score.
    This is a combination of multiple indicators to estimate Bitcoin market tops.
    
    Args:
        from_database: Optional database data to use instead of fetching new data
        
    Returns:
        Dictionary containing CBBI score data
    """
    try:
        # If database data is provided, use it instead of recalculating
        if from_database is not None:
            logger.info("Using CBBI data from database")
            return from_database
            
        logger.info("Fetching CBBI score data")
        
        # Try to scrape from the official source
        try:
            url = "https://colintalkscrypto.com/cbbi/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                # Parse HTML to extract CBBI score
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # This is a simplified implementation - actual scraping would depend on the site structure
                # Look for the score element
                score_element = soup.find('div', {'id': 'cbbi-score'})  # This ID is hypothetical
                
                if score_element:
                    cbbi_score = float(score_element.text.strip())
                    logger.info(f"Successfully scraped CBBI score: {cbbi_score}")
                else:
                    # If scraping fails, calculate an approximation
                    logger.warning("Could not scrape CBBI score, calculating approximation")
                    cbbi_score = calculate_approximate_cbbi()
            else:
                logger.warning(f"Failed to fetch CBBI data: {response.status_code}")
                cbbi_score = calculate_approximate_cbbi()
                
        except Exception as e:
            logger.warning(f"Error scraping CBBI data: {str(e)}")
            cbbi_score = calculate_approximate_cbbi()
        
        # Current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Fetch current BTC price for context
        btc_data = yf.download('BTC-USD', period='1d')
        current_price = btc_data['Close'].iloc[-1] if not btc_data.empty else None
        
        # Build response
        response_data = {
            'score': cbbi_score,
            'last_updated': current_date,
            'btc_price': current_price,
            'history': []
        }
        
        # Simulate historical data for demonstration
        # In a real implementation, this would come from a database
        start_date = datetime.now() - timedelta(days=365*2)  # 2 years of data
        dates = pd.date_range(start=start_date, end=datetime.now(), freq='D')
        
        # Get historical BTC prices
        btc_historical = yf.download('BTC-USD', start=start_date, end=datetime.now())
        
        # Simulate CBBI scores based on BTC price movements
        # This is a simplified model for demonstration
        history = []
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            
            if date_str in btc_historical.index.strftime('%Y-%m-%d').tolist():
                idx = btc_historical.index.strftime('%Y-%m-%d').tolist().index(date_str)
                btc_price = btc_historical['Close'].iloc[idx]
                
                # Calculate a simulated CBBI score
                # This is just a simple model for demonstration
                # Higher prices tend to have higher CBBI scores
                price_max = btc_historical['Close'].max()
                price_min = btc_historical['Close'].min()
                price_range = price_max - price_min
                
                if price_range > 0:
                    # Base score on normalized price position
                    base_score = (btc_price - price_min) / price_range
                    
                    # Add some cyclical variation
                    days_since_start = (date - start_date).days
                    cycle_component = 0.15 * np.sin(days_since_start / 30 * 2 * np.pi)
                    
                    # Combine components
                    simulated_score = min(1.0, max(0.0, base_score * 0.7 + cycle_component + 0.1))
                    
                    history.append({
                        'date': date_str,
                        'score': simulated_score,
                        'btc_price': btc_price
                    })
        
        response_data['history'] = history
        
        logger.info("CBBI data processed successfully")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in get_cbbi_data: {str(e)}")
        return None

def calculate_approximate_cbbi():
    """
    Calculate an approximation of the CBBI score based on available data.
    This is a simplified implementation that attempts to recreate the CBBI methodology.
    
    Returns:
        Approximate CBBI score between 0 and 1
    """
    try:
        logger.info("Calculating approximate CBBI score")
        
        # Fetch BTC data for calculations
        btc_data = yf.download('BTC-USD', period='2y')
        
        # CBBI considers several indicators:
        # 1. Pi Cycle Top Indicator
        # 2. 2-Year MA Multiplier
        # 3. Puell Multiple
        # 4. Golden Ratio Multiplier
        # 5. Bitcoin Price vs 20 Week & 21 Week EMA
        # 6. Bitcoin Logarithmic Regression
        # 7. Bitcoin Trolololo 
        # 8. RHODL Ratio
        
        # Let's calculate a few of these as an approximation
        
        # Set default scores in case calculations fail
        pi_cycle_score = 0.5
        ma_multiplier_score = 0.5
        ema_score = 0.5
        log_reg_score = 0.5
        
        # Calculate individual components with error handling for each
        try:
            # Pi Cycle Top - needs 350 days of data
            if len(btc_data) >= 350:
                btc_data['MA111'] = btc_data['Close'].rolling(window=111).mean()
                btc_data['MA350'] = btc_data['Close'].rolling(window=350).mean()
                btc_data['MA350x2'] = btc_data['MA350'] * 2
                
                # Check if we have valid values at the end of the dataframe
                last_ma111 = btc_data['MA111'].iloc[-1]
                last_ma350x2 = btc_data['MA350x2'].iloc[-1]
                
                if pd.notna(last_ma111) and pd.notna(last_ma350x2) and last_ma350x2 > 0:
                    pi_ratio = last_ma111 / last_ma350x2
                    # Normalize between 0 and 1 (1 is when MA111 = MA350x2)
                    pi_cycle_score = min(1.0, max(0.0, pi_ratio))
            else:
                logger.warning("Not enough data for Pi Cycle calculation")
        except Exception as e:
            logger.warning(f"Error in Pi Cycle calculation: {e}")
        
        try:
            # 2-Year MA Multiplier - needs 730 days of data
            if len(btc_data) >= 730:
                btc_data['MA730'] = btc_data['Close'].rolling(window=730).mean()
                
                last_close = btc_data['Close'].iloc[-1]
                last_ma730 = btc_data['MA730'].iloc[-1]
                
                if pd.notna(last_close) and pd.notna(last_ma730) and last_ma730 > 0:
                    current_multiple = last_close / last_ma730
                    # Normalize between 0 and 1 (5x multiple is close to 1.0)
                    ma_multiplier_score = min(1.0, max(0.0, (current_multiple - 1) / 4))
            else:
                logger.warning("Not enough data for 2-Year MA Multiplier calculation")
        except Exception as e:
            logger.warning(f"Error in MA Multiplier calculation: {e}")
        
        try:
            # Price vs 20 Week & 21 Week EMA - needs at least 150 days
            if len(btc_data) >= 150:
                btc_data['EMA20W'] = btc_data['Close'].ewm(span=140).mean()  # 20 weeks ≈ 140 days
                btc_data['EMA21W'] = btc_data['Close'].ewm(span=147).mean()  # 21 weeks ≈ 147 days
                
                last_close = btc_data['Close'].iloc[-1]
                last_ema20w = btc_data['EMA20W'].iloc[-1]
                last_ema21w = btc_data['EMA21W'].iloc[-1]
                
                if (pd.notna(last_close) and pd.notna(last_ema20w) and 
                    pd.notna(last_ema21w) and (last_ema20w + last_ema21w) > 0):
                    
                    ema_avg = (last_ema20w + last_ema21w) / 2
                    ema_ratio = last_close / ema_avg
                    # Normalize between 0 and 1 (2x multiple is close to 1.0)
                    ema_score = min(1.0, max(0.0, (ema_ratio - 1) / 1))
            else:
                logger.warning("Not enough data for EMA calculation")
        except Exception as e:
            logger.warning(f"Error in EMA calculation: {e}")
        
        try:
            # Simplistic logarithmic regression - needs sufficient data points
            if len(btc_data) > 60:  # At least 60 days of data
                # Calculate log prices, avoiding NaN/Inf from non-positive values
                btc_data['LogPrice'] = np.log10(btc_data['Close'].replace(0, np.nan))
                days = np.arange(len(btc_data))
                
                # Create valid mask, convert to numpy to avoid Series truth value ambiguity
                mask = ~np.isnan(btc_data['LogPrice'].values)
                valid_days = days[mask]
                valid_log_prices = btc_data['LogPrice'].values[mask]
                
                if len(valid_days) > 30:  # Ensure enough valid points
                    coeffs = np.polyfit(valid_days, valid_log_prices, 1)
                    log_trend = 10 ** (coeffs[0] * days[-1] + coeffs[1])
                    
                    last_close = btc_data['Close'].iloc[-1]
                    
                    if pd.notna(last_close) and pd.notna(log_trend) and log_trend > 0:
                        current_deviation = last_close / log_trend
                        # Normalize between 0 and 1 (3x deviation is close to 1.0)
                        log_reg_score = min(1.0, max(0.0, (current_deviation - 1) / 2))
            else:
                logger.warning("Not enough data for logarithmic regression")
        except Exception as e:
            logger.warning(f"Error in log regression calculation: {e}")
        
        # Average the available indicators for an approximate CBBI score
        # The original CBBI uses more indicators and a more complex methodology
        scores = [pi_cycle_score, ma_multiplier_score, ema_score, log_reg_score]
        approximate_cbbi = sum(scores) / len(scores)
        
        logger.info(f"Calculated approximate CBBI score: {approximate_cbbi:.4f}")
        return approximate_cbbi
        
    except Exception as e:
        logger.error(f"Error calculating approximate CBBI: {str(e)}")
        # Return a default mid-range value if calculation fails
        return 0.5

if __name__ == "__main__":
    # Test the function
    data = get_cbbi_data()
    print(json.dumps(data, indent=2))
