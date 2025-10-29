# Telegram Video Processing Bot

A Telegram bot built with Pyrogram for video processing operations.

## Features

- **Split Video**: Split videos at a specific time
- **Merge Videos**: Merge multiple videos into one
- **Screenshots**: Take manual or automatic random screenshots

## Prerequisites

- Python 3.7+
- FFmpeg installed on your system
- Telegram API credentials

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg:
- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **MacOS**: `brew install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/download.html

3. Set up environment variables in `config.py`:
```python
API_ID = "your_api_id"
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"
```

## Usage

Run the bot:
```bash
python bot.py
```

### Commands

- `/start` - Show main menu
- `/done` - Complete merge operation

### Operations

**Split Video:**
1. Click "Split Video"
2. Send video file
3. Send split time (HH:MM:SS or MM:SS)

**Merge Videos:**
1. Click "Merge Videos"
2. Send multiple video files
3. Send `/done` to merge

**Screenshot:**
1. Click "Screenshot"
2. Choose Auto or Manual
3. For Auto: Select count (5/10/15/20)
4. For Manual: Send time (HH:MM:SS or MM:SS)

## File Structure

```
.
├── bot.py          # Main bot file
├── config.py       # Configuration
├── split.py        # Video splitting logic
├── merge.py        # Video merging logic
├── screenshot.py   # Screenshot logic
├── requirements.txt
└── README.md
```
