# Crypto Market Events Tracker

## Overview

The Crypto Market Events Tracker is a comprehensive Streamlit web application that monitors multiple cryptocurrency market indicators to help determine optimal entry and exit points for Bitcoin investments. The system aggregates data from various sources including technical analysis indicators, market sentiment metrics, and external APIs to provide a unified dashboard for crypto market analysis.

The application tracks five key indicators: MAG7 vs Bitcoin performance comparison, Pi Cycle Top indicator, Coinbase App Store ranking, Colin Talks Crypto Bitcoin Bull Run Index (CBBI), and Bitcoin halving cycle analysis. Each indicator provides historical context and current market signals based on proven patterns from previous market cycles.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses Streamlit as the primary web framework, providing an interactive dashboard with multiple pages for different indicators. The main application (`app.py`) serves as the entry point with a sidebar navigation system allowing users to switch between different indicator views. Each indicator has its own dedicated utility module and can be viewed individually or as part of the main dashboard overview.

### Backend Architecture
The system follows a modular architecture with separate utility modules for each indicator located in the `utils/` directory. A centralized data manager (`data_manager.py`) handles all database operations including data fetching, storage, and retrieval. The application uses a background scheduler (`scheduler.py`) to automatically update data at regular intervals, ensuring fresh market data without manual intervention.

### Data Storage Solutions
The application uses SQLite as the primary database solution for storing historical indicator data, daily updates, and monitoring information. The database schema includes separate tables for each indicator type (mag7_btc, pi_cycle, coinbase_rank, daily_cbbi_scores, halving) along with an indicator_updates table for tracking data refresh status. This approach provides reliable local storage with built-in transaction support and easy backup capabilities.

### Data Collection and Processing
Each indicator has its own dedicated module that handles data collection from various sources:
- MAG7 vs Bitcoin data is fetched from Yahoo Finance API
- Pi Cycle calculations use historical Bitcoin price data with 111-day and 350-day moving averages
- Coinbase ranking is scraped from Apple App Store RSS feeds
- CBBI scores are obtained from Colin Talks Crypto's official API
- Halving cycle tracking uses predefined Bitcoin halving dates with mathematical projections

### Scheduling and Automation
The system implements automated data updates using APScheduler with both cron-based (daily at 6 AM Stockholm time) and interval-based (every 12 hours) triggers. This dual approach ensures data freshness while providing fallback mechanisms if the primary scheduled update fails. The scheduler runs in the background and gracefully shuts down when the application exits.

### Monitoring and Health Checks
The application includes dedicated monitoring pages that provide real-time status information about each indicator's last update time, success/failure status, and any error messages. A health check endpoint (`pages/_healthz.py`) enables external monitoring systems to verify application availability.

## External Dependencies

### Financial Data APIs
- **Yahoo Finance (yfinance)**: Primary source for Bitcoin and MAG7 stock price data, providing historical and real-time market information
- **Colin Talks Crypto CBBI API**: Official source for Bitcoin Bull Run Index scores, accessed via HTTPS requests to their data endpoint
- **Apple App Store RSS API**: Used to track Coinbase app ranking in the top free apps chart

### Visualization and UI Libraries
- **Streamlit**: Core web application framework providing the user interface and interactive components
- **Plotly**: Advanced charting library for creating interactive financial charts and technical indicator visualizations
- **Pandas**: Data manipulation and analysis library for processing time series financial data

### Task Scheduling and Background Processing
- **APScheduler**: Advanced Python scheduler for automated data updates and background task management
- **SQLite3**: Built-in Python database interface for local data storage and retrieval

### Web Scraping and Data Processing
- **Requests**: HTTP library for API calls and web scraping operations
- **BeautifulSoup**: HTML parsing library used for extracting data from web pages when API access is not available

### Development and Deployment
- **Python 3.x**: Core runtime environment
- **Replit**: Cloud development and hosting platform for the application deployment