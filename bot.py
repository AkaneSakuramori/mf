from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import API_ID, API_HASH, BOT_TOKEN
from split import handle_split_callback, handle_split_time
from merge import handle_merge_callback, handle_merge_videos, handle_merge_done
from screenshot import handle_ss_callback, handle_ss_type, handle_ss_count, handle_ss_time
from watermark import (
    handle_watermark_callback, 
    handle_watermark_settings, 
    handle_watermark_value,
    handle_watermark_url_input,
    apply_watermark_to_video
)

app = Client("video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_states = {}
user_data = {}

def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📹 Split Video", callback_data="split")],
        [InlineKeyboardButton("🔗 Merge Videos", callback_data="merge")],
        [InlineKeyboardButton("📸 Screenshot", callback_data="screenshot")],
        [InlineKeyboardButton("💧 Watermark Settings", callback_data="watermark")]
    ])

def get_video_options_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📹 Split", callback_data="quick_split")],
        [InlineKeyboardButton("📸 Screenshot", callback_data="quick_screenshot")],
        [InlineKeyboardButton("💧 Add Watermark", callback_data="quick_watermark")],
        [InlineKeyboardButton("🔧 More Options", callback_data="back_main")]
    ])

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        "👋 Welcome to Video Processing Bot!\n\n"
        "Select an option below:",
        reply_markup=get_main_menu()
    )

@app.on_callback_query(filters.regex("^back_main$"))
async def back_main_callback(client, callback_query):
    await callback_query.message.edit_text(
        "👋 Welcome to Video Processing Bot!\n\n"
        "Select an option below:",
        reply_markup=get_main_menu()
    )

@app.on_callback_query(filters.regex("^split$"))
async def split_callback(client, callback_query):
    await handle_split_callback(client, callback_query, user_states, user_data)

@app.on_callback_query(filters.regex("^merge$"))
async def merge_callback(client, callback_query):
    await handle_merge_callback(client, callback_query, user_states, user_data)

@app.on_callback_query(filters.regex("^screenshot$"))
async def screenshot_callback(client, callback_query):
    await handle_ss_callback(client, callback_query, user_states, user_data)

@app.on_callback_query(filters.regex("^watermark$"))
async def watermark_callback(client, callback_query):
    await handle_watermark_callback(client, callback_query, user_states, user_data)

@app.on_callback_query(filters.regex("^wm_(set_|reset)"))
async def watermark_settings_callback(client, callback_query):
    await handle_watermark_settings(client, callback_query, user_states, user_data)

@app.on_callback_query(filters.regex("^(wmpos_|wmsize_|wmopacity_)"))
async def watermark_value_callback(client, callback_query):
    await handle_watermark_value(client, callback_query, user_states, user_data)

@app.on_callback_query(filters.regex("^ss_"))
async def ss_type_callback(client, callback_query):
    await handle_ss_type(client, callback_query, user_states, user_data)

@app.on_callback_query(filters.regex("^auto_"))
async def ss_count_callback(client, callback_query):
    await handle_ss_count(client, callback_query, user_states, user_data)

@app.on_callback_query(filters.regex("^quick_"))
async def quick_action_callback(client, callback_query):
    user_id = callback_query.from_user.id
    action = callback_query.data.split("_")[1]
    
    if action == "split":
        user_states[user_id] = "waiting_split_video"
        user_data[user_id] = {}
        await callback_query.message.edit_text("Send me the video you want to split.")
    
    elif action == "screenshot":
        await handle_ss_callback(client, callback_query, user_states, user_data)
    
    elif action == "watermark":
        if user_id in user_data and "pending_video" in user_data[user_id]:
            video_msg = user_data[user_id]["pending_video"]
            await callback_query.message.delete()
            await apply_watermark_to_video(client, video_msg, user_id)
            user_data.pop(user_id, None)
        else:
            await callback_query.answer("❌ Video not found, please send again")

@app.on_message(filters.command("done"))
async def done_command(client, message: Message):
    user_id = message.from_user.id
    
    if user_states.get(user_id) == "waiting_merge_videos":
        await handle_merge_done(client, message, user_states, user_data)
    else:
        await message.reply_text("No active process. Use /start to begin.")

@app.on_message(filters.video | filters.document)
async def handle_video_message(client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    
    if state == "waiting_split_video":
        user_data[user_id] = {"video": message}
        user_states[user_id] = "waiting_split_time"
        await message.reply_text("Send the time to split at (format: HH:MM:SS or MM:SS)")
    
    elif state == "waiting_merge_videos":
        await handle_merge_videos(client, message, user_states, user_data)
    
    elif state == "waiting_ss_video_manual" or state == "waiting_ss_video_auto":
        user_data[user_id]["video"] = message
        
        if state == "waiting_ss_video_manual":
            user_states[user_id] = "waiting_ss_time"
            await message.reply_text("Send the time for screenshot (format: HH:MM:SS or MM:SS)")
        else:
            count = user_data[user_id].get("ss_count", 10)
            await message.reply_text(f"Processing {count} screenshots...")
            from screenshot import process_auto_screenshots
            await process_auto_screenshots(client, message, user_data[user_id])
            user_states.pop(user_id, None)
            user_data.pop(user_id, None)
    
    else:
        user_data[user_id] = {"pending_video": message}
        await message.reply_text(
            "📹 What would you like to do with this video?",
            reply_markup=get_video_options_menu()
        )

@app.on_message(filters.text & ~filters.command(["start", "done"]))
async def handle_text_message(client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    
    if state == "waiting_split_time":
        await handle_split_time(client, message, user_states, user_data)
    
    elif state == "waiting_ss_time":
        await handle_ss_time(client, message, user_states, user_data)
    
    elif state == "setting_watermark_url":
        await handle_watermark_url_input(client, message, user_states, user_data)

print("Bot is starting...")
app.run()
