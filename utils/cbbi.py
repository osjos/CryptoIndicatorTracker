
#!/usr/bin/env python

import requests
import pandas as pd
from datetime import datetime
import json
import logging
import sqlite3
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CBBI_URL = "https://colintalkscrypto.com/cbbi/data/latest.json"

def fetch_cbbi_df() -> pd.DataFrame:
    """Returns daily CBBI dataframe: columns [date, cbbi] (ISO date, float)."""
    r = requests.get(CBBI_URL, timeout=30)
    r.raise_for_status()
    j = r.json()
    s = pd.Series(j.get("Confidence", {}), name="cbbi")
    if s.empty:
        return pd.DataFrame(columns=["date", "cbbi"])
    df = s.to_frame()
    df.index = pd.to_datetime(df.index, utc=True, errors="coerce")
    df = df.dropna().sort_index()
    df = df.reset_index().rename(columns={"index": "date"})
    df["date"] = df["date"].dt.date.astype(str)
    df["cbbi"] = df["cbbi"].astype(float)
    return df

def get_cbbi_data(from_database=None):
    """
    Get CBBI (Colin Talks Crypto Bitcoin Index) score.
    This function now fetches the latest score from the API.

    Args:
        from_database: Optional database data to use instead of fetching new data

    Returns:
        Dictionary containing CBBI score data
    """
    try:
        # Get the latest CBBI data from the API
        df = fetch_cbbi_df()
        
        if df.empty:
            logger.warning("No CBBI data available from API, attempting to get previous value from database")
            # Try to get previous day's value from database
            try:
                conn = sqlite3.connect('crypto_tracker.db')
                cursor = conn.cursor()
                cursor.execute("SELECT score FROM daily_cbbi_scores ORDER BY date DESC LIMIT 1")
                result = cursor.fetchone()
                conn.close()

                if result:
                    cbbi_score = result[0]
                    logger.warning(f"Using previous day's CBBI score as fallback: {cbbi_score}")
                else:
                    logger.error("No previous CBBI score available in database")
                    return None
            except Exception as e:
                logger.error(f"Error fetching previous CBBI score: {str(e)}")
                return None
        else:
            # Get the most recent score from the dataframe
            cbbi_score = df.iloc[-1]['cbbi']
            last_date = df.iloc[-1]['date']
            logger.info(f"Fetched current CBBI score from API: {cbbi_score} (date: {last_date})")

        # Current date
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Build response
        response_data = {
            'score': cbbi_score,
            'last_updated': current_date,
            'history': df.to_dict('records') if not df.empty else []
        }

        logger.info("CBBI data processed successfully")
        return response_data

    except Exception as e:
        logger.error(f"Error in get_cbbi_data: {str(e)}")
        # Fallback to database
        try:
            conn = sqlite3.connect('crypto_tracker.db')
            cursor = conn.cursor()
            cursor.execute("SELECT score FROM daily_cbbi_scores ORDER BY date DESC LIMIT 1")
            result = cursor.fetchone()
            conn.close()

            if result:
                cbbi_score = result[0]
                current_date = datetime.now().strftime('%Y-%m-%d')
                logger.warning(f"Using database fallback CBBI score: {cbbi_score}")
                return {
                    'score': cbbi_score,
                    'last_updated': current_date
                }
        except Exception as db_error:
            logger.error(f"Database fallback also failed: {str(db_error)}")
        
        return None

def scrape_official_cbbi_score():
    """
    Legacy function - now uses the API instead of scraping.
    Returns:
        The current CBBI score as a float between 0 and 1, or None if fetching fails
    """
    try:
        df = fetch_cbbi_df()
        if not df.empty:
            score = df.iloc[-1]['cbbi']
            logger.info(f"Got CBBI score from API: {score}")
            return score
        else:
            logger.warning("No CBBI data available from API")
            return None
    except Exception as e:
        logger.error(f"Error fetching CBBI score from API: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the function
    data = get_cbbi_data()
    print(json.dumps(data, indent=2))
