import schedule
import time
import subprocess
import os
from datetime import datetime

# Path to the scraper script
SCRAPER_PATH = os.path.join(os.path.dirname(__file__), "scraper.py")

def run_scraper():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting scheduled scrape...")
    try:
        # Run the scraper as a subprocess
        subprocess.run(["python", SCRAPER_PATH], check=True)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Scrape finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running scraper: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Schedule the job every 15 minutes
schedule.every(15).minutes.do(run_scraper)

# Also run it once immediately on startup
print("Scheduler started. Running first scrape now...")
run_scraper()

if __name__ == "__main__":
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Scheduler stopped.")
