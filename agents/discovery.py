"""
Discovery Agent - Searches YouTube for videos based on topic/keywords
"""
import subprocess
import json
import re
import urllib.parse
from typing import Optional

import requests


def search_youtube(
    query: str,
    max_results: int = 10,
    duration_filter: Optional[str] = None
) -> list[dict]:
    """
    Search YouTube for videos matching a query using web scraping.

    Args:
        query: Search query (e.g., "stand up comedy clips")
        max_results: Maximum number of results to return
        duration_filter: Filter by duration - "short" (<4min), "medium" (4-20min), "long" (>20min)

    Returns:
        List of video metadata dictionaries
    """
    try:
        # Build search URL
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"

        # Add duration filter to URL if specified
        if duration_filter == "short":
            url += "&sp=EgIYAQ%3D%3D"  # Under 4 minutes
        elif duration_filter == "medium":
            url += "&sp=EgIYAw%3D%3D"  # 4-20 minutes
        elif duration_filter == "long":
            url += "&sp=EgIYAg%3D%3D"  # Over 20 minutes

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # Extract the ytInitialData JSON from the page
        match = re.search(r'var ytInitialData = ({.*?});</script>', response.text)
        if not match:
            # Try alternate pattern
            match = re.search(r'ytInitialData\s*=\s*({.*?});\s*</script>', response.text)

        if not match:
            print("Could not find ytInitialData in response")
            return []

        data = json.loads(match.group(1))

        # Navigate to video results
        videos = []
        try:
            contents = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]

            for section in contents:
                if "itemSectionRenderer" in section:
                    items = section["itemSectionRenderer"]["contents"]
                    for item in items:
                        if "videoRenderer" in item:
                            video = item["videoRenderer"]
                            video_id = video.get("videoId")
                            if not video_id:
                                continue

                            # Parse duration
                            duration_text = video.get("lengthText", {}).get("simpleText", "0:00")
                            duration_seconds = parse_duration(duration_text)

                            # Parse view count
                            view_text = video.get("viewCountText", {}).get("simpleText", "0 views")
                            view_count = parse_view_count(view_text)

                            videos.append({
                                "id": video_id,
                                "title": video.get("title", {}).get("runs", [{}])[0].get("text", "Unknown"),
                                "url": f"https://www.youtube.com/watch?v={video_id}",
                                "duration": duration_seconds,
                                "channel": video.get("ownerText", {}).get("runs", [{}])[0].get("text", "Unknown"),
                                "view_count": view_count,
                                "description": get_description(video),
                                "thumbnail": get_thumbnail(video),
                            })

                            if len(videos) >= max_results:
                                break

                    if len(videos) >= max_results:
                        break
        except (KeyError, IndexError) as e:
            print(f"Error parsing YouTube data: {e}")
            return []

        return videos

    except requests.RequestException as e:
        print(f"Request error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return []
    except Exception as e:
        print(f"Search error: {e}")
        return []


def parse_duration(duration_text: str) -> int:
    """Convert duration text like '5:30' or '1:23:45' to seconds."""
    try:
        parts = duration_text.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, IndexError):
        pass
    return 0


def parse_view_count(view_text: str) -> int:
    """Parse view count from text like '1.2M views' or '500K views'."""
    try:
        # Remove 'views' and extra text
        view_text = view_text.lower().replace("views", "").replace(",", "").strip()

        if "m" in view_text:
            return int(float(view_text.replace("m", "")) * 1_000_000)
        elif "k" in view_text:
            return int(float(view_text.replace("k", "")) * 1_000)
        elif view_text.isdigit():
            return int(view_text)
    except (ValueError, AttributeError):
        pass
    return 0


def get_description(video: dict) -> str:
    """Extract description snippet from video data."""
    try:
        snippets = video.get("detailedMetadataSnippets", [])
        if snippets:
            runs = snippets[0].get("snippetText", {}).get("runs", [])
            return "".join(r.get("text", "") for r in runs)[:500]
    except (KeyError, IndexError):
        pass
    return ""


def get_thumbnail(video: dict) -> str:
    """Extract thumbnail URL from video data."""
    try:
        thumbnails = video.get("thumbnail", {}).get("thumbnails", [])
        if thumbnails:
            # Get highest quality thumbnail
            return thumbnails[-1].get("url", "")
    except (KeyError, IndexError):
        pass
    return ""


def filter_by_duration(videos: list[dict], duration_filter: str) -> list[dict]:
    """Filter videos by duration category."""
    filtered = []
    for video in videos:
        duration = video.get("duration") or 0
        if duration_filter == "short" and duration < 240:
            filtered.append(video)
        elif duration_filter == "medium" and 240 <= duration <= 1200:
            filtered.append(video)
        elif duration_filter == "long" and duration > 1200:
            filtered.append(video)
        elif duration_filter is None:
            filtered.append(video)
    return filtered if filtered else videos


def get_video_details(video_url: str) -> dict:
    """Get detailed metadata for a specific video."""
    cmd = [
        "yt-dlp",
        video_url,
        "--dump-json",
        "--no-download",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "id": data.get("id"),
                "title": data.get("title"),
                "url": video_url,
                "duration": data.get("duration"),
                "channel": data.get("channel") or data.get("uploader"),
                "view_count": data.get("view_count"),
                "description": data.get("description", ""),
                "upload_date": data.get("upload_date"),
                "categories": data.get("categories", []),
                "tags": data.get("tags", []),
            }
    except Exception as e:
        print(f"Error getting video details: {e}")

    return {}
