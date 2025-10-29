from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import API_ID, API_HASH, BOT_TOKEN
from split import handle_split_callback, handle_split_time
from merge import handle_merge_callback, handle_merge_videos, handle_merge_done
from screenshot import handle_ss_callback, handle_ss_type, handle_ss_count, handle_ss_time

app = Client("video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_states = {}
user_data = {}

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📹 Split Video", callback_data="split")],
        [InlineKeyboardButton("🔗 Merge Videos", callback_data="merge")],
        [InlineKeyboardButton("📸 Screenshot", callback_data="screenshot")]
    ])
    
    await message.reply_text(
        "👋 Welcome to Video Processing Bot!\n\n"
        "Select an option below:",
        reply_markup=keyboard
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

@app.on_callback_query(filters.regex("^ss_"))
async def ss_type_callback(client, callback_query):
    await handle_ss_type(client, callback_query, user_states, user_data)

@app.on_callback_query(filters.regex("^auto_"))
async def ss_count_callback(client, callback_query):
    await handle_ss_count(client, callback_query, user_states, user_data)

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

@app.on_message(filters.text & ~filters.command(["start", "done"]))
async def handle_text_message(client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    
    if state == "waiting_split_time":
        await handle_split_time(client, message, user_states, user_data)
    
    elif state == "waiting_ss_time":
        await handle_ss_time(client, message, user_states, user_data)

print("Bot is starting...")
app.run()
