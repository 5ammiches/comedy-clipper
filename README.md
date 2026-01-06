# 🎬 Comedy Clipper

An AI-powered tool for discovering comedy clips on YouTube and preparing them for TikTok posting. The tool helps you find videos, suggests the best clip moments using AI analysis, and downloads/trims clips for you to add your own commentary and overlays.

## Features

- **🔍 Smart Search**: Search YouTube for comedy content with duration filters
- **🤖 AI Analysis**: Uses Claude to analyze video transcripts and suggest clip-worthy moments
- **✂️ Auto-Trim**: Downloads only the clip segments you need
- **📱 TikTok Format**: Option to convert clips to 9:16 vertical format
- **🎛️ Simple Interface**: Clean Streamlit UI for easy workflow

## Prerequisites

You'll need these installed on your system:

1. **Python 3.10+**
2. **ffmpeg** - For video processing
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Windows (via chocolatey)
   choco install ffmpeg
   ```

3. **yt-dlp** - Installed via pip (included in requirements)

## Installation

1. **Clone/Download the project**
   ```bash
   cd comedy-clipper
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your Anthropic API key
   ```

## Usage

1. **Start the app**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Workflow**:
   - Enter a search query (e.g., "stand up comedy clips")
   - Browse results and select a video
   - Click "Analyze with AI" to get clip suggestions
   - Adjust clip times if needed
   - Download clips (regular or TikTok format)
   - Add your own commentary/overlays before posting!

## Project Structure

```
comedy-clipper/
├── app.py                 # Main Streamlit application
├── agents/
│   ├── __init__.py
│   ├── discovery.py       # YouTube search functionality
│   ├── analysis.py        # AI-powered clip analysis
│   └── download.py        # Video download and trimming
├── output/                # Downloaded clips go here
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

### Sidebar Settings

- **API Key**: Your Anthropic API key (required for AI analysis)
- **Output Directory**: Where clips are saved
- **Clip Length**: Min/max duration for suggested clips
- **Suggestions**: Number of clip suggestions per video

### Manual Mode

Don't want AI suggestions? Click "Manual Clip Selection" to set your own start/end times.

## Tips for Great Content

1. **Add Value**: Use the clips as a base, then add your own:
   - Commentary/reaction overlays
   - Text captions with your take
   - Intro/outro with your branding

2. **Keep Context**: The AI tries to suggest complete jokes/bits - don't cut mid-punchline!

3. **Credit Sources**: Consider adding the original creator's name in your caption

4. **TikTok Format**: Use the "TikTok format" download option for pre-sized 9:16 videos (adds letterboxing - you may want to crop/edit for best results)

## Troubleshooting

**"Couldn't get transcript"**
- Some videos don't have auto-captions
- Use manual clip selection instead

**"Download failed"**
- Check your internet connection
- Some videos may be region-restricted
- Try a different video

**Slow downloads**
- yt-dlp downloads can take time for longer videos
- The "Download Sections" feature may need to download more than just your clip

## Legal Note

This tool is for personal use. When using clips:
- Add transformative value (commentary, reaction, analysis)
- Credit original creators
- Be aware of copyright and fair use in your jurisdiction
- Don't just repost others' content without adding value

---

Made with ❤️ for content creators
