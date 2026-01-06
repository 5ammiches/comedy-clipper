"""
Comedy Clipper - AI-Powered Video Clip Discovery & Preparation Tool

A simple interface for discovering comedy clips on YouTube and preparing them
for TikTok/social media posting with your own commentary.
"""
import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.discovery import search_youtube, get_video_details
from agents.analysis import get_transcript, analyze_for_clips, format_timestamp
from agents.download import download_clip, optimize_for_tiktok

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Comedy Clipper",
    page_icon="🎬",
    layout="wide"
)

# =============================================================================
# INITIALIZE SESSION STATE
# =============================================================================
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'selected_video' not in st.session_state:
    st.session_state.selected_video = None
if 'clip_suggestions' not in st.session_state:
    st.session_state.clip_suggestions = []
if 'downloaded_clips' not in st.session_state:
    st.session_state.downloaded_clips = []


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def format_duration(seconds: int) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    if not seconds:
        return "Unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_views(views: int) -> str:
    """Format view count with K/M suffix."""
    if not views:
        return "Unknown views"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M views"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K views"
    return f"{views} views"


# =============================================================================
# SIDEBAR - Settings & Config
# =============================================================================
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key configuration
    api_key = st.text_input(
        "Open Router API Key",
        value=os.getenv("OPENROUTER_API_KEY", ""),
        type="password",
        help="Required for AI clip analysis. Get yours at https://openrouter.ai/"
    )
    if api_key:
        os.environ["OPENROUTER_API_KEY"] = api_key
    
    st.divider()
    
    # Output directory
    output_dir = st.text_input(
        "Output Directory",
        value="./output",
        help="Where to save downloaded clips"
    )
    
    # Clip settings
    st.subheader("Clip Settings")
    min_clip_length = st.slider("Min clip length (sec)", 10, 30, 15)
    max_clip_length = st.slider("Max clip length (sec)", 30, 120, 60)
    num_suggestions = st.slider("Suggestions per video", 1, 5, 3)
    
    st.divider()
    
    # Downloaded clips list
    st.subheader("📁 Downloaded Clips")
    if st.session_state.downloaded_clips:
        for clip in st.session_state.downloaded_clips[-5:]:  # Show last 5
            st.text(f"✅ {os.path.basename(clip)}")
    else:
        st.text("No clips downloaded yet")


# =============================================================================
# MAIN CONTENT
# =============================================================================
st.title("🎬 Comedy Clipper")
st.markdown("*Discover comedy clips, get AI-powered clip suggestions, and prepare content for your TikTok*")

# =============================================================================
# STEP 1: SEARCH
# =============================================================================
st.header("1️⃣ Search for Videos")

with st.form(key="search_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "Search YouTube",
            placeholder="e.g., stand up comedy, funny interviews, comedy sketches",
            label_visibility="collapsed"
        )
    with col2:
        search_button = st.form_submit_button("🔍 Search", use_container_width=True)

    # Advanced search options inside form
    with st.expander("Advanced Search Options"):
        col1, col2 = st.columns(2)
        with col1:
            duration_filter = st.selectbox(
                "Duration",
                options=[None, "short", "medium", "long"],
                format_func=lambda x: {
                    None: "Any duration",
                    "short": "Short (< 4 min)",
                    "medium": "Medium (4-20 min)",
                    "long": "Long (> 20 min)"
                }.get(x)
            )
        with col2:
            max_results = st.slider("Max results", 5, 20, 10)

if search_button and search_query:
    with st.spinner("Searching YouTube..."):
        try:
            results = search_youtube(
                query=search_query,
                max_results=max_results,
                duration_filter=duration_filter
            )
            st.session_state.search_results = results
            st.session_state.selected_video = None
            st.session_state.clip_suggestions = []
            if not results:
                st.warning("No results found. Try a different search term.")
        except Exception as e:
            st.error(f"Search error: {e}")

