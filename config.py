import os
import json

API_ID = int(os.environ.get("API_ID", "YOUR_API_ID"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")

DOWNLOAD_PATH = "downloads/"
OUTPUT_PATH = "outputs/"
SETTINGS_FILE = "user_settings.json"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def get_user_settings(user_id):
    settings = load_settings()
    user_id_str = str(user_id)
    
    if user_id_str not in settings:
        settings[user_id_str] = {
            "watermark_url": None,
            "watermark_position": "topleft",
            "watermark_size": "20",
            "watermark_opacity": "1.0"
        }
        save_settings(settings)
    
    return settings[user_id_str]

def update_user_settings(user_id, key, value):
    settings = load_settings()
    user_id_str = str(user_id)
    
    if user_id_str not in settings:
        settings[user_id_str] = {
            "watermark_url": None,
            "watermark_position": "topleft",
            "watermark_size": "20",
            "watermark_opacity": "1.0"
        }
    
    settings[user_id_str][key] = value
    save_settings(settings)

def get_watermark_settings(user_id):
    user_settings = get_user_settings(user_id)
    return {
        "url": user_settings.get("watermark_url"),
        "position": user_settings.get("watermark_position", "topleft"),
        "size": user_settings.get("watermark_size", "20"),
        "opacity": user_settings.get("watermark_opacity", "1.0")
    }
