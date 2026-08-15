"""
AUTOMATION MODULE — Tech Skill Demand Tracker
=============================================
This module demonstrates automated weekly data collection.
The scheduler is configured to run every Monday at 9:00 AM,
triggering the full scraping pipeline automatically.

To activate: run this script and keep it running in background.
Currently disabled for portfolio demonstration purposes.
"""

import schedule
import time
import subprocess
import sys

def run_scrapers():
    print("Running weekly scrape...")
    subprocess.run([sys.executable, 'scrapers/run_all_scrapers.py'])

# Configured to run every Monday at 9 AM
schedule.every().monday.at("09:00").do(run_scrapers)

# Uncomment below to activate the scheduler:
# print("Scheduler running — press Ctrl+C to stop")
# print(f"Next run: {schedule.next_run()}")
# while True:
#     schedule.run_pending()
#     time.sleep(3600)

print("Scheduler configured successfully.")
print(f"Would run at: Monday 09:00 AM weekly")
print("To activate, uncomment the while loop above.")