import os

API_ID = int(os.environ.get("API_ID", "YOUR_API_ID"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")

DOWNLOAD_PATH = "downloads/"
OUTPUT_PATH = "outputs/"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)