# Display search results
if st.session_state.search_results:
    st.subheader(f"Found {len(st.session_state.search_results)} videos")

    for i, video in enumerate(st.session_state.search_results):
        with st.container():
            col1, col2 = st.columns([1, 2])
            with col1:
                # Responsive embedded YouTube player using 16:9 aspect ratio container
                st.markdown(
                    f'''
                    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 8px;">
                        <iframe
                            src="https://www.youtube.com/embed/{video['id']}?rel=0"
                            style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;"
                            allowfullscreen>
                        </iframe>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(f"**{video['title']}**")
                st.caption(f"{video['channel']} • {format_views(video.get('view_count'))} • {format_duration(video.get('duration'))}")
                st.write("")  # Spacer
                if st.button("Select for Clipping", key=f"select_{i}", use_container_width=True):
                    st.session_state.selected_video = video
                    st.session_state.clip_suggestions = []
            st.divider()


# =============================================================================
# STEP 2: ANALYZE VIDEO
# =============================================================================
if st.session_state.selected_video:
    st.header("2️⃣ Analyze Video")
    
    video = st.session_state.selected_video
    
    st.markdown(f"### Selected: {video['title']}")
    st.markdown(f"🔗 [Watch on YouTube]({video['url']})")
    
    # Show video embed
    video_id = video.get('id')
    if video_id:
        st.video(f"https://www.youtube.com/watch?v={video_id}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Analyze with AI", use_container_width=True):
            if not os.getenv("OPENROUTER_API_KEY"):
                st.error("Please set your Open Router API key in the sidebar")
            else:
                with st.spinner("Getting transcript..."):
                    transcript = get_transcript(video['url'])
                
                if not transcript:
                    st.warning("Couldn't get transcript. AI analysis unavailable.")
                else:
                    with st.spinner("AI is analyzing for best clip moments..."):
                        suggestions = analyze_for_clips(
                            video_title=video['title'],
                            video_duration=video.get('duration', 300),
                            transcript=transcript,
                            target_clip_length=(min_clip_length, max_clip_length),
                            num_suggestions=num_suggestions
                        )
                        st.session_state.clip_suggestions = suggestions
    
    with col2:
        if st.button("⏱️ Manual Clip Selection", use_container_width=True):
            # Add a manual clip entry
            st.session_state.clip_suggestions.append({
                "start_seconds": 0,
                "end_seconds": min(60, video.get('duration', 60)),
                "description": "Manual selection - adjust times below",
                "suggested_caption": "",
                "manual": True
            })

# =============================================================================
# STEP 3: CLIP SUGGESTIONS
# =============================================================================
if st.session_state.clip_suggestions:
    st.header("3️⃣ Review & Download Clips")
    
    video = st.session_state.selected_video
    video_duration = video.get('duration', 600)
    
    for i, clip in enumerate(st.session_state.clip_suggestions):
        if 'error' in clip:
            st.error(f"Error: {clip['error']}")
            continue
        
        with st.container():
            st.markdown(f"### Clip {i + 1}")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Editable time range
                start_time = st.number_input(
                    "Start (seconds)",
                    min_value=0,
                    max_value=video_duration - 1,
                    value=clip['start_seconds'],
                    key=f"start_{i}"
                )
                end_time = st.number_input(
                    "End (seconds)",
                    min_value=1,
                    max_value=video_duration,
                    value=clip['end_seconds'],
                    key=f"end_{i}"
                )
                
                clip_duration = end_time - start_time
                st.caption(f"Clip duration: {clip_duration} seconds ({format_timestamp(start_time)} - {format_timestamp(end_time)})")
                
            with col2:
                st.markdown("**Why this clip:**")
                st.write(clip.get('description', 'No description'))
                
                if clip.get('suggested_caption'):
                    st.markdown("**Suggested caption:**")
                    st.info(clip['suggested_caption'])
            
            # Download buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Generate filename
                safe_title = "".join(c for c in video['title'][:30] if c.isalnum() or c in ' -_').strip()
                filename = f"{safe_title}_clip{i+1}_{start_time}s-{end_time}s"
                
                custom_name = st.text_input(
                    "Filename",
                    value=filename,
                    key=f"filename_{i}",
                    label_visibility="collapsed"
                )
            
            with col2:
                if st.button(f"⬇️ Download Clip", key=f"download_{i}", use_container_width=True):
                    with st.spinner("Downloading and trimming..."):
                        clip_path = download_clip(
                            video_url=video['url'],
                            start_seconds=start_time,
                            end_seconds=end_time,
                            output_dir=output_dir,
                            output_name=custom_name
                        )
                        
                        if clip_path:
                            st.success(f"✅ Saved: {clip_path}")
                            st.session_state.downloaded_clips.append(clip_path)
                        else:
                            st.error("Failed to download clip")
            
            with col3:
                if st.button(f"📱 Download (TikTok format)", key=f"tiktok_{i}", use_container_width=True):
                    with st.spinner("Downloading and converting to 9:16..."):
                        # First download the clip
                        temp_path = download_clip(
                            video_url=video['url'],
                            start_seconds=start_time,
                            end_seconds=end_time,
                            output_dir=output_dir,
                            output_name=f"{custom_name}_temp"
                        )
                        
                        if temp_path:
                            # Then convert to TikTok format
                            tiktok_path = optimize_for_tiktok(
                                temp_path,
                                os.path.join(output_dir, f"{custom_name}_tiktok.mp4")
                            )
                            
                            if tiktok_path:
                                st.success(f"✅ Saved: {tiktok_path}")
                                st.session_state.downloaded_clips.append(tiktok_path)
                                # Clean up temp file
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)
                            else:
                                st.error("Failed to convert to TikTok format")
                        else:
                            st.error("Failed to download clip")
            
            st.divider()


# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    <p>🎬 Comedy Clipper | Remember to add your own commentary & overlays before posting!</p>
    <p>Clips saved to: <code>{}</code></p>
</div>
""".format(os.path.abspath(output_dir)), unsafe_allow_html=True)
