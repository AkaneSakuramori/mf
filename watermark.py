import os
import asyncio
import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DOWNLOAD_PATH, OUTPUT_PATH, get_watermark_settings, update_user_settings

async def show_watermark_menu(client, message_or_callback, user_id):
    settings = get_watermark_settings(user_id)
    
    status_text = f"""⚙️ **Watermark Settings**

📌 Logo URL: {settings['url'] if settings['url'] else '❌ Not Set'}
📍 Position: {settings['position'].title()}
📏 Size: {settings['size']}%
🌫 Opacity: {settings['opacity']}

Choose an option below:"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Set Logo URL", callback_data="wm_set_url")],
        [InlineKeyboardButton("📍 Position", callback_data="wm_set_position"),
         InlineKeyboardButton("📏 Size", callback_data="wm_set_size")],
        [InlineKeyboardButton("🌫 Opacity", callback_data="wm_set_opacity")],
        [InlineKeyboardButton("🔄 Reset to Default", callback_data="wm_reset")],
        [InlineKeyboardButton("« Back", callback_data="back_main")]
    ])
    
    if hasattr(message_or_callback, 'edit_text'):
        await message_or_callback.edit_text(status_text, reply_markup=keyboard)
    else:
        await message_or_callback.reply_text(status_text, reply_markup=keyboard)

async def handle_watermark_callback(client, callback_query, user_states, user_data):
    user_id = callback_query.from_user.id
    await show_watermark_menu(client, callback_query.message, user_id)

async def handle_watermark_settings(client, callback_query, user_states, user_data):
    user_id = callback_query.from_user.id
    action = callback_query.data
    
    if action == "wm_set_url":
        user_states[user_id] = "setting_watermark_url"
        await callback_query.message.edit_text(
            "Send me the watermark image URL\n\n"
            "Example: https://example.com/logo.png"
        )
    
    elif action == "wm_set_position":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↖️ Top Left", callback_data="wmpos_topleft"),
             InlineKeyboardButton("↗️ Top Right", callback_data="wmpos_topright")],
            [InlineKeyboardButton("↙️ Bottom Left", callback_data="wmpos_bottomleft"),
             InlineKeyboardButton("↘️ Bottom Right", callback_data="wmpos_bottomright")],
            [InlineKeyboardButton("🎯 Center", callback_data="wmpos_center")],
            [InlineKeyboardButton("« Back", callback_data="watermark")]
        ])
        await callback_query.message.edit_text("Select watermark position:", reply_markup=keyboard)
    
    elif action == "wm_set_size":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("10%", callback_data="wmsize_10"),
             InlineKeyboardButton("15%", callback_data="wmsize_15")],
            [InlineKeyboardButton("20%", callback_data="wmsize_20"),
             InlineKeyboardButton("25%", callback_data="wmsize_25")],
            [InlineKeyboardButton("30%", callback_data="wmsize_30"),
             InlineKeyboardButton("40%", callback_data="wmsize_40")],
            [InlineKeyboardButton("« Back", callback_data="watermark")]
        ])
        await callback_query.message.edit_text("Select watermark size:", reply_markup=keyboard)
    
    elif action == "wm_set_opacity":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("25%", callback_data="wmopacity_0.25"),
             InlineKeyboardButton("50%", callback_data="wmopacity_0.5")],
            [InlineKeyboardButton("75%", callback_data="wmopacity_0.75"),
             InlineKeyboardButton("100%", callback_data="wmopacity_1.0")],
            [InlineKeyboardButton("« Back", callback_data="watermark")]
        ])
        await callback_query.message.edit_text("Select watermark opacity:", reply_markup=keyboard)
    
    elif action == "wm_reset":
        update_user_settings(user_id, "watermark_url", None)
        update_user_settings(user_id, "watermark_position", "topleft")
        update_user_settings(user_id, "watermark_size", "20")
        update_user_settings(user_id, "watermark_opacity", "1.0")
        await callback_query.answer("✅ Settings reset to default!")
        await show_watermark_menu(client, callback_query.message, user_id)

async def handle_watermark_value(client, callback_query, user_states, user_data):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data.startswith("wmpos_"):
        position = data.split("_")[1]
        update_user_settings(user_id, "watermark_position", position)
        await callback_query.answer(f"✅ Position set to {position.title()}")
        await show_watermark_menu(client, callback_query.message, user_id)
    
    elif data.startswith("wmsize_"):
        size = data.split("_")[1]
        update_user_settings(user_id, "watermark_size", size)
        await callback_query.answer(f"✅ Size set to {size}%")
        await show_watermark_menu(client, callback_query.message, user_id)
    
    elif data.startswith("wmopacity_"):
        opacity = data.split("_")[1]
        update_user_settings(user_id, "watermark_opacity", opacity)
        await callback_query.answer(f"✅ Opacity set to {float(opacity)*100}%")
        await show_watermark_menu(client, callback_query.message, user_id)

async def handle_watermark_url_input(client, message, user_states, user_data):
    user_id = message.from_user.id
    url = message.text.strip()
    
    if not url.startswith("http"):
        await message.reply_text("❌ Invalid URL. Please send a valid image URL starting with http:// or https://")
        return
    
    update_user_settings(user_id, "watermark_url", url)
    await message.reply_text("✅ Watermark logo URL saved!")
    user_states.pop(user_id, None)
    await show_watermark_menu(client, message, user_id)

async def apply_watermark_to_video(client, message, user_id):
    settings = get_watermark_settings(user_id)
    
    if not settings['url']:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Configure Watermark", callback_data="watermark")]
        ])
        await message.reply_text(
            "❌ Watermark logo not set!\n\n"
            "Please configure your watermark settings first.",
            reply_markup=keyboard
        )
        return
    
    status_msg = await message.reply_text("⏳ Downloading video...")
    
    video_file = None
    output_file = None
    
    try:
        video_file = os.path.join(DOWNLOAD_PATH, f"{user_id}_watermark_{int(time.time())}.mp4")
        await client.download_media(message, video_file)
        
        if not os.path.exists(video_file):
            raise Exception("Failed to download video")
        
        await status_msg.edit_text("⏳ Applying watermark...")
        
        output_file = os.path.join(OUTPUT_PATH, f"{user_id}_watermarked_{int(time.time())}.mp4")
        
        position_map = {
            "topleft": "10:10",
            "topright": "main_w-overlay_w-10:10",
            "bottomleft": "10:main_h-overlay_h-10",
            "bottomright": "main_w-overlay_w-10:main_h-overlay_h-10",
            "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2"
        }
        
        overlay_position = position_map.get(settings['position'], "10:10")
        size_percent = float(settings['size'])
        opacity = float(settings['opacity'])
        
        filter_complex = (
            f"[1:v]scale=iw*{size_percent/100}:ih*{size_percent/100},"
            f"format=rgba,colorchannelmixer=aa={opacity}[wm];"
            f"[0:v][wm]overlay={overlay_position}"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_file,
            "-i", settings['url'],
            "-filter_complex", filter_complex,
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
