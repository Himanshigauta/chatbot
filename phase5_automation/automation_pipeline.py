import subprocess
import os
import json
from datetime import datetime

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRAPER_PATH = os.path.join(BASE_DIR, "phase1_data_acquisition", "scraper.py")
INDEXER_PATH = os.path.join(BASE_DIR, "phase2_indexing", "indexer.py")
METADATA_PATH = os.path.join(BASE_DIR, "last_updated.json")

def run_update():
    print(f"[{datetime.now()}] Starting Automation Update...")

    try:
        # 1. Run Scraper
        print(f"[{datetime.now()}] Running Scraper...")
        subprocess.run(["python", SCRAPER_PATH], check=True, cwd=BASE_DIR)

        # 2. Run Indexer
        print(f"[{datetime.now()}] Running Indexer...")
        subprocess.run(["python", "indexer.py"], check=True, cwd=os.path.join(BASE_DIR, "phase2_indexing"))

        # 3. Update Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(METADATA_PATH, "w") as f:
            json.dump({"last_updated": timestamp}, f, indent=4)
        
        print(f"[{datetime.now()}] Update Complete! Next update scheduled.")
        
    except Exception as e:
        print(f"[{datetime.now()}] Error during update: {e}")

if __name__ == "__main__":
    run_update()
