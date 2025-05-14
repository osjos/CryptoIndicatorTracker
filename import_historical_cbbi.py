import sqlite3
import logging
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def import_historical_cbbi_data():
    """
    Import manually extracted historical CBBI scores.
    This replaces any simulated data with actual historical values.
    """
    try:
        # Connect to the database
        conn = sqlite3.connect('crypto_tracker.db')
        cursor = conn.cursor()
        
        # First, clear any existing records in this date range
        # to avoid duplicates
        cursor.execute("""
            DELETE FROM daily_cbbi_scores 
            WHERE date BETWEEN '2025-04-01' AND '2025-05-14'
        """)
        
        # Historical data in format YYYYMMDD and score (as percentage)
        historical_data = [
            ("20250401", 72),
            ("20250402", 74),
            ("20250403", 74),
            ("20250404", 72),
            ("20250405", 73),
            ("20250406", 73),
            ("20250407", 73),
            ("20250408", 74),
            ("20250409", 75),
            ("20250410", 76),
            ("20250411", 76),
            ("20250412", 76),
            ("20250413", 75),
            # Continue with current data we've collected since the 14th
            ("20250414", 76),
        ]
        
        # Current timestamp (for all records)
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert each historical record
        for date_str, score in historical_data:
            # Convert the date format from YYYYMMDD to YYYY-MM-DD
            date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
            
            # Convert percentage score to decimal (0-1 range)
            decimal_score = score / 100.0
            
            # Insert the record
            cursor.execute(
                "INSERT INTO daily_cbbi_scores (date, score, timestamp) VALUES (?, ?, ?)",
                (date, decimal_score, current_timestamp)
            )
            
            logger.info(f"Imported historical CBBI score for {date}: {score}%")
        
        # Commit and close
        conn.commit()
        conn.close()
        
        logger.info("Historical CBBI data import completed successfully")
        
    except Exception as e:
        logger.error(f"Error importing historical CBBI data: {str(e)}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import_historical_cbbi_data()