#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
import random
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_coinbase_ranking(from_database=None):
    """
    Get Coinbase app ranking from App Store (US).
    Scrapes AppFigures.com for free iPhone apps in the US market.
    
    Args:
        from_database: Optional database data to use instead of fetching new data
        
    Returns:
        Dictionary containing Coinbase app ranking data
    """
    try:
        # If database data is provided, use it instead of fetching new data
        if from_database is not None:
            logger.info("Using Coinbase ranking data from database")
            return from_database
        
        logger.info("Fetching Coinbase app ranking from AppFigures")
        
        # Use AppFigures.com for app ranking data - specifically tracking top free iPhone apps in the US
        url = "https://appfigures.com/top-apps/ios-app-store/united-states/iphone/top-overall"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        coinbase_rank = None
        
        if response.status_code == 200:
            # First try using trafilatura for cleaner text extraction
            try:
                import trafilatura
                downloaded = trafilatura.fetch_url(url)
                content = trafilatura.extract(downloaded)
                
                if content:
                    # Check if "Coinbase" appears in the content
                    if "Coinbase" in content:
                        # Create soup for more structured parsing
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find all app entries
                        app_entries = soup.find_all('div', class_=['app-card', 'app-row', 'app-item'])
                        
                        for i, entry in enumerate(app_entries):
                            # Look for Coinbase in the app name or developer
                            if "Coinbase" in entry.get_text():
                                # AppFigures lists are 0-indexed, so add 1 for rank
                                coinbase_rank = i + 1
                                logger.info(f"Found Coinbase at rank {coinbase_rank}")
                                break
                        
                        # If we didn't find it through structured parsing, try to find rank in context
                        if not coinbase_rank:
                            # Try to find rank near Coinbase mentions
                            import re
                            
                            # Look for patterns like "#123 Coinbase" or "Coinbase #123"
                            rank_patterns = re.findall(r'#(\d+)[^\d]*Coinbase|Coinbase[^\d]*#(\d+)', content)
                            if rank_patterns:
                                for pattern in rank_patterns:
                                    # Each pattern is a tuple with two capture groups
                                    # Check each group to see if it contains a number
                                    for group in pattern:
                                        if group.isdigit():
                                            coinbase_rank = int(group)
                                            logger.info(f"Found Coinbase from text rank: {coinbase_rank}")
                                            break
                    else:
                        logger.info("Coinbase not found in the AppFigures top chart content")
                        
            except ImportError as e:
                logger.warning(f"Trafilatura not available: {str(e)}, falling back to BeautifulSoup parsing")
            
            # Fallback to direct BeautifulSoup parsing if trafilatura didn't find it
            if not coinbase_rank:
                try:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find all app entries (adjust these selectors based on the actual page structure)
                    app_entries = soup.find_all(['div', 'li', 'tr'], attrs={
                        'class': lambda x: x and any(c in x for c in ['app-row', 'app-item', 'app-card', 'app-entry'])
                    })
                    
                    # If no structured entries found, look for any elements containing "Coinbase"
                    if not app_entries:
                        app_entries = soup.find_all(lambda tag: tag.name in ['div', 'li', 'tr'] and 'Coinbase' in tag.get_text())
                    
                    for i, entry in enumerate(app_entries):
                        if "Coinbase" in entry.get_text():
                            # Get the rank, either from a specific element or by position in list
                            rank_elem = entry.find(class_=['rank', 'position', 'number'])
                            if rank_elem and rank_elem.text.strip().replace('#', '').isdigit():
                                coinbase_rank = int(rank_elem.text.strip().replace('#', ''))
                            else:
                                # Fallback to position in list
                                coinbase_rank = i + 1
                            
                            logger.info(f"Found Coinbase at rank {coinbase_rank} using BeautifulSoup")
                            break
                except Exception as parse_err:
                    logger.error(f"BeautifulSoup parsing error: {str(parse_err)}")
            
            # If Coinbase not found in the results, set rank to "200+"
            if not coinbase_rank:
                logger.info("Coinbase not found in top chart, using 200+ as the rank")
                coinbase_rank = "200+"
            
            # Create response with current data
            current_date = datetime.now().strftime('%Y-%m-%d')
            response_data = {
                'rank': coinbase_rank,
                'last_updated': current_date,
                'history': [],
                'source': "AppFigures.com - US iPhone Free Apps"
            }
            
            if coinbase_rank == "200+":
                response_data['status'] = "Coinbase not found in top 200 apps"
            
            # For now, we'll keep a minimal history with just today's data
            # This avoids misleading simulated historical data
            history = [{
                'date': current_date,
                'rank': coinbase_rank
            }]
            
            response_data['history'] = history
            
            logger.info(f"Coinbase current rank: {coinbase_rank}")
            return response_data
        else:
            logger.error(f"Failed to fetch app ranking data: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error in get_coinbase_ranking: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the function
    data = get_coinbase_ranking()
    print(json.dumps(data, indent=2))
