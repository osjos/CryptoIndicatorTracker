#!/usr/bin/env python

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
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
            # Schedule the database update to run every 6 hours
            scheduler.add_job(
                func=scheduled_update_database,
                trigger=IntervalTrigger(hours=6),
                id='update_database_job',
                name='Update Database',
                replace_existing=True
            )
            
            # Start the scheduler
            scheduler.start()
            logger.info("Scheduler started successfully")
            
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
        logger.info(f"Running scheduled database update at {datetime.now()}")
        update_database()
        logger.info("Scheduled database update completed successfully")
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