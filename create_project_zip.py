
#!/usr/bin/env python

import zipfile
import os
from datetime import datetime

def create_project_zip():
    """
    Create a zip file containing all the project files for the Crypto Market Events Tracker.
    """
    # Get current timestamp for the zip filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"crypto_tracker_project_{timestamp}.zip"
    
    # Files and directories to include in the zip
    files_to_include = [
        # Core application files
        'app.py',
        'data_manager.py', 
        'scheduler.py',
        
        # Configuration files
        '.replit',
        'pyproject.toml',
        '.streamlit/config.toml',
        
        # Utils directory
        'utils/__init__.py',
        'utils/mag7_btc.py',
        'utils/pi_cycle.py',
        'utils/app_store.py',
        'utils/cbbi.py',
        'utils/halving_tracker.py',
        
        # Pages directory
        'pages/_healthz.py',
        'pages/monitor.py',
        
        # Additional utility scripts
        'import_historical_cbbi.py',
        'populate_test_cbbi_data.py',
        'check_cbbi.py',
        'check_cbbi_website.py',
        
        # Database (if you want to include it)
        'crypto_tracker.db',
        
        # Any other relevant files
        'cbbi_page.html',
        'cbbi_scripts.js',
        'cbbi_trafilatura.xml',
        'latest.json'
    ]
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_include:
                if os.path.exists(file_path):
                    if os.path.isfile(file_path):
                        # Add individual file
                        zipf.write(file_path, file_path)
                        print(f"✓ Added: {file_path}")
                    elif os.path.isdir(file_path):
                        # Add directory and all its contents
                        for root, dirs, files in os.walk(file_path):
                            for file in files:
                                full_path = os.path.join(root, file)
                                zipf.write(full_path, full_path)
                                print(f"✓ Added: {full_path}")
                else:
                    print(f"⚠ File not found: {file_path}")
            
            # Create a README file with project information
            readme_content = """# Crypto Market Events Tracker

## Project Overview
This is a comprehensive crypto market analysis tool that combines traditional finance indicators with Bitcoin-specific metrics to help identify market cycle positions.

## Key Features
- Real-time data updates daily at 6 AM Stockholm time
- 5 different crypto market indicators:
  1. MAG7 vs Bitcoin Index
  2. Pi Cycle Top Indicator  
  3. Coinbase App Store Ranking
  4. CBBI Score Integration
  5. Bitcoin Halving Cycle Analysis
- Interactive Plotly visualizations
- SQLite database for data persistence
- Streamlit web interface
- Deployed on Replit with autoscale

## Files Structure
- app.py: Main Streamlit application
- data_manager.py: Database management
- scheduler.py: Background task scheduling
- utils/: Data fetching modules for each indicator
- pages/: Additional Streamlit pages
- crypto_tracker.db: SQLite database

## Installation
1. Install dependencies: pip install -r requirements.txt (or use pyproject.toml)
2. Run: streamlit run app.py

## Deployment
Configured for Replit deployment with .replit configuration file.
"""
            
            zipf.writestr("README.md", readme_content)
            print("✓ Added: README.md")
        
        print(f"\n🎉 Project zip file created successfully: {zip_filename}")
        print(f"📁 File size: {os.path.getsize(zip_filename) / (1024*1024):.2f} MB")
        print("\n📋 Zip file contents:")
        
        # List zip contents
        with zipfile.ZipFile(zip_filename, 'r') as zipf:
            for info in zipf.infolist():
                print(f"  - {info.filename} ({info.file_size} bytes)")
        
        return zip_filename
        
    except Exception as e:
        print(f"❌ Error creating zip file: {str(e)}")
        return None

if __name__ == "__main__":
    zip_file = create_project_zip()
    if zip_file:
        print(f"\n✅ Success! You can download the zip file: {zip_file}")
        print("💡 In Replit, you can download it by clicking on the file in the file explorer.")
