#!/usr/bin/env python

import sqlite3
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define database file path
DB_PATH = "crypto_tracker.db"

def populate_test_cbbi_data():
    """
    Populate the daily_cbbi_scores table with test data points for the past 30 days.
    This is to simulate having historical data for development purposes.
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_cbbi_scores'")
        if not cursor.fetchone():
            logger.error("daily_cbbi_scores table does not exist")
            return False

        # Start with today's date and go back 30 days
        today = datetime.now()
        
        # Test data points - simulate a trend
        cbbi_values = [
            0.76, 0.75, 0.74, 0.74, 0.73, 0.72, 0.71, 0.70, 0.70, 0.69,
            0.68, 0.67, 0.67, 0.66, 0.65, 0.64, 0.64, 0.63, 0.62, 0.61,
            0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.67, 0.69, 0.72, 0.76
        ]  # Note: Last value is 0.76 to match the official website

        # Insert data points for the past 30 days
        for i in range(30):
            date = today - timedelta(days=29-i)  # Start with 29 days ago
            date_str = date.strftime('%Y-%m-%d')
            timestamp = date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Get the CBBI value for this day
            cbbi_score = cbbi_values[i]
            
            # Check if we already have this date in the database
            cursor.execute("SELECT id FROM daily_cbbi_scores WHERE date = ?", (date_str,))
            existing_entry = cursor.fetchone()
            
            if existing_entry:
                # Update existing entry
                cursor.execute(
                    "UPDATE daily_cbbi_scores SET score = ?, timestamp = ? WHERE date = ?",
                    (cbbi_score, timestamp, date_str)
                )
                logger.info(f"Updated test CBBI score for {date_str}: {cbbi_score}")
            else:
                # Insert new entry
                cursor.execute(
                    "INSERT INTO daily_cbbi_scores (date, score, timestamp) VALUES (?, ?, ?)",
                    (date_str, cbbi_score, timestamp)
                )
                logger.info(f"Inserted test CBBI score for {date_str}: {cbbi_score}")
        
        conn.commit()
        conn.close()
        logger.info("Test CBBI data populated successfully")
        return True
    except Exception as e:
        logger.error(f"Error populating test CBBI data: {str(e)}")
        return False

if __name__ == "__main__":
    populate_test_cbbi_data()