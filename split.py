import os
import subprocess
from config import DOWNLOAD_PATH, OUTPUT_PATH

async def handle_split_callback(client, callback_query, user_states, user_data):
    user_id = callback_query.from_user.id
    user_states[user_id] = "waiting_split_video"
    user_data[user_id] = {}
    
    await callback_query.message.edit_text("Send me the video you want to split.")

async def handle_split_time(client, message, user_states, user_data):
    user_id = message.from_user.id
    split_time = message.text.strip()
    
    video_msg = user_data[user_id].get("video")
    if not video_msg:
        await message.reply_text("Error: No video found. Please start again with /start")
        return
    
    status_msg = await message.reply_text("⏳ Downloading video...")
    
    try:
        video_file = video_msg.video or video_msg.document
        file_path = os.path.join(DOWNLOAD_PATH, f"{user_id}_split.mp4")
        await client.download_media(video_msg, file_path)
        
        await status_msg.edit_text("⏳ Splitting video...")
        
        output1 = os.path.join(OUTPUT_PATH, f"{user_id}_part1.mp4")
        output2 = os.path.join(OUTPUT_PATH, f"{user_id}_part2.mp4")
        
        cmd1 = [
            "ffmpeg", "-i", file_path,
            "-t", split_time,
            "-c", "copy",
            output1, "-y"
        ]
        
        cmd2 = [
            "ffmpeg", "-i", file_path,
            "-ss", split_time,
            "-c", "copy",
            output2, "-y"
        ]
        
        subprocess.run(cmd1, check=True, capture_output=True)
        subprocess.run(cmd2, check=True, capture_output=True)
        
        await status_msg.edit_text("⏳ Uploading videos...")
        
        await message.reply_document(output1, caption="Part 1")
        await message.reply_document(output2, caption="Part 2")
        
        await status_msg.edit_text("✅ Video split successfully!")
        
        os.remove(file_path)
        os.remove(output1)
        os.remove(output2)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
    
    user_states.pop(user_id, None)
    user_data.pop(user_id, None)
