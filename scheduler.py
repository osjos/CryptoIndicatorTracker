#!/usr/bin/env python

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import sqlite3
from data_manager import update_database
from utils.cbbi import scrape_official_cbbi_score  # Import the CBBI scraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a scheduler
scheduler = BackgroundScheduler()

def start_scheduler():
    """
    Start the background scheduler with all scheduled tasks.
    """
    try:
        if not scheduler.running:
            # Define Stockholm timezone
            stockholm_tz = pytz.timezone('Europe/Stockholm')
            
            # Schedule the database update to run daily at 6 AM Stockholm time
            scheduler.add_job(
                func=scheduled_update_database,
                trigger=CronTrigger(hour=6, minute=0, timezone=stockholm_tz),
                id='update_database_job',
                name='Daily Update Database at 6 AM Stockholm Time',
                replace_existing=True
            )
            
            # Add a backup interval-based job that runs every 12 hours
            # This ensures data is updated even if the app restarts and misses the 6 AM trigger
            scheduler.add_job(
                func=scheduled_update_database,
                trigger=IntervalTrigger(hours=12),
                id='backup_update_database_job',
                name='Backup Update Every 12 Hours',
                replace_existing=True
            )
            
            # Start the scheduler
            scheduler.start()
            logger.info("Scheduler started successfully with daily update at 6 AM Stockholm time")
            
            # Run an initial update to ensure we have fresh data
            scheduled_update_database()
        else:
            logger.info("Scheduler is already running")
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")

def stop_scheduler():
    """
    Stop the background scheduler.
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

def scheduled_update_database():
    """
    Function to be called by the scheduler to update the database.
    """
    try:
        # Get current time in Stockholm timezone for logging
        stockholm_tz = pytz.timezone('Europe/Stockholm')
        now_stockholm = datetime.now(pytz.UTC).astimezone(stockholm_tz)
        
        logger.info(f"Running scheduled database update at {now_stockholm.strftime('%Y-%m-%d %H:%M:%S')} Stockholm time")
        update_database()
        
        # Log the completion with Stockholm time
        now_stockholm = datetime.now(pytz.UTC).astimezone(stockholm_tz)
        logger.info(f"Scheduled database update completed successfully at {now_stockholm.strftime('%Y-%m-%d %H:%M:%S')} Stockholm time")
    except Exception as e:
        logger.error(f"Error in scheduled database update: {str(e)}")

def scheduled_update_cbbi_score():
    """
    Function to update just the CBBI score in the database.
    This allows for more frequent updates of this critical value.
    """
    try:
        # Get current time in Stockholm timezone for logging
        stockholm_tz = pytz.timezone('Europe/Stockholm')
        now_stockholm = datetime.now(pytz.UTC).astimezone(stockholm_tz)
        
        logger.info(f"Running CBBI score update at {now_stockholm.strftime('%Y-%m-%d %H:%M:%S')} Stockholm time")
        
        # Scrape the latest CBBI score from the official website
        cbbi_score = scrape_official_cbbi_score()
        
        if cbbi_score is not None:
            # Convert to decimal if needed
            if cbbi_score > 1:
                cbbi_score = cbbi_score / 100.0
                
            # Store in database
            conn = sqlite3.connect('crypto_tracker.db')
            cursor = conn.cursor()
            
            # Current date and timestamp
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Check if we already have an entry for today
            cursor.execute("SELECT id FROM daily_cbbi_scores WHERE date = ?", (current_date,))
            existing_entry = cursor.fetchone()
            
            if existing_entry:
                # Update existing entry
                cursor.execute(
                    "UPDATE daily_cbbi_scores SET score = ?, timestamp = ? WHERE date = ?",
                    (cbbi_score, current_timestamp, current_date)
                )
                logger.info(f"Updated CBBI score for {current_date}: {cbbi_score:.2f} ({int(cbbi_score*100)}%)")
            else:
                # Insert new entry
                cursor.execute(
                    "INSERT INTO daily_cbbi_scores (date, score, timestamp) VALUES (?, ?, ?)",
                    (current_date, cbbi_score, current_timestamp)
                )
                logger.info(f"Inserted new CBBI score for {current_date}: {cbbi_score:.2f} ({int(cbbi_score*100)}%)")
            
            conn.commit()
            conn.close()
            
            # Log the completion with Stockholm time
            now_stockholm = datetime.now(pytz.UTC).astimezone(stockholm_tz)
            logger.info(f"CBBI score update completed successfully at {now_stockholm.strftime('%Y-%m-%d %H:%M:%S')} Stockholm time")
        else:
            logger.warning("Could not retrieve CBBI score, update skipped")
            
    except Exception as e:
        logger.error(f"Error updating CBBI score: {str(e)}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Test the scheduler
    start_scheduler()
    
    # Keep the script running to observe the scheduler
    try:
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        stop_scheduler()