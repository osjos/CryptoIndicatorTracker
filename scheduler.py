#!/usr/bin/env python

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
from data_manager import update_database

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