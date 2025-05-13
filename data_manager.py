#!/usr/bin/env python

import sqlite3
import json
from datetime import datetime
import logging
import os

# Import data functions
from utils.mag7_btc import get_mag7_btc_data
from utils.pi_cycle import get_pi_cycle_data
from utils.app_store import get_coinbase_ranking
from utils.cbbi import get_cbbi_data
from utils.halving_tracker import get_halving_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define database file path
DB_PATH = "crypto_tracker.db"

def init_database():
    """
    Initialize the SQLite database and create tables if they don't exist.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create tables for each data type
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mag7_btc (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            data TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pi_cycle (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            data TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS coinbase_rank (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            data TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cbbi (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            data TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS halving (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            data TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def update_database():
    """
    Update all data sources in the database.
    """
    try:
        # Initialize database if it doesn't exist
        if not os.path.exists(DB_PATH):
            init_database()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Current date for all updates
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Update MAG7-BTC data
        mag7_btc_data = get_mag7_btc_data()
        if mag7_btc_data:
            cursor.execute(
                "INSERT OR REPLACE INTO mag7_btc (date, data) VALUES (?, ?)",
                (current_date, json.dumps(mag7_btc_data))
            )
        
        # Update Pi Cycle data
        pi_cycle_data = get_pi_cycle_data()
        if pi_cycle_data:
            cursor.execute(
                "INSERT OR REPLACE INTO pi_cycle (date, data) VALUES (?, ?)",
                (current_date, json.dumps(pi_cycle_data))
            )
        
        # Update Coinbase ranking data
        coinbase_data = get_coinbase_ranking()
        if coinbase_data:
            cursor.execute(
                "INSERT OR REPLACE INTO coinbase_rank (date, data) VALUES (?, ?)",
                (current_date, json.dumps(coinbase_data))
            )
        
        # Update CBBI data
        cbbi_data = get_cbbi_data()
        if cbbi_data:
            cursor.execute(
                "INSERT OR REPLACE INTO cbbi (date, data) VALUES (?, ?)",
                (current_date, json.dumps(cbbi_data))
            )
        
        # Update halving cycle data
        halving_data = get_halving_data()
        if halving_data:
            cursor.execute(
                "INSERT OR REPLACE INTO halving (date, data) VALUES (?, ?)",
                (current_date, json.dumps(halving_data))
            )
        
        conn.commit()
        conn.close()
        logger.info("Database updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
        return False

def get_historical_coinbase_rankings():
    """
    Retrieve all historical Coinbase app ranking data from the database.
    
    Returns:
        List of dictionaries containing date and rank for each recorded entry
    """
    try:
        # Check if database exists
        if not os.path.exists(DB_PATH):
            logger.info("Database does not exist for historical coinbase data")
            return []
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all coinbase ranking data
        cursor.execute("SELECT date, data FROM coinbase_rank ORDER BY date ASC")
        results = cursor.fetchall()
        
        historical_data = []
        
        if results:
            for date_str, data_json in results:
                data = json.loads(data_json)
                rank = data.get('rank')
                
                # Skip entries with no rank
                if rank is None:
                    continue
                    
                # Convert string ranks like "200+" to integer 201 for consistency in graphs
                if isinstance(rank, str) and "+" in rank:
                    rank_value = 201  # Just above 200 for plotting purposes
                else:
                    rank_value = rank
                
                historical_data.append({
                    'date': date_str,
                    'rank': rank_value
                })
        
        conn.close()
        return historical_data
    except Exception as e:
        logger.error(f"Error retrieving historical coinbase rankings: {str(e)}")
        return []

def get_latest_data():
    """
    Get the latest data for all indicators from the database.
    If database doesn't exist or is empty, fetch fresh data.
    
    Returns:
        Dictionary containing the latest data for all indicators
    """
    try:
        # Check if database exists
        if not os.path.exists(DB_PATH):
            logger.info("Database does not exist, creating and updating...")
            update_database()
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Container for all data
        data = {}
        
        # Get latest MAG7-BTC data
        cursor.execute("SELECT data FROM mag7_btc ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            data['mag7_btc'] = json.loads(result[0])
        else:
            logger.info("No MAG7-BTC data in database, fetching fresh data...")
            data['mag7_btc'] = get_mag7_btc_data()
        
        # Get latest Pi Cycle data
        cursor.execute("SELECT data FROM pi_cycle ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            data['pi_cycle'] = json.loads(result[0])
        else:
            logger.info("No Pi Cycle data in database, fetching fresh data...")
            data['pi_cycle'] = get_pi_cycle_data()
        
        # Get latest Coinbase ranking data
        cursor.execute("SELECT data FROM coinbase_rank ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            data['coinbase_rank'] = json.loads(result[0])
        else:
            logger.info("No Coinbase ranking data in database, fetching fresh data...")
            data['coinbase_rank'] = get_coinbase_ranking()
        
        # Get latest CBBI data
        cursor.execute("SELECT data FROM cbbi ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            data['cbbi'] = json.loads(result[0])
        else:
            logger.info("No CBBI data in database, fetching fresh data...")
            data['cbbi'] = get_cbbi_data()
        
        # Get latest halving cycle data
        cursor.execute("SELECT data FROM halving ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            data['halving'] = json.loads(result[0])
        else:
            logger.info("No halving cycle data in database, fetching fresh data...")
            data['halving'] = get_halving_data()
        
        conn.close()
        logger.info("Retrieved latest data for all indicators")
        return data
    except Exception as e:
        logger.error(f"Error retrieving latest data: {str(e)}")
        # If database access fails, try to get fresh data
        logger.info("Attempting to fetch fresh data for all indicators...")
        
        data = {
            'mag7_btc': get_mag7_btc_data(),
            'pi_cycle': get_pi_cycle_data(),
            'coinbase_rank': get_coinbase_ranking(),
            'cbbi': get_cbbi_data(),
            'halving': get_halving_data()
        }
        
        return data

if __name__ == "__main__":
    # Test the functions
    init_database()
    update_database()
    data = get_latest_data()
    for key in data:
        print(f"{key}: {type(data[key])}")
