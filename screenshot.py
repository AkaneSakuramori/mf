import os
import subprocess
import random
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DOWNLOAD_PATH, OUTPUT_PATH

async def handle_ss_callback(client, callback_query, user_states, user_data):
    user_id = callback_query.from_user.id
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Auto", callback_data="ss_auto")],
        [InlineKeyboardButton("✋ Manual", callback_data="ss_manual")]
    ])
    
    await callback_query.message.edit_text(
        "Select screenshot mode:",
        reply_markup=keyboard
    )

async def handle_ss_type(client, callback_query, user_states, user_data):
    user_id = callback_query.from_user.id
    choice = callback_query.data.split("_")[1]
    
    if choice == "auto":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("5 Screenshots", callback_data="auto_5")],
            [InlineKeyboardButton("10 Screenshots", callback_data="auto_10")],
            [InlineKeyboardButton("15 Screenshots", callback_data="auto_15")],
            [InlineKeyboardButton("20 Screenshots", callback_data="auto_20")]
        ])
        
        await callback_query.message.edit_text(
            "Select number of screenshots:",
            reply_markup=keyboard
        )
    else:
        user_states[user_id] = "waiting_ss_video_manual"
        user_data[user_id] = {}
        await callback_query.message.edit_text("Send me the video for manual screenshot.")

async def handle_ss_count(client, callback_query, user_states, user_data):
    if callback_query:
        user_id = callback_query.from_user.id
        count = int(callback_query.data.split("_")[1])
        
        user_states[user_id] = "waiting_ss_video_auto"
        user_data[user_id] = {"ss_count": count}
        
        await callback_query.message.edit_text(f"Send me the video. I'll take {count} random screenshots.")

async def handle_ss_time(client, message, user_states, user_data):
    user_id = message.from_user.id
    ss_time = message.text.strip()
    
    video_msg = user_data[user_id].get("video")
    if not video_msg:
        await message.reply_text("Error: No video found. Please start again with /start")
        return
    
    status_msg = await message.reply_text("⏳ Downloading video...")
    
    try:
        file_path = os.path.join(DOWNLOAD_PATH, f"{user_id}_ss.mp4")
        await client.download_media(video_msg, file_path)
        
        await status_msg.edit_text("⏳ Taking screenshot...")
        
        output_file = os.path.join(OUTPUT_PATH, f"{user_id}_screenshot.jpg")
        
        cmd = [
            "ffmpeg",
            "-ss", ss_time,
            "-i", file_path,
            "-vframes", "1",
            output_file, "-y"
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        await status_msg.edit_text("⏳ Uploading screenshot...")
        
        await message.reply_photo(output_file, caption=f"Screenshot at {ss_time}")
        
        await status_msg.edit_text("✅ Screenshot taken successfully!")
        
        os.remove(file_path)
        os.remove(output_file)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
    
    user_states.pop(user_id, None)
    user_data.pop(user_id, None)

async def process_auto_screenshots(client, message, data):
    user_id = message.from_user.id
    count = data.get("ss_count", 10)
    video_msg = data.get("video")
    
    status_msg = await message.reply_text("⏳ Downloading video...")
    
    try:
        file_path = os.path.join(DOWNLOAD_PATH, f"{user_id}_ss_auto.mp4")
        await client.download_media(video_msg, file_path)
        
        duration_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        
        result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        
        await status_msg.edit_text(f"⏳ Taking {count} screenshots...")
        
        times = sorted(random.sample(range(1, int(duration)), min(count, int(duration) - 1)))
        
        for idx, ss_time in enumerate(times, 1):
            output_file = os.path.join(OUTPUT_PATH, f"{user_id}_ss_{idx}.jpg")
            
            cmd = [
                "ffmpeg",
                "-ss", str(ss_time),
                "-i", file_path,
                "-vframes", "1",
                output_file, "-y"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            await message.reply_photo(output_file, caption=f"Screenshot {idx}/{count} at {ss_time}s")
            os.remove(output_file)
            
            await status_msg.edit_text(f"⏳ Progress: {idx}/{count}")
        
        await status_msg.edit_text(f"✅ All {count} screenshots taken successfully!")
        
        os.remove(file_path)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
