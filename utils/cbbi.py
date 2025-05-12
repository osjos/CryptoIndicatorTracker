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
        
        # Pi Cycle Top
        btc_data['MA111'] = btc_data['Close'].rolling(window=111).mean()
        btc_data['MA350'] = btc_data['Close'].rolling(window=350).mean()
        btc_data['MA350x2'] = btc_data['MA350'] * 2
        btc_data['Pi_Ratio'] = btc_data['MA111'] / btc_data['MA350x2']
        # Handle Series ambiguity by explicitly checking if we have valid data
        if not btc_data['Pi_Ratio'].empty and not pd.isna(btc_data['Pi_Ratio'].iloc[-1]):
            pi_cycle_score = min(1.0, float(btc_data['Pi_Ratio'].iloc[-1]))
        else:
            pi_cycle_score = 0.5  # Default mid-range value
        
        # 2-Year MA Multiplier
        btc_data['MA730'] = btc_data['Close'].rolling(window=730).mean()
        # Handle potential division by zero or NaN values
        if not btc_data.empty and not pd.isna(btc_data['MA730'].iloc[-1]) and btc_data['MA730'].iloc[-1] > 0:
            current_multiple = btc_data['Close'].iloc[-1] / btc_data['MA730'].iloc[-1]
            # Normalize between 0 and 1 (5x multiple is close to 1.0)
            ma_multiplier_score = min(1.0, max(0.0, (current_multiple - 1) / 4))
        else:
            ma_multiplier_score = 0.5  # Default mid-range value
        
        # Price vs 20 Week & 21 Week EMA
        btc_data['EMA20W'] = btc_data['Close'].ewm(span=140).mean()  # 20 weeks ≈ 140 days
        btc_data['EMA21W'] = btc_data['Close'].ewm(span=147).mean()  # 21 weeks ≈ 147 days
        
        # Handle potential division by zero or NaN values
        if (not btc_data.empty and 
            not pd.isna(btc_data['EMA20W'].iloc[-1]) and 
            not pd.isna(btc_data['EMA21W'].iloc[-1]) and
            (btc_data['EMA20W'].iloc[-1] + btc_data['EMA21W'].iloc[-1]) > 0):
            
            ema_avg = (btc_data['EMA20W'].iloc[-1] + btc_data['EMA21W'].iloc[-1]) / 2
            ema_ratio = btc_data['Close'].iloc[-1] / ema_avg
            # Normalize between 0 and 1 (2x multiple is close to 1.0)
            ema_score = min(1.0, max(0.0, (ema_ratio - 1) / 1))
        else:
            ema_score = 0.5  # Default mid-range value
        
        # Simplistic logarithmic regression
        log_reg_score = 0.5  # Default value
        
        if not btc_data.empty and len(btc_data) > 2:  # Need at least 2 points for a line
            try:
                btc_data['LogPrice'] = np.log10(btc_data['Close'])
                days = np.arange(len(btc_data))
                
                # Remove NaN values before fitting
                valid_idx = ~pd.isna(btc_data['LogPrice'])
                if sum(valid_idx) > 2:  # At least 2 valid points needed
                    valid_days = days[valid_idx]
                    valid_log_prices = btc_data['LogPrice'][valid_idx]
                    
                    coeffs = np.polyfit(valid_days, valid_log_prices, 1)
                    log_trend = 10 ** (coeffs[0] * days + coeffs[1])
                    
                    if not pd.isna(log_trend[-1]) and log_trend[-1] > 0:
                        current_deviation = btc_data['Close'].iloc[-1] / log_trend[-1]
                        # Normalize between 0 and 1 (3x deviation is close to 1.0)
                        log_reg_score = min(1.0, max(0.0, (current_deviation - 1) / 2))
            except Exception as e:
                logger.warning(f"Error in log regression calculation: {e}")
                # Keep the default value
        
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
