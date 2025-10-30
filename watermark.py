import os
import asyncio
import time
import re
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DOWNLOAD_PATH, OUTPUT_PATH

async def handle_watermark_callback(client, callback_query, user_states, user_data):
    user_id = callback_query.from_user.id
    user_states[user_id] = "waiting_watermark_url"
    user_data[user_id] = {}
    
    await callback_query.message.edit_text(
        "Send me the watermark image URL\n\n"
        "Example: https://example.com/watermark.png\n"
        "Or send /skip to use default position"
    )

async def handle_watermark_url(client, message, user_states, user_data):
    user_id = message.from_user.id
    
    if message.text.strip().startswith("/skip"):
        user_data[user_id]["watermark_url"] = None
        user_states[user_id] = "waiting_watermark_video"
        await message.reply_text("Send me the video to apply watermark")
        return
    
    watermark_url = message.text.strip()
    
    if not watermark_url.startswith("http"):
        await message.reply_text("Invalid URL. Please send a valid image URL starting with http:// or https://")
        return
    
    user_data[user_id]["watermark_url"] = watermark_url
    user_states[user_id] = "waiting_watermark_position"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Top Left", callback_data="pos_topleft")],
        [InlineKeyboardButton("Top Right", callback_data="pos_topright")],
        [InlineKeyboardButton("Bottom Left", callback_data="pos_bottomleft")],
        [InlineKeyboardButton("Bottom Right", callback_data="pos_bottomright")],
        [InlineKeyboardButton("Center", callback_data="pos_center")]
    ])
    
    await message.reply_text("Select watermark position:", reply_markup=keyboard)

async def handle_watermark_position(client, callback_query, user_states, user_data):
    user_id = callback_query.from_user.id
    position = callback_query.data.split("_")[1]
    
    user_data[user_id]["position"] = position
    user_states[user_id] = "waiting_watermark_video"
    
    await callback_query.message.edit_text("Send me the video to apply watermark")

async def apply_watermark(client, message, user_states, user_data):
    user_id = message.from_user.id
    
    video_msg = message
    watermark_url = user_data[user_id].get("watermark_url")
    position = user_data[user_id].get("position", "topleft")
    
    if not watermark_url:
        await message.reply_text("Error: No watermark URL provided")
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
        return
    
    status_msg = await message.reply_text("⏳ Downloading video...")
    
    video_file = None
    output_file = None
    
    try:
        video_file = os.path.join(DOWNLOAD_PATH, f"{user_id}_watermark.mp4")
        await client.download_media(video_msg, video_file)
        
        if not os.path.exists(video_file):
            raise Exception("Failed to download video")
        
        await status_msg.edit_text("⏳ Applying watermark...")
        
        output_file = os.path.join(OUTPUT_PATH, f"{user_id}_watermarked.mp4")
        
        position_map = {
            "topleft": "10:10",
            "topright": "main_w-overlay_w-10:10",
            "bottomleft": "10:main_h-overlay_h-10",
            "bottomright": "main_w-overlay_w-10:main_h-overlay_h-10",
            "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2"
        }
        
        overlay_position = position_map.get(position, "10:10")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_file,
            "-i", watermark_url,
            "-filter_complex",
            f"[0:v][1:v]overlay={overlay_position}",
            "-c:a", "copy",
            "-preset", "fast",
            output_file
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        last_update = time.time()
        progress_text = ""
        
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            
            decoded = line.decode('utf-8', errors='ignore')
            
            if "time=" in decoded and time.time() - last_update >= 5:
                try:
                    time_part = decoded.split("time=")[-1].split(" ")[0]
                    new_text = f"⏳ Applying watermark...\nProcessed: {time_part}"
                    if new_text != progress_text:
                        progress_text = new_text
                        await status_msg.edit_text(new_text)
                except:
                    pass
                last_update = time.time()
        
        await process.wait()
        
        if process.returncode != 0:
            stderr = await process.stderr.read()
            error_msg = stderr.decode('utf-8', errors='ignore')
            raise Exception(f"FFmpeg failed: {error_msg[:200]}")
        
        if not os.path.exists(output_file) or os.path.getsize(output_file) < 1000:
            raise Exception("Output file not created or too small")
        
        await status_msg.edit_text("⏳ Uploading watermarked video...")
        
        await message.reply_document(output_file, caption="✅ Watermarked Video")
        await status_msg.edit_text("✅ Watermark applied successfully!")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
    
    finally:
        if video_file and os.path.exists(video_file):
            try:
                os.remove(video_file)
            except:
                pass
        
        if output_file and os.path.exists(output_file):
            try:
                os.remove(output_file)
            except:
                pass
        
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
