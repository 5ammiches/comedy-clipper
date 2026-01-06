"""
Analysis Agent - Uses AI to analyze videos and suggest clip segments
"""
import subprocess
import json
import os
from typing import Optional
from openai import OpenAI


def get_transcript(video_url: str) -> Optional[str]:
    """
    Extract transcript/subtitles from a YouTube video.
    
    Returns the transcript text or None if unavailable.
    """
    cmd = [
        "yt-dlp",
        video_url,
        "--write-auto-sub",
        "--sub-lang", "en",
        "--skip-download",
        "--output", "/tmp/transcript_temp",
        "--convert-subs", "srt"
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, timeout=60)
        
        # Look for the generated subtitle file
        for ext in [".en.srt", ".en.vtt", ".srt", ".vtt"]:
            transcript_path = f"/tmp/transcript_temp{ext}"
            if os.path.exists(transcript_path):
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                os.remove(transcript_path)
                return parse_srt(content)
        
        return None
        
    except Exception as e:
        print(f"Transcript extraction error: {e}")
        return None


def parse_srt(srt_content: str) -> str:
    """Parse SRT content into plain text with timestamps."""
    lines = srt_content.strip().split('\n')
    transcript_parts = []
    current_time = None
    
    for line in lines:
        line = line.strip()
        if '-->' in line:
            current_time = line.split('-->')[0].strip()
        elif line and not line.isdigit() and current_time:
            # Remove HTML tags
            clean_line = line.replace('<i>', '').replace('</i>', '')
            transcript_parts.append(f"[{current_time}] {clean_line}")
    
    return '\n'.join(transcript_parts)


def analyze_for_clips(
    video_title: str,
    video_duration: int,
    transcript: str,
    target_clip_length: tuple[int, int] = (15, 60),
    num_suggestions: int = 3
) -> list[dict]:
    """
    Use AI (via Open Router) to analyze transcript and suggest clip segments.

    Args:
        video_title: Title of the video
        video_duration: Total duration in seconds
        transcript: Video transcript with timestamps
        target_clip_length: (min_seconds, max_seconds) for clips
        num_suggestions: Number of clip suggestions to generate

    Returns:
        List of suggested clips with start/end times and descriptions
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return [{
            "error": "OPENROUTER_API_KEY not set",
            "suggestion": "Set your API key in the .env file"
        }]

    # Initialize OpenAI client with Open Router endpoint
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    
    prompt = f"""Analyze this comedy video transcript and identify the {num_suggestions} best moments that would make engaging short clips for TikTok/social media.

VIDEO TITLE: {video_title}
TOTAL DURATION: {video_duration} seconds
TARGET CLIP LENGTH: {target_clip_length[0]}-{target_clip_length[1]} seconds

TRANSCRIPT:
{transcript[:8000]}  # Truncate if too long

For each suggested clip, provide:
1. Start timestamp (in seconds)
2. End timestamp (in seconds)  
3. A brief description of why this moment is clip-worthy
4. Suggested caption/hook for TikTok

Return your response as a JSON array with this structure:
[
  {{
    "start_seconds": 45,
    "end_seconds": 72,
    "description": "Comedian delivers perfect punchline about...",
    "suggested_caption": "When your mom says..."
  }}
]

Focus on:
- Complete jokes/bits (don't cut mid-punchline)
- Moments with strong reactions or punchlines
- Self-contained segments that make sense without full context
- Engaging openings that hook viewers

Return ONLY the JSON array, no other text."""

    try:
        # Using Open Router - you can change the model to any available on Open Router
        # Popular options: anthropic/claude-3.5-sonnet, openai/gpt-4-turbo, google/gemini-pro
        response = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",  # Claude via Open Router
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        if response_text.startswith('['):
            clips = json.loads(response_text)
        else:
            # Try to find JSON array in response
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            if start != -1 and end > start:
                clips = json.loads(response_text[start:end])
            else:
                return []
        
        # Validate and clean up suggestions
        valid_clips = []
        for clip in clips:
            if all(k in clip for k in ['start_seconds', 'end_seconds']):
                clip['start_seconds'] = max(0, int(clip['start_seconds']))
                clip['end_seconds'] = min(video_duration, int(clip['end_seconds']))
                if clip['end_seconds'] > clip['start_seconds']:
                    valid_clips.append(clip)
        
        return valid_clips
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return []


def format_timestamp(seconds: int) -> str:
    """Convert seconds to HH:MM:SS format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
