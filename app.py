import streamlit as st
import re
import time
import os
from pathlib import Path
import requests

# -----------------------
# Page Configuration
# -----------------------
st.set_page_config(
    page_title="Drive Slideshow Gallery",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------
# Custom CSS Theme
# -----------------------
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --background-dark: #0f172a;
        --background-light: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --accent: #f59e0b;
    }
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        border-radius: 1rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(99, 102, 241, 0.3);
    }
    
    .main-header h1 {
        color: white;
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }
    
    /* Enhanced slideshow container with centered frame layout */
    .slideshow-container {
        position: relative;
        max-width: 1400px;
        margin: 2rem auto;
        background: rgba(30, 41, 59, 0.6);
        border-radius: 1.5rem;
        padding: 3rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    /* Image frame with perfect centering */
    .image-frame {
        position: relative;
        width: 100%;
        max-width: 1200px;
        margin: 0 auto;
        background: #000;
        border-radius: 1rem;
        overflow: hidden;
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.7);
        border: 8px solid rgba(99, 102, 241, 0.3);
    }
    
    .image-frame img {
        display: block;
        width: 100%;
        height: auto;
        max-height: 70vh;
        object-fit: contain;
        background: #000;
    }
    
    /* Enhanced caption with slide counter */
    .image-caption {
        text-align: center;
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-top: 2rem;
        padding: 1.2rem 2rem;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
        border-radius: 0.75rem;
        border: 1px solid rgba(99, 102, 241, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
    }
    
    .slide-counter {
        display: inline-block;
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 2rem;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* Progress bar */
    .progress-container {
        width: 100%;
        height: 8px;
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
        overflow: hidden;
        margin: 1.5rem 0;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, var(--primary-color), var(--accent));
        border-radius: 4px;
        transition: width 0.3s ease;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.6);
    }
    
    /* Info cards */
    .info-card {
        background: var(--background-light);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 4px solid var(--primary-color);
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    .info-card h3 {
        color: var(--primary-color);
        margin-top: 0;
    }
    
    /* Simplified stats container for cleaner look */
    .stats-container {
        display: flex;
        justify-content: center;
        margin: 2rem 0 1rem 0;
        flex-wrap: wrap;
        gap: 1.5rem;
    }
    
    .stat-box {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
        padding: 1.2rem 2.5rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 5px 20px rgba(99, 102, 241, 0.2);
        border: 1px solid rgba(99, 102, 241, 0.3);
        backdrop-filter: blur(10px);
        min-width: 140px;
    }
    
    .stat-box h2 {
        color: var(--primary-color);
        font-size: 2.5rem;
        margin: 0;
        font-weight: 800;
        text-shadow: 0 2px 10px rgba(99, 102, 241, 0.4);
    }
    
    .stat-box p {
        color: var(--text-secondary);
        font-size: 0.95rem;
        margin: 0.5rem 0 0 0;
        font-weight: 500;
    }
    
    /* Control buttons styling */
    .stButton > button {
        border-radius: 0.75rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(99, 102, 241, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------
# Extract Folder ID
# -----------------------
def extract_folder_id(url: str):
    """Extract folder ID from various Google Drive URL formats"""
    patterns = [
        r'/folders/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'^([a-zA-Z0-9_-]+)$'
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError("Invalid Google Drive folder link.")

def get_gdrive_image_urls(folder_id: str):
    """
    Extract individual image URLs from a public Google Drive folder.
    Uses multiple methods to reliably fetch images from public folders.
    """
    images = []
    
    try:
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(folder_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            html_content = response.text
            
            # Method 1: Extract all 33-character file IDs from the page
            # Google Drive embeds file metadata in JavaScript data structures
            all_file_ids = re.findall(r'"([a-zA-Z0-9_-]{33})"', html_content)
            
            seen = set()
            for file_id in all_file_ids:
                if file_id != folder_id and file_id not in seen:
                    seen.add(file_id)
                    images.append({
                        "name": f"Image {len(images)+1}.jpg",
                        "url": f"https://drive.google.com/uc?export=view&id={file_id}",
                        "source": "gdrive",
                        "file_id": file_id
                    })
            
            # Method 2: Also search for 28-character file IDs (alternative format)
            if len(images) < 50:
                alt_file_ids = re.findall(r'"([a-zA-Z0-9_-]{28})"', html_content)
                for file_id in alt_file_ids:
                    if file_id != folder_id and file_id not in seen and len(file_id) == 28:
                        seen.add(file_id)
                        images.append({
                            "name": f"Image {len(images)+1}.jpg",
                            "url": f"https://drive.google.com/uc?export=view&id={file_id}",
                            "source": "gdrive",
                            "file_id": file_id
                        })
            
            # Method 3: Search for file IDs in data attributes and JSON structures
            if len(images) < 50:
                json_pattern = r'\["([a-zA-Z0-9_-]{25,})"'
                json_ids = re.findall(json_pattern, html_content)
                for file_id in json_ids:
                    if file_id != folder_id and file_id not in seen and len(file_id) >= 25:
                        seen.add(file_id)
                        images.append({
                            "name": f"Image {len(images)+1}.jpg",
                            "url": f"https://drive.google.com/uc?export=view&id={file_id}",
                            "source": "gdrive",
                            "file_id": file_id
                        })
        
        if images:
            st.success(f"✅ Found {len(images)} images in Google Drive folder")
            return images
        else:
            st.warning("⚠️ Could not find images. Please ensure:")
            st.markdown("""
            - Folder sharing: "Anyone with the link can view"
            - Folder contains image files
            - Use folder ID: `1LfSwuD7WxbS0ZdDeGo0hpiviUx6vMhqs`
            """)
        
        return []
        
    except Exception as e:
        st.error(f"❌ Error loading from Google Drive: {str(e)}")
        st.info("💡 Try using just the folder ID instead of the full URL")
        return []

# -----------------------
# Get Public Drive Images
# -----------------------
def get_public_drive_images(folder_id: str):
    """
    Get publicly accessible images from Google Drive folder.
    Works with folders that have 'Anyone with the link can view' permission.
    """
    return get_gdrive_image_urls(folder_id)

# -----------------------
# Initialize Session State
# -----------------------
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'autoplay' not in st.session_state:
    st.session_state.autoplay = False
if 'images' not in st.session_state:
    st.session_state.images = []
if 'slideshow_speed' not in st.session_state:
    st.session_state.slideshow_speed = 3
if 'loop_mode' not in st.session_state:
    st.session_state.loop_mode = True

# -----------------------
# Header
# -----------------------
st.markdown("""
<div class="main-header">
    <h1>🎬 Drive Slideshow Gallery</h1>
    <p>View images from Google Drive public folders (no auth required)</p>
</div>
""", unsafe_allow_html=True)

# -----------------------
# Sidebar Configuration
# -----------------------
with st.sidebar:
    st.markdown("## 🎨 Configuration")
    
    st.markdown("### 📁 Google Drive Folder")
    folder_url = st.text_input(
        "🔗 Folder URL/ID",
        value="https://drive.google.com/drive/folders/1LfSwuD7WxbS0ZdDeGo0hpiviUx6vMhqs?usp=share_link",
        placeholder="Paste your public folder link here...",
        help="Folder must have 'Anyone with the link can view' permission"
    )
    
    st.markdown("---")
    
    st.markdown("## ⚙️ Slideshow Settings")
    
    slideshow_speed = st.slider(
        "⏱️ Slide Duration (seconds)",
        min_value=1,
        max_value=15,
        value=st.session_state.slideshow_speed,
        help="How long each image is displayed"
    )
    st.session_state.slideshow_speed = slideshow_speed
    
    loop_mode = st.checkbox(
        "🔁 Loop Slideshow", 
        value=st.session_state.loop_mode,
        help="Automatically restart from beginning after last slide"
    )
    st.session_state.loop_mode = loop_mode
    
    show_info = st.checkbox("ℹ️ Show Image Details", value=True)
    
    st.markdown("---")
    
    if st.session_state.images:
        st.markdown("## 📊 Gallery Stats")
        total_images = len(st.session_state.images)
        current_pos = st.session_state.current_index + 1
        
        st.metric("Total Items", total_images)
        st.metric("Current Position", f"{current_pos} of {total_images}")
        st.progress(current_pos / total_images)
        
        if st.session_state.loop_mode:
            st.success("🔁 Loop Mode: ON")
        else:
            st.info("🔁 Loop Mode: OFF")

# -----------------------
# Load Images
# -----------------------
if st.button("🚀 Load Gallery", type="primary", use_container_width=True):
    with st.spinner("🔄 Loading images..."):
        all_images = []
        
        # Load Google Drive images
        if folder_url:
            try:
                folder_id = extract_folder_id(folder_url)
                gdrive_imgs = get_public_drive_images(folder_id)
                all_images.extend(gdrive_imgs)
                st.success(f"✅ Loaded {len(gdrive_imgs)} images from Google Drive")
            except Exception as e:
                st.error(f"❌ Error loading Google Drive: {str(e)}")
        else:
            st.error("❌ Please provide a Google Drive folder URL or ID")
        
        st.session_state.images = all_images
        st.session_state.current_index = 0
        
        if all_images:
            st.balloons()

# -----------------------
# Slideshow Display
# -----------------------
if st.session_state.images and st.session_state.current_index < len(st.session_state.images):
    imgs = st.session_state.images
    total = len(imgs)
    idx = st.session_state.current_index
    
    st.markdown(f"""
    <div class="stats-container">
        <div class="stat-box">
            <h2>{idx + 1}/{total}</h2>
            <p>Current Slide</p>
        </div>
        <div class="stat-box">
            <h2>{round((idx + 1) / total * 100)}%</h2>
            <p>Progress</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    progress_percentage = ((idx + 1) / total) * 100
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {progress_percentage}%"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="slideshow-container">', unsafe_allow_html=True)
    
    current_item = imgs[idx]
    
    st.markdown('<div class="image-frame">', unsafe_allow_html=True)
    
    if current_item["source"] == "gdrive" and "url" in current_item:
        # Try multiple URL formats for Google Drive
        file_id = current_item.get("file_id", "")
        
        # Try different Google Drive URL formats
        urls_to_try = [
            f"https://drive.google.com/uc?export=view&id={file_id}",
            f"https://lh3.googleusercontent.com/d/{file_id}",
            f"https://drive.google.com/thumbnail?id={file_id}&sz=w2000",
            f"https://drive.google.com/uc?export=download&id={file_id}",
        ]
        
        image_loaded = False
        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=10, allow_redirects=True)
                content_type = response.headers.get('Content-Type', '')
                
                if response.status_code == 200 and 'image' in content_type:
                    from PIL import Image
                    from io import BytesIO
                    
                    img = Image.open(BytesIO(response.content))
                    st.image(img, width="stretch")
                    image_loaded = True
                    break
            except Exception as e:
                continue
        
        if not image_loaded:
            st.error(f"❌ Unable to load image: {current_item['name']}")
            st.info(f"💡 File ID: {file_id}")
            st.markdown(f"[Open in Google Drive](https://drive.google.com/file/d/{file_id}/view)")

    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="image-caption">
        <span class="slide-counter">{idx + 1} / {total}</span>
        <span>☁️ {current_item["name"]}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### 🎮 Slideshow Controls")
    col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 1.5])
    
    with col1:
        if st.button("⏮️ First", use_container_width=True):
            st.session_state.current_index = 0
            st.rerun()
    
    with col2:
        if st.button("⬅️ Prev", use_container_width=True):
            if idx == 0 and st.session_state.loop_mode:
                st.session_state.current_index = total - 1
            else:
                st.session_state.current_index = max(0, idx - 1)
            st.rerun()
    
    with col3:
        if st.button("⏸️ Pause" if st.session_state.autoplay else "▶️ Play", use_container_width=True, type="primary"):
            st.session_state.autoplay = not st.session_state.autoplay
            st.rerun()
    
    with col4:
        if st.button("➡️ Next", use_container_width=True):
            if idx == total - 1 and st.session_state.loop_mode:
                st.session_state.current_index = 0
            else:
                st.session_state.current_index = min(total - 1, idx + 1)
            st.rerun()
    
    with col5:
        if st.button("⏭️ Last", use_container_width=True):
            st.session_state.current_index = total - 1
            st.rerun()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Shuffle", use_container_width=True):
            import random
            st.session_state.current_index = random.randint(0, total - 1)
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop & Reset", use_container_width=True):
            st.session_state.autoplay = False
            st.session_state.current_index = 0
            st.rerun()
    
    with col3:
        jump_to = st.selectbox(
            "Jump to slide:",
            range(1, total + 1),
            index=idx,
            label_visibility="collapsed"
        )
        if jump_to != idx + 1:
            st.session_state.current_index = jump_to - 1
            st.rerun()
    
    # Show details in expander to keep view clean
    if show_info:
        with st.expander("📋 View Item Details"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Name", current_item["name"])
            with col2:
                st.metric("Source", "GOOGLE DRIVE")
            with col3:
                st.metric("Position", f"{idx + 1} of {total}")
    
    if st.session_state.autoplay:
        time.sleep(slideshow_speed)
        # If at last slide, loop back to start if loop mode is on
        if idx == total - 1 and st.session_state.loop_mode:
            st.session_state.current_index = 0
        elif idx < total - 1:
            st.session_state.current_index = idx + 1
        else:
            # At end and no loop - stop autoplay
            st.session_state.autoplay = False
        st.rerun()

else:
    # Welcome screen
    st.markdown("""
    <div class="info-card">
        <h3>👋 Welcome to Drive Slideshow Gallery!</h3>
        <p>Get started by following these steps:</p>
        <ol>
            <li>🔗 Paste your Google Drive public folder URL or ID in the sidebar</li>
            <li>🚀 Click "Load Gallery" to start</li>
            <li>▶️ Use the controls to navigate or enable autoplay</li>
        </ol>
        <p><strong>Features:</strong></p>
        <ul>
            <li>✨ No authentication required</li>
            <li>☁️ Support for public Google Drive folders</li>
            <li>⏯️ Auto-play with customizable timing</li>
            <li>📊 Real-time progress tracking</li>
            <li>🎨 Beautiful dark theme with gradients</li>
            <li>🔀 Shuffle mode for random viewing</li>
            <li>🔁 Loop mode for continuous slideshow</li>
        </ul>
        <p><strong>Setup Instructions:</strong></p>
        <ul>
            <li>🔓 Ensure folder has "Anyone with the link can view" permission</li>
            <li>📂 Folder should contain image files (PNG, JPG, GIF, etc.)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo stats
    st.markdown("""
    <div class="stats-container">
        <div class="stat-box">
            <h2>🎬</h2>
            <p>Ready to Start</p>
        </div>
        <div class="stat-box">
            <h2>∞</h2>
            <p>Unlimited Images</p>
        </div>
        <div class="stat-box">
            <h2>⚡</h2>
            <p>No Auth Needed</p>
        </div>
        <div class="stat-box">
            <h2>🔁</h2>
            <p>Loop Mode Available</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
