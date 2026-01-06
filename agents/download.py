"""
Download & Trim Agent - Downloads videos and extracts clips using yt-dlp and ffmpeg
"""
import subprocess
import os
from datetime import datetime
from typing import Optional


def download_full_video(
    video_url: str,
    output_dir: str = "./clips",
    max_quality: str = "720"
) -> Optional[str]:
    """
    Download a full video from YouTube.
    
    Args:
        video_url: YouTube video URL
        output_dir: Directory to save the video
        max_quality: Maximum video quality (e.g., "720", "1080")
    
    Returns:
        Path to downloaded file or None if failed
    """
    os.makedirs(output_dir, exist_ok=True)
    
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    
    cmd = [
        "yt-dlp",
        video_url,
        "-f", f"bestvideo[height<={max_quality}]+bestaudio/best[height<={max_quality}]",
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--print", "after_move:filepath"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout
        )
        
        if result.returncode == 0:
            # Get the output filepath from stdout
            filepath = result.stdout.strip().split('\n')[-1]
            if os.path.exists(filepath):
                return filepath
        
        print(f"Download error: {result.stderr}")
        return None
        
    except subprocess.TimeoutExpired:
        print("Download timed out")
        return None
    except Exception as e:
        print(f"Download error: {e}")
        return None


def download_clip(
    video_url: str,
    start_seconds: int,
    end_seconds: int,
    output_dir: str = "./output",
    output_name: Optional[str] = None
) -> Optional[str]:
    """
    Download a specific segment of a video.
    
    Uses yt-dlp's built-in segment download for efficiency.
    
    Args:
        video_url: YouTube video URL
        start_seconds: Start time in seconds
        end_seconds: End time in seconds
        output_dir: Directory to save the clip
        output_name: Custom filename (without extension)
    
    Returns:
        Path to the clip file or None if failed
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if output_name:
        output_file = os.path.join(output_dir, f"{output_name}.mp4")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"clip_{timestamp}.mp4")
    
    # Method 1: Try yt-dlp with download sections (faster, less accurate)
    duration = end_seconds - start_seconds
    
    cmd = [
        "yt-dlp",
        video_url,
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "--merge-output-format", "mp4",
        "--download-sections", f"*{start_seconds}-{end_seconds}",
        "-o", output_file,
        "--force-keyframes-at-cuts"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0 and os.path.exists(output_file):
            return output_file
        
        # Method 2: Fallback - download full and trim with ffmpeg
        print("Trying fallback method: download + ffmpeg trim")
        return download_and_trim_fallback(
            video_url, start_seconds, end_seconds, output_file
        )
        
    except subprocess.TimeoutExpired:
        print("Download timed out")
        return None
    except Exception as e:
        print(f"Clip download error: {e}")
        return None


def download_and_trim_fallback(
    video_url: str,
    start_seconds: int,
    end_seconds: int,
    output_file: str
) -> Optional[str]:
    """
    Fallback method: Download full video then trim with ffmpeg.
    More reliable but slower.
    """
    temp_file = "/tmp/temp_video_for_trim.mp4"
    
    # Download full video
    cmd_download = [
        "yt-dlp",
        video_url,
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "--merge-output-format", "mp4",
        "-o", temp_file
    ]
    
    try:
        result = subprocess.run(
            cmd_download,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0 or not os.path.exists(temp_file):
            return None
        
        # Trim with ffmpeg
        trimmed = trim_video(temp_file, start_seconds, end_seconds, output_file)
        
        # Cleanup temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return trimmed
        
    except Exception as e:
        print(f"Fallback download error: {e}")
        return None


def trim_video(
    input_file: str,
    start_seconds: int,
    end_seconds: int,
    output_file: str
) -> Optional[str]:
    """
    Trim a video file using ffmpeg.
    
    Args:
        input_file: Path to input video
        start_seconds: Start time in seconds
        end_seconds: End time in seconds
        output_file: Path for output file
    
    Returns:
        Path to trimmed file or None if failed
    """
    duration = end_seconds - start_seconds
    
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-ss", str(start_seconds),  # Start time (before -i for fast seek)
        "-i", input_file,
        "-t", str(duration),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-movflags", "+faststart",  # Optimize for web playback
        "-loglevel", "error",
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0 and os.path.exists(output_file):
            return output_file
        
        print(f"Trim error: {result.stderr}")
        return None
        
    except Exception as e:
        print(f"Trim error: {e}")
        return None


def get_video_duration(filepath: str) -> Optional[int]:
    """Get duration of a video file in seconds."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return int(float(result.stdout.strip()))
    except:
        pass
    
    return None


def optimize_for_tiktok(
    input_file: str,
    output_file: Optional[str] = None
) -> Optional[str]:
    """
    Optimize a video for TikTok (9:16 aspect ratio, proper encoding).
    
    Note: This creates a letterboxed/pillarboxed version.
    For best results, the user should manually crop/edit.
    """
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_tiktok{ext}"
    
    # Pad to 9:16 aspect ratio
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-loglevel", "error",
        output_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(output_file):
            return output_file
    except Exception as e:
        print(f"TikTok optimization error: {e}")
    
    return None
