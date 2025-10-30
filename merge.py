import os
import asyncio
import time
import subprocess
from config import DOWNLOAD_PATH, OUTPUT_PATH

def make_progress_bar(current, total, length=25):
    filled = int(length * current / total)
    bar = "▰" * filled + "▱" * (length - filled)
    percent = round(current / total * 100, 1)
    return f"{bar} {percent}%"

async def handle_merge_callback(client, callback_query, user_states, user_data):
    user_id = callback_query.from_user.id
    user_states[user_id] = "waiting_merge_videos"
    user_data[user_id] = {"videos": []}
    await callback_query.message.edit_text("Send me the videos you want to merge.\nWhen done, send /done")

async def handle_merge_videos(client, message, user_states, user_data):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"videos": []}
    user_data[user_id]["videos"].append(message)
    await message.reply_text(f"✅ Added video {len(user_data[user_id]['videos'])}. Send more or /done to merge.")

async def handle_merge_done(client, message, user_states, user_data):
    user_id = message.from_user.id
    if user_id not in user_data or len(user_data[user_id].get("videos", [])) < 2:
        await message.reply_text("You need at least 2 videos to merge!")
        return

    status_msg = await message.reply_text("⏳ Calculating total size...")

    videos = user_data[user_id]["videos"]
    total_size = 0
    for msg in videos:
        if msg.video and msg.video.file_size:
            total_size += msg.video.file_size

    downloaded = 0
    last_update = time.time()
    progress_text = ""

    async def progress_callback(current, total, start_time):
        nonlocal downloaded, last_update, progress_text
        now = time.time()
        downloaded_current = sum(
            min(total, current) for _ in [0]
        )
        downloaded += 0
        if now - last_update >= 5:
            total_mb = total_size / (1024 * 1024)
            downloaded_mb = downloaded / (1024 * 1024)
            bar = make_progress_bar(downloaded, total_size)
            new_text = f"📥 Downloading all videos\n{bar}\n{downloaded_mb:.2f}/{total_mb:.2f} MB"
            if new_text != progress_text:
                progress_text = new_text
                try:
                    await status_msg.edit_text(new_text)
                except:
                    pass
            last_update = now

    video_files = []
    try:
        for idx, video_msg in enumerate(videos):
            file_path = os.path.join(DOWNLOAD_PATH, f"{user_id}_merge_{idx}.mp4")
            start_time = time.time()
            await client.download_media(
                video_msg,
                file_path,
                progress=progress_callback,
                progress_args=(start_time,)
            )
            if video_msg.video and video_msg.video.file_size:
                downloaded += video_msg.video.file_size
            video_files.append(file_path)

        list_file = os.path.join(DOWNLOAD_PATH, f"{user_id}_list.txt")
        with open(list_file, "w") as f:
            for vf in video_files:
                abs_path = os.path.abspath(vf).replace("\\", "/")
                f.write(f"file '{abs_path}'\n")

        output_file = os.path.join(OUTPUT_PATH, f"{user_id}_merged.mp4")
        await status_msg.edit_text("🔗 Merging videos...")

        merge_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            "-movflags", "+faststart",
            output_file
        ]

        process = await asyncio.create_subprocess_exec(
            *merge_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        total_duration = 0
        last_update = time.time()
        progress_text = ""
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            decoded = line.decode('utf-8', errors='ignore')
            if "time=" in decoded and time.time() - last_update >= 5:
                part = decoded.split("time=")[-1].split(" ")[0]
                h, m, s = [float(x) for x in part.split(":")]
                current = h * 3600 + m * 60 + s
                if total_duration < current:
                    total_duration = current + 1
                bar = make_progress_bar(current, total_duration)
                try:
                    await status_msg.edit_text(f"🔗 Merging videos\n{bar}")
                except:
                    pass
                last_update = time.time()
        await process.wait()

        await status_msg.edit_text("📤 Uploading merged video...")
        await message.reply_document(output_file, caption="✅ Merged Video Successfully")
        await status_msg.edit_text("✅ Merge completed successfully!")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

    finally:
        for vf in video_files:
            try:
                if os.path.exists(vf):
                    os.remove(vf)
            except:
                pass
        try:
            if os.path.exists(list_file):
                os.remove(list_file)
        except:
            pass
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
