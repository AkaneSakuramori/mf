import os
import subprocess
from config import DOWNLOAD_PATH, OUTPUT_PATH

async def handle_merge_callback(client, callback_query, user_states, user_data):
    user_id = callback_query.from_user.id
    user_states[user_id] = "waiting_merge_videos"
    user_data[user_id] = {"videos": []}
    
    await callback_query.message.edit_text(
        "Send me the videos you want to merge.\n"
        "When done, send /done"
    )

async def handle_merge_videos(client, message, user_states, user_data):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {"videos": []}
    
    user_data[user_id]["videos"].append(message)
    await message.reply_text(f"✅ Video {len(user_data[user_id]['videos'])} added. Send more or /done to merge.")

async def handle_merge_done(client, message, user_states, user_data):
    user_id = message.from_user.id
    
    if user_id not in user_data or len(user_data[user_id].get("videos", [])) < 2:
        await message.reply_text("You need at least 2 videos to merge!")
        return
    
    status_msg = await message.reply_text("⏳ Downloading videos...")
    
    try:
        video_files = []
        for idx, video_msg in enumerate(user_data[user_id]["videos"]):
            file_path = os.path.join(DOWNLOAD_PATH, f"{user_id}_merge_{idx}.mp4")
            await client.download_media(video_msg, file_path)
            video_files.append(file_path)
        
        await status_msg.edit_text("⏳ Merging videos...")
        
        list_file = os.path.join(DOWNLOAD_PATH, f"{user_id}_list.txt")
        with open(list_file, "w") as f:
            for video_file in video_files:
                f.write(f"file '{video_file}'\n")
        
        output_file = os.path.join(OUTPUT_PATH, f"{user_id}_merged.mp4")
        
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_file, "-y"
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        await status_msg.edit_text("⏳ Uploading merged video...")
        
        await message.reply_document(output_file, caption="Merged Video")
        
        await status_msg.edit_text("✅ Videos merged successfully!")
        
        for video_file in video_files:
            os.remove(video_file)
        os.remove(list_file)
        os.remove(output_file)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
    
    user_states.pop(user_id, None)
    user_data.pop(user_id, None)
