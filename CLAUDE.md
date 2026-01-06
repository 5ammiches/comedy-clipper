# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
streamlit run app.py

# Install dependencies
pip install -r requirements.txt
```

**System dependencies required:** ffmpeg (for video processing), yt-dlp (installed via pip)

## Architecture

Comedy Clipper is a Streamlit-based tool for discovering YouTube comedy clips and preparing them for TikTok. It uses a three-agent pipeline:

```
Search → Analyze → Download
```

### Agent Pipeline

1. **Discovery Agent** (`agents/discovery.py`)
   - Scrapes YouTube search results via web scraping (parses `ytInitialData` JSON)
   - Returns video metadata: id, title, duration, channel, view count, thumbnail
   - Uses `requests` library, not yt-dlp for search

2. **Analysis Agent** (`agents/analysis.py`)
   - Extracts transcripts using yt-dlp (`--write-auto-sub`)
   - Sends transcript to AI via Open Router to identify clip-worthy comedy moments
   - Uses OpenAI SDK with Open Router endpoint (`https://openrouter.ai/api/v1`)
   - Returns JSON with start/end timestamps, descriptions, and suggested captions
   - Default model: `anthropic/claude-3.5-sonnet` (configurable in code)
   - Other available models: `openai/gpt-4-turbo`, `google/gemini-pro`, etc.

3. **Download Agent** (`agents/download.py`)
   - Downloads video segments using yt-dlp `--download-sections`
   - Falls back to full download + ffmpeg trim if needed
   - `optimize_for_tiktok()` converts to 9:16 aspect ratio using ffmpeg

### Frontend (`app.py`)

Streamlit app with three-step workflow:
1. Search form with embedded YouTube players in results
2. Video selection with AI analysis or manual clip selection
3. Clip review with adjustable timestamps and download buttons

Session state keys: `search_results`, `selected_video`, `clip_suggestions`, `downloaded_clips`

## Configuration

- API key: Set `OPENROUTER_API_KEY` in `.env` or via sidebar input
  - Get your API key at: https://openrouter.ai/
  - Supports any model available on Open Router
- Output directory: Configurable in sidebar (default: `./output`)
- Clip settings: min/max length, number of suggestions per video
- AI Model: Change in `agents/analysis.py` (line 134) - default is `anthropic/claude-3.5-sonnet`
