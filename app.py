import streamlit as st
import requests
import re
import time
import random
import io
from PIL import Image
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ============================================================================
# Configuration and Constants
# ============================================================================

DEFAULT_FOLDERS = {
    "Folder 1": "https://drive.google.com/drive/folders/1vP6zhJVq68CnT0SVUS8dQALC7tOSrMqN?usp=share_link",
    "Folder 2": "https://drive.google.com/drive/folders/1fbHjKWNRleTk2giAQiCGR9s8V0VE14IO?usp=share_link",
    "Folder 3": "https://drive.google.com/drive/folders/10e7Swca0GHr6bIQ6_M6JRs4WBqZ4K7iJ?usp=share_link"
}

DEFAULT_FOLDER_URL = "https://drive.google.com/drive/folders/1vP6zhJVq68CnT0SVUS8dQALC7tOSrMqN?usp=share_link"

# API Configuration
API_BASE_URL = "https://api.kie.ai/api/v1/jobs"
API_FALLBACK_URL = "https://zyloai.xyz"  # Fallback if primary fails
API_HEADERS = {"Content-Type": "application/json"}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RETRY_BACKOFF = 2  # exponential backoff multiplier

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title="Drive Slideshow & AI Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Custom CSS Theme - Complete Styling
# ============================================================================
st.markdown("""
<style>
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --background-dark: #0f172a;
        --background-light: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --accent: #f59e0b;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
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
    
    .image-card {
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 15px;
        background: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        margin-bottom: 20px;
        height: 100%;
    }
    
    .image-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        border-color: #4CAF50;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .status-success {
        background-color: #28a745;
        color: white;
    }
    
    .status-waiting {
        background-color: #ffc107;
        color: black;
    }
    
    .status-fail {
        background-color: #dc3545;
        color: white;
    }
    
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 10px 0;
    }
    
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #17a2b8;
        margin: 10px 0;
    }

    /* New styles for stats bar */
    .stats-bar {
        display: flex;
        justify-content: space-around;
        margin: 1.5rem 0;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.3);
    }

    /* Page Header */
    .page-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        border-radius: 1rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.3);
    }

    .page-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Configuration
# ============================================================================
# Moved DEFAULT_FOLDER_URL and DEFAULT_FOLDERS to Configuration section
# DEFAULT_FOLDER_URL = 'https://drive.google.com/drive/folders/1vP6zhJVq68CnT0SVUS8dQALC7tOSrMqN?usp=share_link'
# BASE_URL = "https://api.kie.ai/api/v1/jobs" # Removed, replaced by API_BASE_URL
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# ============================================================================
# Session State Initialization
# ============================================================================
def init_session_state():
    """Initialize all session state variables with enhanced persistence."""
    defaults = {
        'default_folder_url': DEFAULT_FOLDER_URL,
        'current_index': 0,
        'autoplay': False,
        'images': [],
        'slideshow_speed': 3,
        'loop_mode': True,
        'current_page': 'Slideshow',
        'api_key': '',
        'selected_images': [],  # Master list - all images selected across pages
        'selected_slideshow_images': [],  # Images selected from slideshow
        'selected_library_images': [],  # Images selected from library
        'selected_history_images': [],  # Images selected from history
        'task_history': [],
        'library_images': [],
        'library_view_mode': 'Grid',  
        'library_sort_by': 'Newest First',
        'saved_folders': {
            'Folder 1': 'https://drive.google.com/drive/folders/1fbHjKWNRleTk2giAQiCGR9s8V0VE14IO?usp=share_link',
            'Folder 2': 'https://drive.google.com/drive/folders/1vP6zhJVq68CnT0SVUS8dQALC7tOSrMqN?usp=share_link',
            'Folder 3': 'https://drive.google.com/drive/folders/10e7Swca0GHr6bIQ6_M6JRs4WBqZ4K7iJ?usp=share_link'
        },
        'gdrive_authenticated': False,
        'gdrive_folder_id': None,
        'gdrive_folder_name': 'Generated Images',
        'auto_upload': False,
        'show_api_input': False,
        'service_account_info': None,
        'credentials': None,
        'service': None,
        'polling_active': False,
        'current_task': None,
        'stats': {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_images': 0,
            'uploaded_images': 0
        },
        'selected_image_for_edit': None,
        'edit_mode': None,
        'image_preview_cache': {},  # Cache normalized image data by ID
        'url_cache': {},  # Cache best URLs by image ID
        'editing_folder': None,
        'show_folder_manager': False,
        'last_loaded_folder': None,
        'generation_preview_images': [],
        'library_loaded': False,
        'all_library_images': [],
        'library_source_filter': 'All',
        'library_filter_type': 'All',
        'selection_metadata': {},  # Store metadata about when/where images were selected
        'page_view_history': [],  # Track page navigation history
        'last_selection_sync': None,  # Timestamp of last selection sync
        'show_selection_breakdown': False, # Toggle for selection breakdown view
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# Selection State Management Functions
# ============================================================================

def sync_master_selection():
    """Sync all selection sources into master selected_images list."""
    master_selection = []
    seen_ids = set()
    
    # Combine from all sources
    all_sources = [
        ('slideshow', st.session_state.get('selected_slideshow_images', [])),
        ('library', st.session_state.get('selected_library_images', [])),
        ('history', st.session_state.get('selected_history_images', []))
    ]
    
    for source_name, source_list in all_sources:
        for img in source_list:
            img_id = get_image_id(img)
            if img_id not in seen_ids:
                # Ensure image is normalized and cached
                normalized = get_or_cache_normalized_image(img)
                if normalized:
                    # Add metadata about source
                    if 'selection_source' not in normalized:
                        normalized['selection_source'] = source_name
                    master_selection.append(normalized)
                    seen_ids.add(img_id)
    
    st.session_state.selected_images = master_selection
    st.session_state.last_selection_sync = time.time()
    return master_selection

def get_image_id(img):
    """Get unique ID for an image from various possible fields."""
    if isinstance(img, dict):
        return (
            img.get('id') or 
            img.get('file_id') or 
            img.get('task_id') or
            img.get('url') or
            img.get('name') or
            str(hash(str(img))) # Fallback hash for completely unknown objects
        )
    elif isinstance(img, str):
        return img # If it's just a URL string
    return str(hash(str(img))) # Fallback for non-dict/non-string types

def get_or_cache_normalized_image(img):
    """Get normalized image from cache or normalize and cache it."""
    img_id = get_image_id(img)
    
    # Check cache first
    if img_id in st.session_state.image_preview_cache:
        cached = st.session_state.image_preview_cache[img_id]
        # Verify cached data is still valid
        if cached and isinstance(cached, dict) and cached.get('url'):
            return cached
    
    # Normalize and cache
    normalized = normalize_image_urls(img)
    if normalized and isinstance(normalized, dict):
        st.session_state.image_preview_cache[img_id] = normalized
        # Also cache best URL
        best_url = get_best_streamlit_url(normalized)
        if best_url:
            st.session_state.url_cache[img_id] = best_url
        return normalized
    
    return None

def add_to_selection(img, source='unknown'):
    """Add image to appropriate selection list with validation."""
    normalized = get_or_cache_normalized_image(img)
    if not normalized:
        return False
    
    # Add source tracking
    normalized['selection_source'] = source
    normalized['selection_time'] = time.time()
    
    img_id = get_image_id(normalized)
    
    # Add to appropriate source list
    if source == 'slideshow':
        target_list_key = 'selected_slideshow_images'
    elif source == 'library':
        target_list_key = 'selected_library_images'
    elif source == 'history':
        target_list_key = 'selected_history_images'
    else:
        target_list_key = 'selected_images' # Master list (shouldn't usually add directly)
    
    target_list = st.session_state.get(target_list_key, [])
    
    # Check if already in list
    if not any(get_image_id(existing) == img_id for existing in target_list):
        target_list.append(normalized)
        st.session_state[target_list_key] = target_list
        sync_master_selection()
        return True
    
    return False

def remove_from_selection(img, source='unknown'):
    """Remove image from appropriate selection list."""
    img_id = get_image_id(img)
    
    # Remove from appropriate source list
    if source == 'slideshow':
        target_list_key = 'selected_slideshow_images'
    elif source == 'library':
        target_list_key = 'selected_library_images'
    elif source == 'history':
        target_list_key = 'selected_history_images'
    else:
        target_list_key = 'selected_images' # Master list
    
    target_list = st.session_state.get(target_list_key, [])
    
    # Filter out the image to remove
    st.session_state[target_list_key] = [img for img in target_list if get_image_id(img) != img_id]
    
    sync_master_selection()

def is_image_selected(img, source=None):
    """Check if image is selected in any list or specific source."""
    img_id = get_image_id(img)
    
    if source:
        if source == 'slideshow':
            check_list = st.session_state.get('selected_slideshow_images', [])
        elif source == 'library':
            check_list = st.session_state.get('selected_library_images', [])
        elif source == 'history':
            check_list = st.session_state.get('selected_history_images', [])
        else:
            check_list = st.session_state.get('selected_images', []) # Check master list if source is general
        
        return any(get_image_id(existing) == img_id for existing in check_list)
    else:
        # Check all lists if no source specified
        all_selected_in_master = st.session_state.get('selected_images', [])
        return any(get_image_id(existing) == img_id for existing in all_selected_in_master)

def get_total_selected_count():
    """Get total number of unique selected images across all sources."""
    sync_master_selection()
    return len(st.session_state.get('selected_images', []))

def clear_all_selections():
    """Clear all image selections from all sources."""
    st.session_state.selected_images = []
    st.session_state.selected_slideshow_images = []
    st.session_state.selected_library_images = []
    st.session_state.selected_history_images = []
    st.session_state.image_preview_cache = {} # Clear image cache
    st.session_state.url_cache = {} # Clear URL cache
    st.session_state.last_selection_sync = time.time()

def render_selection_preview_banner():
    """Render a persistent banner showing selected images across all pages."""
    total_selected = get_total_selected_count()
    
    if total_selected == 0:
        return
    
    # Dynamic class based on current page for styling context
    current_page = st.session_state.current_page.lower()
    banner_style = f"banner-{current_page}"

    st.markdown(f"""
    <div class='selection-banner {banner_style}' style='background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color:white;padding:16px;border-radius:12px;margin-bottom:20px;
                box-shadow:0 4px 12px rgba(102,126,234,0.3);'>
        <div style='display:flex;justify-content:space-between;align-items:center;'>
            <div>
                <h3 style='margin:0;font-size:18px;'>🎯 {total_selected} Image{'' if total_selected == 1 else 's'} Selected</h3>
                <p style='margin:4px 0 0 0;opacity:0.9;font-size:14px;'>Ready for AI generation.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Expandable preview
    with st.expander(f"👁️ Preview All {total_selected} Selected Images", expanded=False):
        selected_imgs = st.session_state.get('selected_images', [])
        if selected_imgs:
            cols = st.columns(min(6, len(selected_imgs)))
            for i, img in enumerate(selected_imgs[:12]):  # Show max 12 in preview
                with cols[i % 6]:
                    # Use the cached normalized image if available
                    cached_img = get_or_cache_normalized_image(img)
                    if cached_img:
                        display_image_with_fallback(cached_img, caption=f"#{i+1}", show_source=False, width=100)
                        source = img.get('selection_source', 'unknown')
                        st.caption(f"From: {source}")
            
            if len(selected_imgs) > 12:
                st.info(f"... and {len(selected_imgs) - 12} more images")
            
            # Action buttons
            action_cols = st.columns([2, 2, 1])
            with action_cols[0]:
                if st.button("➡️ Go to Generate Page", key="banner_goto_generate", use_container_width=True):
                    st.session_state.current_page = "Generate"
                    st.rerun()
            with action_cols[1]:
                if st.button("📋 View Breakdown", key="banner_breakdown", use_container_width=True):
                    st.session_state.show_selection_breakdown = not st.session_state.get('show_selection_breakdown', False)
                    st.rerun()
            with action_cols[2]:
                if st.button("🗑️ Clear All", key="banner_clear", use_container_width=True):
                    clear_all_selections()
                    st.rerun()
            
            # Show breakdown if toggled
            if st.session_state.get('show_selection_breakdown', False):
                st.markdown("#### 📊 Selection Breakdown")
                breakdown_cols = st.columns(3)
                with breakdown_cols[0]:
                    slideshow_count = len(st.session_state.get('selected_slideshow_images', []))
                    st.metric("From Slideshow", slideshow_count)
                with breakdown_cols[1]:
                    library_count = len(st.session_state.get('selected_library_images', []))
                    st.metric("From Library", library_count)
                with breakdown_cols[2]:
                    history_count = len(st.session_state.get('selected_history_images', []))
                    st.metric("From History", history_count)

# ============================================================================
# Utility Functions
# ============================================================================

def normalize_image_urls(image_data):
    """
    Normalize and enhance image data with all URL variants for maximum compatibility.
    Ensures consistent URL structure across all pages and selections.
    """
    if not image_data:
        return None
    
    # Ensure image_data is a dictionary
    if not isinstance(image_data, dict):
        # Attempt to convert if it's a string URL
        if isinstance(image_data, str) and image_data.startswith('http'):
            image_data = {'url': image_data, 'name': 'Unknown'}
        else:
            return None  # Return None instead of empty dict

    file_id = (
        image_data.get('id') or 
        image_data.get('file_id') or 
        image_data.get('fileId')
    )
    
    # Ensure we have a file_id stored
    if file_id:
        image_data['file_id'] = file_id
        image_data['id'] = file_id  # Ensure both fields exist
        
        # Generate all possible URL formats
        image_data['drive_direct_link'] = f"https://lh3.googleusercontent.com/d/{file_id}"
        image_data['drive_public_url'] = f"https://drive.google.com/uc?export=view&id={file_id}"
        image_data['drive_thumbnail_url'] = f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"
        image_data['high_res_thumbnail'] = f"https://drive.google.com/thumbnail?id={file_id}&sz=w2000"
        image_data['drive_web_view'] = f"https://drive.google.com/file/d/{file_id}/view"
        
        # Set primary URL if not already set
        if not image_data.get('url'):
            image_data['url'] = image_data['drive_direct_link']
        
        # Preserve original URLs if they exist
        if not image_data.get('original_url') and image_data.get('url'):
            image_data['original_url'] = image_data['url']
    
    # Preserve generation URLs
    if image_data.get('original_generation_url') and not image_data.get('generation_source'):
        image_data['generation_source'] = 'ai_generated'
    
    if not image_data.get('url'):
        fallback_url = (
            image_data.get('original_generation_url') or 
            image_data.get('original_url') or
            image_data.get('webContentLink') or
            image_data.get('thumbnailLink')
        )
        if fallback_url:
            image_data['url'] = fallback_url
    
    if not image_data.get('name'):
        name_fallback = (
            image_data.get('title') or
            (f"Image_{image_data.get('id', '')[:8]}" if image_data.get('id') else None) or
            f"Image_{random.randint(1000, 9999)}"
        )
        image_data['name'] = name_fallback

    return image_data


def get_best_streamlit_url(image_data):
    """
    Get the best URL for displaying in Streamlit based on testing.
    Priority: CDN direct > high-res thumbnail > public URL > thumbnail
    """
    if not image_data:
        return None
    
    # Try in order of known Streamlit compatibility
    url_priority = [
        image_data.get('drive_direct_link'),
        image_data.get('high_res_thumbnail'),
        image_data.get('drive_public_url'),
        image_data.get('drive_thumbnail_url'),
        image_data.get('url'),
        image_data.get('original_generation_url'),
        image_data.get('webContentLink'), # From Drive API listing
        image_data.get('thumbnailLink') # Also from Drive API listing
    ]
    
    for url in url_priority:
        if url:
            return url
    
    return None


def extract_folder_id(url: str):
    """Extract folder ID from various Google Drive URL formats"""
    patterns = [
        r'/folders/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'^([a-zA-Z0-9_-]+)$' # For cases where only the ID is provided
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError("Invalid Google Drive folder link.")

def extract_file_id(url: str):
    """Extract file ID from Google Drive URL"""
    patterns = [
        r'/d/([a-zA-Z0-9_-]+)', # Common shared link format
        r'id=([a-zA-Z0-9_-]+)', # Query parameter format
        r'^([a-zA-Z0-9_-]+)$'  # Case where only ID is provided
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# ============================================================================
# Drive Functions - Public Folder Access (No Auth Required)
# ============================================================================

def get_folder_name_from_id(folder_id: str) -> str:
    """Get a friendly folder name from the stored folders dictionary."""
    saved_folders = st.session_state.get('saved_folders', {})
    
    # Ensure saved_folders is a list of dictionaries for consistent access
    if isinstance(saved_folders, dict):
        saved_folders = [{"name": k, "url": v} for k, v in saved_folders.items()]

    if isinstance(saved_folders, list):
        for folder_config in saved_folders:
            if isinstance(folder_config, dict):
                url = folder_config.get('url', '')
                if folder_id in url:
                    return folder_config.get('name', "Unknown Folder")
    
    return "Unknown Folder"

def organize_images_by_folder(images):
    """Organize images by their source folder."""
    folders = {}
    for img in images:
        folder_id = img.get('folder_id', 'unknown')
        # Attempt to get a friendly name; fall back to folder_id if not found
        folder_name = img.get('folder_name', get_folder_name_from_id(folder_id))
        
        if folder_name not in folders:
            folders[folder_name] = []
        folders[folder_name].append(img)
    
    return folders

def display_url_options_card(image_data):
    """Display a comprehensive card showing all available URLs for an image with live testing."""
    st.markdown("""
        <div style='background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;padding:16px;margin:12px 0;'>
            <div style='font-weight:600;font-size:14px;margin-bottom:12px;color:#212529;'>
                📎 Available Image URLs (Tested for Streamlit)
            </div>
    """, unsafe_allow_html=True)
    
    url_types = []
    
    if image_data.get('drive_direct_link'):
        url_types.append({
            'label': 'CDN Direct Link (BEST FOR STREAMLIT)',
            'url': image_data['drive_direct_link'],
            'color': '#34A853',
            'icon': '🚀',
            'desc': 'lh3.googleusercontent.com - Most reliable for Streamlit display',
            'priority': 1
        })
    
    if image_data.get('high_res_thumbnail'):
        url_types.append({
            'label': 'High-Res Thumbnail',
            'url': image_data['high_res_thumbnail'],
            'color': '#FBBC04',
            'icon': '🖼️',
            'desc': 'Drive thumbnail at 2000px - Good quality backup',
            'priority': 2
        })
    
    if image_data.get('drive_public_url'):
        url_types.append({
            'label': 'Drive Public View URL',
            'url': image_data['drive_public_url'],
            'color': '#4285F4',
            'icon': '☁️',
            'desc': 'drive.google.com/uc - Standard public view link',
            'priority': 3
        })
    
    if image_data.get('drive_thumbnail_url'):
        url_types.append({
            'label': 'Standard Thumbnail',
            'url': image_data['drive_thumbnail_url'],
            'color': '#FBBC04',
            'icon': '📸',
            'desc': 'Drive thumbnail at 1200px - Smaller preview',
            'priority': 4
        })
    
    if image_data.get('original_generation_url') and image_data['original_generation_url'] not in [u['url'] for u in url_types]:
        url_types.append({
            'label': 'Original Generation URL',
            'url': image_data['original_generation_url'],
            'color': '#FF6B6B',
            'icon': '⭐',
            'desc': 'Original URL from AI generation',
            'priority': 5
        })
    
    if image_data.get('url') and image_data.get('url') not in [u['url'] for u in url_types]:
        url_types.append({
            'label': 'Standard URL',
            'url': image_data['url'],
            'color': '#6c757d',
            'icon': '🔗',
            'desc': 'Default image URL',
            'priority': 6
        })
    
    if image_data.get('webViewLink'):
        url_types.append({
            'label': 'Drive Web View Link',
            'url': image_data['webViewLink'],
            'color': '#17a2b8',
            'icon': '🌐',
            'desc': 'Open in Google Drive web interface',
            'priority': 7
        })
        
    if image_data.get('webContentLink'): # From Drive API listing
        url_types.append({
            'label': 'Drive Web Content Link',
            'url': image_data['webContentLink'],
            'color': '#6c757d',
            'icon': '🔗',
            'desc': 'Direct link to content from Drive API',
            'priority': 8
        })
    
    # Sort by priority
    url_types.sort(key=lambda x: x.get('priority', 999))
    
    for url_info in url_types:
        priority_badge = ""
        if url_info.get('priority') == 1:
            priority_badge = "<span style='background:#28a745;color:white;padding:2px 6px;border-radius:3px;font-size:9px;margin-left:8px;'>RECOMMENDED</span>"
        
        st.markdown(f"""
            <div style='background:white;border-left:4px solid {url_info['color']};padding:10px;margin:8px 0;border-radius:4px;'>
                <div style='display:flex;align-items:center;margin-bottom:6px;'>
                    <span style='font-size:18px;margin-right:8px;'>{url_info['icon']}</span>
                    <span style='font-weight:600;font-size:13px;color:#212529;'>{url_info['label']}</span>
                    {priority_badge}
                </div>
                <div style='font-size:11px;color:#6c757d;margin-bottom:6px;'>{url_info['desc']}</div>
                <div style='background:#f8f9fa;padding:8px;border-radius:4px;font-family:monospace;font-size:10px;color:#495057;word-break:break-all;'>
                    {url_info['url'][:120]}{'...' if len(url_info['url']) > 120 else ''}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        copy_col, test_col = st.columns([1, 1])
        with copy_col:
            if st.button(f"📋 Copy URL", key=f"copy_{url_info['label']}_{image_data.get('id', 'unknown')}_{random.randint(1000,9999)}", use_container_width=True):
                st.code(url_info['url'], language="text")
                st.success("✓ URL copied!")
        with test_col:
            if st.button(f"🧪 Test Display", key=f"test_{url_info['label']}_{image_data.get('id', 'unknown')}_{random.randint(1000,9999)}", use_container_width=True):
                with st.spinner(f"Testing {url_info['label']}..."):
                    try:
                        st.image(url_info['url'], caption=f"✓ {url_info['label']} displays correctly", use_container_width=True)
                        st.success(f"✅ SUCCESS: {url_info['label']} displays correctly!")
                    except Exception as e:
                        st.error(f"❌ FAILED: {str(e)[:80]}")
                        print(f"[v0] Test failed for {url_info['label']}: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

def load_images_from_folder(folder_url):
    """Load images from Google Drive folder URL with normalized URLs using multiple extraction methods."""
    try:
        folder_id = extract_folder_id(folder_url)
        if not folder_id:
            st.error("Invalid folder URL format.")
            return []
        
        print(f"[v0] Loading images from folder: {folder_id}")
        
        api_url = f"https://drive.google.com/drive/folders/{folder_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        print(f"[v0] Drive HTML response status: {response.status_code}")
        
        if response.status_code != 200:
            st.error(f"Failed to access folder. Status: {response.status_code}. Ensure folder is publicly shared.")
            return []
            
        html_content = response.text
        
        # Multiple regex patterns to extract file IDs
        # Pattern 1: Standard 33-character file IDs
        pattern_33 = r'"([a-zA-Z0-9_-]{33})"'
        # Pattern 2: 28-character file IDs (also valid)
        pattern_28 = r'"([a-zA-Z0-9_-]{28})"'
        # Pattern 3: Look for IDs in specific Drive contexts
        pattern_context = r'data-id="([a-zA-Z0-9_-]{28,33})"'
        
        ids_33 = re.findall(pattern_33, html_content)
        ids_28 = re.findall(pattern_28, html_content)
        ids_context = re.findall(pattern_context, html_content)
        
        # Combine all found IDs, prioritizing 33-char, then context, then 28-char
        all_ids = ids_33 + ids_context + ids_28
        potential_ids = list(dict.fromkeys(all_ids))  # Remove duplicates while preserving order
        
        print(f"[v0] Found {len(potential_ids)} potential file IDs (33-char: {len(ids_33)}, 28-char: {len(ids_28)}, context: {len(ids_context)})")
        
        if not potential_ids:
            st.warning("No file IDs found in folder HTML. The folder may be empty or not publicly accessible.")
            st.info("💡 Tip: Make sure the folder is shared with 'Anyone with the link can view' permissions.")
            return []
        
        images = []
        seen_ids = set()
        
        # Try to validate IDs by attempting to access them
        valid_count = 0
        for file_id in potential_ids:
            if file_id == folder_id or file_id in seen_ids:
                continue
            seen_ids.add(file_id)
            
            # Generate all URL variants
            direct_cdn_url = f"https://lh3.googleusercontent.com/d/{file_id}"
            public_view_url = f"https://drive.google.com/uc?export=view&id={file_id}"
            thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1200"
            high_res_thumbnail = f"https://drive.google.com/thumbnail?id={file_id}&sz=w2000"
            web_view_link = f"https://drive.google.com/file/d/{file_id}/view"
            
            image_data = {
                "name": f"Image_{file_id[:8]}", 
                "url": direct_cdn_url,
                "source": "gdrive_public",
                "file_id": file_id,
                "folder_id": folder_id,
                "folder_name": get_folder_name_from_id(folder_id),
                "drive_direct_link": direct_cdn_url,
                "drive_public_url": public_view_url,
                "drive_thumbnail_url": thumbnail_url,
                "high_res_thumbnail": high_res_thumbnail,
                "webViewLink": web_view_link,
                "id": file_id,
                "original_url": direct_cdn_url,
                "original_generation_url": direct_cdn_url
            }
            images.append(normalize_image_urls(image_data))
            valid_count += 1
        
        print(f"[v0] Extracted {len(images)} images from folder")
        
        if images:
            st.success(f"✓ Loaded {len(images)} images from '{get_folder_name_from_id(folder_id)}'")
            with st.expander("📋 View Sample URLs (First 3)", expanded=False):
                for idx, img in enumerate(images[:3]):
                    st.markdown(f"**Image {idx+1}: {img.get('name', 'Unknown')}**")
                    st.json({
                        "CDN Direct (Best for Streamlit)": img.get('drive_direct_link', 'N/A'),
                        "Public View": img.get('drive_public_url', 'N/A'),
                        "High-Res Thumbnail": img.get('high_res_thumbnail', 'N/A'),
                        "Standard Thumbnail": img.get('drive_thumbnail_url', 'N/A')
                    })
                    st.markdown("---")
        else:
            st.warning("⚠️ No valid image IDs found in this folder.")
            st.info("Troubleshooting:\n- Ensure the folder contains image files\n- Verify folder is shared publicly ('Anyone with the link can view')\n- Try a different folder")
        
        return images
        
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. The folder may be too large. Try a smaller folder or check your connection.")
        print("[v0] Timeout loading folder")
        return []
    except ValueError as ve:
        st.error(f"❌ Invalid folder URL: {ve}")
        print(f"[v0] Invalid folder URL: {ve}")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        print(f"[v0] Error loading folder: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

def get_gdrive_image_urls(folder_id: str, folder_name: str = None):
    """
    Extract individual image URLs from a public Google Drive folder using scraping.
    Prioritizes direct CDN links for maximum Streamlit compatibility.
    """
    print(f"[v0] Fetching images from public folder ID: {folder_id}")
    images = []
    
    # Determine folder name
    if not folder_name:
        folder_name = get_folder_name_from_id(folder_id)
    
    try:
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(folder_url, headers=headers, timeout=20) # Increased timeout
        print(f"[v0] Drive API response status: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Method 1: Extract all 33-character file IDs
            all_file_ids = re.findall(r'"([a-zA-Z0-9_-]{33})"', html_content)
            print(f"[v0] Found {len(all_file_ids)} potential file IDs (33 chars)")
            
            seen = set()
            for file_id in all_file_ids:
                if file_id != folder_id and file_id not in seen:
                    seen.add(file_id)
                    
                    direct_cdn_url = f"https://lh3.googleusercontent.com/d/{file_id}"
                    public_view_url = f"https://drive.google.com/uc?export=view&id={file_id}"
                    thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1200"
                    high_res_thumbnail = f"https://drive.google.com/thumbnail?id={file_id}&sz=w2000"
                    web_view_link = f"https://drive.google.com/file/d/{file_id}/view"
                    
                    image_data = {
                        "name": f"Image {len(images)+1}",
                        "url": direct_cdn_url,  # Primary URL is now CDN link
                        "source": "gdrive_public",
                        "file_id": file_id,
                        "folder_id": folder_id,
                        "folder_name": folder_name,
                        
                        # Multiple URL formats ordered by Streamlit compatibility
                        "drive_direct_link": direct_cdn_url,  # Best for Streamlit
                        "drive_public_url": public_view_url,  # Fallback 1
                        "drive_thumbnail_url": thumbnail_url,  # Fallback 2
                        "high_res_thumbnail": high_res_thumbnail,  # Fallback 3
                        "webViewLink": web_view_link,
                        "id": file_id,
                        "original_url": direct_cdn_url,
                        "original_generation_url": direct_cdn_url
                    }
                    images.append(normalize_image_urls(image_data))
            
            # Method 2: 28-character file IDs (less common for images, but include)
            if len(images) < 50: # Avoid excessive searching if we already have many
                alt_file_ids = re.findall(r'"([a-zA-Z0-9_-]{28})"', html_content)
                print(f"[v0] Found {len(alt_file_ids)} additional file IDs (28 chars)")
                for file_id in alt_file_ids:
                    if file_id != folder_id and file_id not in seen and len(file_id) == 28:
                        seen.add(file_id)
                        
                        direct_cdn_url = f"https://lh3.googleusercontent.com/d/{file_id}"
                        public_view_url = f"https://drive.google.com/uc?export=view&id={file_id}"
                        thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1200"
                        high_res_thumbnail = f"https://drive.google.com/thumbnail?id={file_id}&sz=w2000"
                        web_view_link = f"https://drive.google.com/file/d/{file_id}/view"
                        
                        image_data = {
                            "name": f"Image {len(images)+1}",
                            "url": direct_cdn_url,
                            "source": "gdrive_public",
                            "file_id": file_id,
                            "folder_id": folder_id,
                            "folder_name": folder_name,
                            "drive_direct_link": direct_cdn_url,
                            "drive_public_url": public_view_url,
                            "drive_thumbnail_url": thumbnail_url,
                            "high_res_thumbnail": high_res_thumbnail,
                            "webViewLink": web_view_link,
                            "id": file_id,
                            "original_url": direct_cdn_url,
                            "original_generation_url": direct_cdn_url
                        }
                        images.append(normalize_image_urls(image_data))
            
            # Method 3: JSON structures (less common for direct image links in folder view, but for completeness)
            # This might be more relevant for file listings from the Drive API itself.
            # For direct folder scraping, ID patterns are more reliable.
            # if len(images) < 50:
            #     json_pattern = r'\["([a-zA-Z0-9_-]{25,})"'
            #     json_ids = re.findall(json_pattern, html_content)
            #     print(f"[v0] Found {len(json_ids)} file IDs from JSON (25+ chars)")
            #     for file_id in json_ids:
            #         if file_id != folder_id and file_id not in seen and len(file_id) >= 25:
            #             seen.add(file_id)
                        
            #             direct_cdn_url = f"https://lh3.googleusercontent.com/d/{file_id}"
            #             public_view_url = f"https://drive.google.com/uc?export=view&id={file_id}"
            #             thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1200"
            #             high_res_thumbnail = f"https://drive.google.com/thumbnail?id={file_id}&sz=w2000"
            #             web_view_link = f"https://drive.google.com/file/d/{file_id}/view"
                        
            #             image_data = {
            #                 "name": f"Image {len(images)+1}",
            #                 "url": direct_cdn_url,
            #                 "source": "gdrive_public",
            #                 "file_id": file_id,
            #                 "folder_id": folder_id,
            #                 "folder_name": folder_name,
            #                 "drive_direct_link": direct_cdn_url,
            #                 "drive_public_url": public_view_url,
            #                 "drive_thumbnail_url": thumbnail_url,
            #                 "high_res_thumbnail": high_res_thumbnail,
            #                 "webViewLink": web_view_link,
            #                 "id": file_id,
            #                 "original_url": direct_cdn_url,
            #                 "original_generation_url": direct_cdn_url
            #             }
            #             images.append(normalize_image_urls(image_data))
        
        print(f"[v0] Total images found: {len(images)}")
        if images:
            with st.expander("📋 View Sample Image URLs (First 3)", expanded=False):
                for idx, img in enumerate(images[:3]):
                    st.markdown(f"**Image {idx+1}:**")
                    st.json({
                        "CDN Direct (Best)": img.get('drive_direct_link', 'N/A'),
                        "Public View": img.get('drive_public_url', 'N/A'),
                        "Thumbnail": img.get('drive_thumbnail_url', 'N/A'),
                        "High-Res Thumbnail": img.get('high_res_thumbnail', 'N/A')
                    })
                    st.markdown("---")
        else:
            st.warning("No images found in folder. Check folder sharing settings ('Anyone with the link can view').")
        
        return images
    
    except requests.exceptions.Timeout:
        st.error("Request timed out. The folder may be too large or network is slow.")
        print("[v0] Request timeout error")
        return []
    except Exception as e:
        st.error(f"Error fetching images: {str(e)}")
        print(f"[v0] Error in get_gdrive_image_urls: {str(e)}")
        return []


def display_image_with_fallback(image_data, caption="", use_container_width=True, width=None, show_source=True):
    """
    Display image with intelligent fallback through multiple URL options.
    Uses normalized URLs for maximum Streamlit compatibility.
    """
    if not image_data:
        st.warning("No image data provided")
        return False
    
    # Ensure image data is normalized
    # Check cache first, otherwise normalize and cache
    img_id = get_image_id(image_data)
    normalized_image_data = get_or_cache_normalized_image(image_data)

    if not normalized_image_data: # Check if normalization returned None
        st.error("Invalid image data after normalization.")
        return False

    urls_to_try = []
    
    # Priority 1: Direct CDN link (lh3.googleusercontent.com) - Best for Streamlit
    if normalized_image_data.get('drive_direct_link'):
        urls_to_try.append(('CDN Direct', normalized_image_data['drive_direct_link'], '#34A853'))
    
    # Priority 2: High-res thumbnail - Good quality fallback
    if normalized_image_data.get('high_res_thumbnail'):
        urls_to_try.append(('High-Res Thumb', normalized_image_data['high_res_thumbnail'], '#FBBC04'))
    
    # Priority 3: Original generation URL if available
    if normalized_image_data.get('original_generation_url') and 'lh3.googleusercontent' not in str(normalized_image_data.get('original_generation_url', '')):
        url_val = normalized_image_data.get('original_generation_url')
        if url_val:
            urls_to_try.append(('Original Gen', url_val, '#FF6B6B'))
    
    # Priority 4: Drive public URL
    if normalized_image_data.get('drive_public_url'):
        urls_to_try.append(('Drive Public', normalized_image_data['drive_public_url'], '#4285F4'))
    
    # Priority 5: Standard thumbnail
    if normalized_image_data.get('drive_thumbnail_url'):
        urls_to_try.append(('Thumbnail', normalized_image_data['drive_thumbnail_url'], '#FBBC04'))
    
    # Priority 6: Any other URL field
    if normalized_image_data.get('url') and normalized_image_data.get('url') not in [u[1] for u in urls_to_try]:
        url_val = normalized_image_data.get('url')
        if url_val:
            urls_to_try.append(('Standard URL', url_val, '#6c757d'))

    if normalized_image_data.get('webContentLink') and normalized_image_data.get('webContentLink') not in [u[1] for u in urls_to_try]:
        url_val = normalized_image_data.get('webContentLink')
        if url_val:
            urls_to_try.append(('Drive Content', url_val, '#6c757d'))
    
    if not urls_to_try:
        st.error("No valid image URLs found")
        print(f"[v0] No URLs found in image_data keys: {list(normalized_image_data.keys())}")
        return False
    
    displayed = False
    used_source_info = None
    failed_attempts = []
    
    for source_label, url, badge_color in urls_to_try:
        try:
            print(f"[v0] Attempting {source_label}: {url[:100]}...")
            if width:
                st.image(url, caption=caption, width=width)
            else:
                st.image(url, caption=caption, use_container_width=use_container_width)
            
            displayed = True
            used_source_info = (source_label, badge_color)
            print(f"[v0] ✓ SUCCESS: Displayed from {source_label}")
            break
            
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"[v0] ✗ FAILED {source_label}: {error_msg}")
            failed_attempts.append(f"{source_label}: {error_msg}")
            continue
    
    if displayed and show_source and used_source_info:
        source_label, badge_color = used_source_info
        st.markdown(
            f"<div style='margin-top:-10px;margin-bottom:10px;'>"
            f"<span style='background:{badge_color};color:white;padding:4px 8px;border-radius:4px;font-size:11px;font-weight:600;'>"
            f"✓ Loaded from: {source_label}</span></div>",
            unsafe_allow_html=True
        )
        return True
    
    if not displayed:
        print(f"[v0] ✗ ALL URLS FAILED. Tried {len(urls_to_try)} sources:")
        for fail in failed_attempts:
            print(f"[v0]   - {fail}")
        
        st.markdown(
            f"<div style='padding:40px;background:#fff3cd;border:2px dashed #ffc107;border-radius:12px;text-align:center;color:#856404;'>"
            f"<div style='font-size:48px;margin-bottom:10px;'>⚠️</div>"
            f"<div style='font-size:16px;font-weight:600;margin-bottom:8px;'>Image Load Failed</div>"
            f"<div style='font-size:13px;margin-bottom:5px;'>'{normalized_image_data.get('name', 'Unknown')}'</div>"
            f"<div style='font-size:11px;color:#856404;margin-bottom:10px;'>Tried {len(urls_to_try)} URL format(s)</div>"
            f"<details style='margin-top:12px;text-align:left;background:white;padding:10px;border-radius:6px;'>"
            f"<summary style='cursor:pointer;font-weight:600;font-size:12px;'>🔍 Debug Info</summary>"
            f"<div style='font-family:monospace;font-size:10px;margin-top:8px;'>"
            f"{'<br>'.join([f'• {fa}' for fa in failed_attempts])}"
            f"</div></details>"
            f"</div>",
            unsafe_allow_html=True
        )
        return False
    
    return displayed

def display_image_grid(images, columns=3, show_metadata=True, show_actions=True):
    """Display a grid of images with metadata and action buttons."""
    if not images:
        st.info("No images to display in this view.")
        return
    
    for i, image_data in enumerate(images):
        if i % columns == 0:
            cols = st.columns(columns)
        
        with cols[i % columns]:
            with st.container():
                st.markdown("<div class='image-card' style='border:1px solid #e0e0e0;border-radius:12px;padding:12px;margin-bottom:16px;'>", unsafe_allow_html=True)
                
                file_name = image_data.get('name', f'Image {i+1}')
                # Display image with fallback and source info
                display_image_with_fallback(image_data, caption=file_name, show_source=True)
                
                if show_metadata:
                    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                    
                    metadata_badges = []
                    
                    if image_data.get('original_generation_url') or image_data.get('original_url'):
                        metadata_badges.append("<span style='background:#FF6B6B;color:white;padding:3px 6px;border-radius:4px;font-size:10px;margin-right:4px;'>Original</span>")
                    
                    if image_data.get('drive_public_url') or image_data.get('public_image_url') or image_data.get('source') == 'gdrive_public':
                        metadata_badges.append("<span style='background:#4285F4;color:white;padding:3px 6px;border-radius:4px;font-size:10px;margin-right:4px;'>Drive</span>")
                    
                    if image_data.get('source') == 'gdrive_upload' or image_data.get('source') == 'gdrive_storage':
                         metadata_badges.append("<span style='background:#17a2b8;color:white;padding:3px 6px;border-radius:4px;font-size:10px;margin-right:4px;'>Uploaded</span>")
                    
                    if image_data.get('createdTime'):
                        try:
                            created_dt_str = image_data['createdTime']
                            if created_dt_str.endswith('Z'):
                                created_dt_str = created_dt_str[:-1] + '+00:00'
                            created_date = datetime.fromisoformat(created_dt_str)
                            date_str = created_date.strftime('%m/%d %H:%M')
                            metadata_badges.append("<span style='background:#6c757d;color:white;padding:3px 6px;border-radius:4px;font-size:10px;margin-right:4px;'>{}</span>".format(date_str))
                        except ValueError:
                            pass
                    
                    if image_data.get('size'):
                        try:
                            size_bytes = int(image_data['size'])
                            if size_bytes >= 1024 * 1024:
                                size_str = f"{size_bytes / (1024*1024):.1f}MB"
                            elif size_bytes >= 1024:
                                size_str = f"{size_bytes / 1024:.0f}KB"
                            else:
                                size_str = f"{size_bytes}B"
                            metadata_badges.append("<span style='background:#6c757d;color:white;padding:3px 6px;border-radius:4px;font-size:10px;margin-right:4px;'>{}</span>".format(size_str))
                        except (ValueError, TypeError):
                            pass

                    # Display folder name if available in metadata
                    if image_data.get('folder_name'):
                        metadata_badges.append(f"<span style='background:#17a2b8;color:white;padding:3px 6px;border-radius:4px;font-size:10px;margin-right:4px;'>📁 {image_data['folder_name']}</span>")
                    
                    if metadata_badges:
                        st.markdown("<div style='margin-bottom:8px;'>" + "".join(metadata_badges) + "</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                if show_actions:
                    file_id = image_data.get('id', f'img_{i}')
                    
                    st.markdown("---")
                    
                    edit_col1, edit_col2 = st.columns(2)
                    with edit_col1:
                        if st.button("Qwen Edit", key=f"qwen_edit_{file_id}_{i}", help="Edit this image with Qwen", use_container_width=True):
                            st.session_state.selected_image_for_edit = image_data
                            st.session_state.edit_mode = 'qwen'
                            st.session_state.current_page = "Generate"
                            st.rerun()
                    
                    with edit_col2:
                        if st.button("Seedream", key=f"seedream_edit_{file_id}_{i}", help="Edit this image with Seedream", use_container_width=True):
                            st.session_state.selected_image_for_edit = image_data
                            st.session_state.edit_mode = 'seedream'
                            st.session_state.current_page = "Generate"
                            st.rerun()
                    
                    with st.expander("View All URLs"):
                        display_url_options_card(image_data)
                
                st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# Sidebar Configuration
# ============================================================================
def handle_api_key_change():
    """Callback to handle API key change."""
    st.session_state.api_key = st.session_state.api_key_input

def handle_service_account_upload():
    """Callback to handle service account JSON upload."""
    uploaded_file = st.session_state.service_account_uploader
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.getvalue().decode("utf-8")
            service_account_json = json.loads(file_content)
            
            success, message = authenticate_with_service_account(service_account_json)
            
            if success:
                st.session_state.service_account_info = file_content
                st.success(message)
                with st.spinner("Setting up Drive folder..."):
                    folder_id = create_app_folder()
                    if folder_id:
                        st.success(f"Created/Found Drive folder with ID: {folder_id}")
                    else:
                        st.warning("Could not create or find Google Drive folder.")
                st.rerun()
            else:
                st.error(message)
        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please ensure it's a valid service account key.")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

def save_folder_config(folder_name: str, folder_url: str):
    """Save a folder configuration."""
    # Ensure saved_folders is a list of dictionaries for easier management
    if not isinstance(st.session_state.saved_folders, list):
        st.session_state.saved_folders = [{"name": k, "url": v} for k, v in st.session_state.saved_folders.items()]
    
    # Check if folder name already exists
    if any(f['name'] == folder_name for f in st.session_state.saved_folders):
        st.warning(f"Folder '{folder_name}' already exists. Please use a different name or rename it.")
        return
    
    st.session_state.saved_folders.append({"name": folder_name, "url": folder_url})
    st.success(f"Saved folder: {folder_name}")

def delete_folder_config(folder_name: str):
    """Delete a folder configuration."""
    st.session_state.saved_folders = [f for f in st.session_state.saved_folders if f['name'] != folder_name]
    st.success(f"Deleted folder: {folder_name}")

def rename_folder_config(old_name: str, new_name: str):
    """Rename a folder configuration."""
    for folder in st.session_state.saved_folders:
        if folder['name'] == old_name:
            folder['name'] = new_name
            st.success(f"Renamed folder: {old_name} → {new_name}")
            return
    st.warning(f"Folder '{old_name}' not found for renaming.")


def render_folder_manager():
    """Render the folder management interface."""
    st.markdown("### Folder Management")
    
    # Add new folder section
    with st.expander("Add New Folder", expanded=False):
        col1, col2 = st.columns([2, 1])
        with col1:
            new_folder_name = st.text_input(
                "Folder Name",
                key="new_folder_name",
                placeholder="My Custom Folder"
            )
            new_folder_url = st.text_input(
                "Folder URL",
                key="new_folder_url",
                placeholder="https://drive.google.com/drive/folders/..."
            )
        with col2:
            st.markdown("<div style='height: 48px;'></div>", unsafe_allow_html=True)
            if st.button("Add Folder", type="primary", use_container_width=True):
                if new_folder_name and new_folder_url:
                    try:
                        # Validate URL
                        extract_folder_id(new_folder_url)
                        save_folder_config(new_folder_name, new_folder_url)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Invalid folder URL: {str(e)}")
                else:
                    st.warning("Please provide both folder name and URL")
    
    # Display existing folders
    st.markdown("### Saved Folders")
    
    # Ensure saved_folders is a list of dicts for consistent access
    if not isinstance(st.session_state.saved_folders, list):
        st.session_state.saved_folders = [{"name": k, "url": v} for k, v in st.session_state.saved_folders.items()]

    if not st.session_state.saved_folders:
        st.info("No saved folders. Add one above to get started!")
        return
    
    for idx, folder_config in enumerate(st.session_state.saved_folders):
        folder_name = folder_config['name']
        folder_url = folder_config['url']
        
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            
            with col1:
                # Show folder name with edit capability
                if st.session_state.editing_folder == folder_name:
                    new_name = st.text_input(
                        "New name",
                        value=folder_name,
                        key=f"rename_{idx}",
                        label_visibility="collapsed"
                    )
                else:
                    st.markdown(f"**{folder_name}**")
            
            with col2:
                # Show truncated URL
                truncated_url = folder_url[:40] + "..." if len(folder_url) > 40 else folder_url
                st.caption(truncated_url)
            
            with col3:
                # Load button
                if st.button("Load", key=f"load_{idx}", use_container_width=True):
                    with st.spinner("Loading images..."):
                        try:
                            folder_id = extract_folder_id(folder_url)
                            if folder_id:
                                gdrive_imgs = get_gdrive_image_urls(folder_id, folder_name) # Pass folder_name
                                st.session_state.images = gdrive_imgs
                                st.session_state.current_index = 0
                                st.session_state.default_folder_url = folder_url # Update default URL
                                st.session_state.show_folder_manager = False
                                st.session_state.last_loaded_folder = folder_url # Track last loaded folder
                                if gdrive_imgs:
                                    st.balloons()
                                    st.success(f"Loaded {len(gdrive_imgs)} images!")
                                    st.rerun()
                                else:
                                    st.error("No images found.")
                            else:
                                st.error("Invalid folder URL")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            with col4:
                # Edit button
                if st.session_state.editing_folder == folder_name:
                    if st.button("Save", key=f"save_{idx}", use_container_width=True):
                        if new_name and new_name != folder_name:
                            rename_folder_config(folder_name, new_name)
                            st.session_state.editing_folder = None
                            st.rerun()
                else:
                    if st.button("Edit", key=f"edit_{idx}", use_container_width=True):
                        st.session_state.editing_folder = folder_name
                        st.rerun()
            
            with col5:
                # Delete button
                if st.button("Delete", key=f"delete_{idx}", use_container_width=True):
                    delete_folder_config(folder_name)
                    st.rerun()
            
            st.divider()

# ============================================================================
# Main App Layout - Sidebar and Page Routing
# ============================================================================
with st.sidebar:
    st.markdown("# 🎬 Drive Slideshow & AI")
    st.markdown("---")
    
    # Page Navigation
    st.header("Navigation")
    page = st.radio(
        "Select Page",
        ["Slideshow", "Generate", "History", "Library"],
        index=["Slideshow", "Generate", "History", "Library"].index(st.session_state.current_page),
        key="page_nav"
    )
    if page != st.session_state.current_page:
        st.session_state.current_page = page
        st.rerun()
    
    st.markdown("---")
    
    # API Key Input (moved to sidebar for better organization)
    st.header("API Configuration")
    api_key_input = st.text_input(
        "API Key",
        type="password",
        value=st.session_state.api_key,
        key="api_key_input",
        on_change=handle_api_key_change,
        help="Enter your KIE.AI API key"
    )
    
    if st.session_state.api_key:
        st.success("API Key configured")
    else:
        st.warning("Please enter API key")
    
    st.markdown("---")
    
    # Google Drive Setup
    st.header("Google Drive Setup")
    
    if not st.session_state.gdrive_authenticated:
        st.info("Upload service account JSON file")
        
        uploaded_file = st.file_uploader(
            "Service Account JSON",
            type=['json'],
            key="service_account_uploader",
            on_change=handle_service_account_upload,
            help="Upload your Google service account credentials JSON file"
        )
    else:
        st.success(f"Google Drive Connected")
        
        col1, col2 = st.columns(2)
        with col1:
            auto_upload = st.checkbox(
                "Auto Upload",
                value=st.session_state.auto_upload,
                help="Automatically upload generated images to Google Drive"
            )
            st.session_state.auto_upload = auto_upload
        
        with col2:
            if st.button("Refresh Library", use_container_width=True):
                with st.spinner("Refreshing library..."):
                    # Reset library loaded flag to force reload
                    st.session_state.library_loaded = False
                    # Clear existing library images to ensure a clean load
                    st.session_state.all_library_images = [] 
                    st.rerun()
                st.success("Library refresh initiated!")
        
        if st.button("Disconnect", use_container_width=True):
            st.session_state.gdrive_authenticated = False
            st.session_state.service = None
            st.session_state.credentials = None
            st.session_state.service_account_info = None
            st.session_state.gdrive_folder_id = None
            st.session_state.library_images = [] # Clear library on disconnect
            st.session_state.library_loaded = False # Reset load flag
            st.rerun()
    
    st.markdown("---")
    
    # Folder Management button
    st.header("Manage Folders")
    if st.button("Open Folder Manager", use_container_width=True):
        st.session_state.show_folder_manager = not st.session_state.show_folder_manager
        st.rerun()
        
    if st.session_state.show_folder_manager:
        render_folder_manager()
        st.markdown("---")

    # Statistics
    st.header("Statistics")
    
    stats = st.session_state.stats
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Tasks", stats['total_tasks'])
        st.metric("Successful", stats['successful_tasks'])
    with col2:
        st.metric("Failed", stats['failed_tasks'])
        st.metric("Uploaded", stats['uploaded_images'])
    
    success_rate = (stats['successful_tasks'] / stats['total_tasks'] * 100) if stats['total_tasks'] > 0 else 0
    st.metric("Success Rate", f"{success_rate:.1f}%")

# ============================================================================
# API Functions - Task Creation and Management
# ============================================================================

def create_task(api_key, model, input_params, callback_url=None):
    """Create a generation task with retry logic and fallback endpoints."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "input": input_params
    }
    
    if callback_url:
        payload["callBackUrl"] = callback_url
    
    # Try primary endpoint with retries
    for attempt in range(MAX_RETRIES):
        try:
            print(f"[v0] Attempt {attempt + 1}/{MAX_RETRIES}: Creating task with {API_BASE_URL}")
            response = requests.post(
                f"{API_BASE_URL}/createTask",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Check for successful status code and API-level success
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("code") == 200:
                        st.session_state.stats['total_tasks'] += 1
                        print(f"[v0] ✓ Task created successfully: {data['data']['taskId']}")
                        return {"success": True, "task_id": data["data"]["taskId"]}
                    else:
                        error_msg = data.get('msg', 'Unknown API error')
                        print(f"[v0] ✗ API returned error: {error_msg}")
                        return {"success": False, "error": error_msg}
                except json.JSONDecodeError:
                    return {"success": False, "error": "Invalid JSON response from API"}
            else:
                print(f"[v0] ✗ HTTP error: {response.status_code}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                    print(f"[v0] Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                # If it's the last attempt, try fallback or return error
                pass # Will try fallback below or return error if fallback fails
                
        except requests.exceptions.RequestException as e:
            print(f"[v0] ✗ Network error: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                print(f"[v0] Retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            # If it's the last attempt, try fallback or return error
            pass # Will try fallback below or return error if fallback fails
            
    # If primary endpoint attempts failed, try fallback endpoint
    print(f"[v0] Primary endpoint failed after {MAX_RETRIES} attempts. Trying fallback endpoint: {API_FALLBACK_URL}")
    try:
        response = requests.post(
            f"{API_FALLBACK_URL}/createTask",
            headers=headers,
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                st.session_state.stats['total_tasks'] += 1
                print(f"[v0] ✓ Task created successfully via fallback: {data['data']['taskId']}")
                return {"success": True, "task_id": data["data"]["taskId"]}
            else:
                error_msg = data.get('msg', 'Unknown API error')
                print(f"[v0] ✗ Fallback API returned error: {error_msg}")
                return {"success": False, "error": error_msg}
        else:
            print(f"[v0] ✗ Fallback HTTP error: {response.status_code}")
            return {"success": False, "error": f"Fallback HTTP {response.status_code}: {response.text}"}
            
    except requests.exceptions.RequestException as e:
        print(f"[v0] ✗ Fallback network error: {str(e)}")
        return {"success": False, "error": f"Fallback Network error: {str(e)}"}
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON response from fallback API"}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred during fallback: {str(e)}"}
    
    # If all attempts failed
    return {"success": False, "error": "Max retries exceeded for both primary and fallback endpoints."}


def check_task_status(api_key, task_id):
    """Check task status with the API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/recordInfo",
            headers=headers,
            params={"taskId": task_id},
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("code") == 200:
                    return {"success": True, "data": data["data"]}
                else:
                    return {"success": False, "error": data.get('msg', 'Unknown API error')}
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid JSON response from API"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}


def poll_task_until_complete(api_key, task_id, max_attempts=60, delay=2):
    """Poll task status until completion or timeout."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for attempt in range(max_attempts):
        result = check_task_status(api_key, task_id)
        
        if result["success"]:
            task_data = result["data"]
            state = task_data.get("state", "unknown").lower() # Use get with default and lower for safety
            
            # Calculate progress based on attempt number, capped at 95% until success
            progress_val = min((attempt + 1) / max_attempts, 0.95)
            progress_bar.progress(progress_val)
            status_text.text(f"Status: {state.upper()} | Attempt {attempt + 1}/{max_attempts}")
            
            if state == "success":
                progress_bar.progress(1.0)
                status_text.text("✅ Task completed successfully!")
                return {"success": True, "data": task_data}
            elif state == "fail":
                progress_bar.empty()
                status_text.text("❌ Task failed")
                return {"success": False, "error": task_data.get('failMsg', 'Unknown failure reason'), "data": task_data}
            
            time.sleep(delay)
        else:
            # Display error message if status check fails
            error_message = result.get('error', 'Unknown error during status check')
            status_text.text(f"⚠️ Error checking status: {error_message}")
            print(f"[v0] Polling error: {error_message}")
            time.sleep(delay)
    
    # Timeout reached if loop completes without success or failure
    progress_bar.empty()
    status_text.text("⏱️ Polling timed out")
    return {"success": False, "error": "Timeout reached while waiting for task completion"}


def save_and_upload_results(task_id, model, prompt, result_urls):
    """Save results to history and auto-upload to Google Drive if enabled."""
    updated = False
    for i, task in enumerate(st.session_state.task_history):
        if task['id'] == task_id:
            st.session_state.task_history[i]['status'] = 'success'
            
            normalized_results = []
            for url in result_urls:
                # If it's a direct image URL, wrap it in normalized format
                if isinstance(url, str):
                    normalized_results.append({
                        'url': url,
                        'original_generation_url': url,
                        'name': f"{model.replace('/', '_')}_{task_id}_result", # Basic name
                        'generation_source': 'ai_generated',
                        'source': 'ai_generated' # Add source for consistency
                    })
                else:
                    # Assume it's already a dict-like object and normalize it
                    normalized_results.append(normalize_image_urls(url))
            
            st.session_state.task_history[i]['results'] = normalized_results
            st.session_state.stats['successful_tasks'] += 1
            st.session_state.stats['total_images'] += len(result_urls)
            updated = True
            
            # Auto-upload to Google Drive if authenticated and enabled
            if st.session_state.gdrive_authenticated and st.session_state.auto_upload:
                for j, result_item in enumerate(normalized_results): # Iterate over normalized results
                    # Handle both string URLs and dict objects
                    actual_url = result_item.get('url', result_item.get('original_generation_url', ''))
                    
                    if not actual_url:
                        print(f"[v0] Skipping upload: No valid URL found for result item {j+1} in task {task_id}")
                        continue
                    
                    # Infer file extension if possible
                    file_extension = 'png'  # default
                    if '.jpg' in actual_url.lower() or '.jpeg' in actual_url.lower():
                        file_extension = 'jpg'
                    elif '.webp' in actual_url.lower():
                        file_extension = 'webp'
                    elif '.png' in actual_url.lower(): # Explicitly check for png
                        file_extension = 'png'
                    
                    # Get a better name if possible from the normalized data
                    file_name_base = result_item.get('name', f"{model.replace('/', '_')}_{task_id}_result_{j+1}")
                    file_name = f"{file_name_base}.{file_extension}"
                    
                    try:
                        with st.spinner(f"Uploading '{file_name}' to Drive..."):
                            drive_url = upload_to_drive(actual_url, file_name)
                            if drive_url:
                                print(f"[v0] Uploaded '{file_name}' to Google Drive: {drive_url}")
                                # Add Drive URL to task history
                                if 'drive_urls' not in st.session_state.task_history[i]:
                                    st.session_state.task_history[i]['drive_urls'] = []
                                # Store normalized drive data
                                st.session_state.task_history[i]['drive_urls'].append({
                                    'url': drive_url,
                                    'name': file_name,
                                    'source': 'gdrive_upload'
                                })
                                st.session_state.stats['uploaded_images'] += 1
                                # Add to library session state for immediate feedback
                                uploaded_image_data = normalize_image_urls({
                                    'url': drive_url,
                                    'name': file_name,
                                    'source': 'gdrive_upload',
                                    'folder_name': 'Drive Storage', # Generic for uploaded files
                                    'webViewLink': drive_url
                                })
                                # Add to the library list (not necessarily history sub-list)
                                st.session_state.library_images.insert(0, uploaded_image_data)
                                st.session_state.all_library_images.insert(0, uploaded_image_data) # Also add to the main library list
                                st.session_state.library_loaded = True # Ensure flag is set if library was empty
                            else:
                                print(f"[v0] upload_to_drive returned None for '{file_name}'.")
                    except Exception as e:
                        print(f"[v0] Upload failed for '{file_name}': {str(e)}")
                        continue # Continue to next image if one upload fails
            
            break
    
    return updated

# ============================================================================
# Google Drive Authentication and Upload Functions
# ============================================================================

def authenticate_with_service_account(service_account_json: dict):
    """Authenticate with Google Drive using service account credentials."""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            service_account_json, scopes=SCOPES
        )
        service = build("drive", "v3", credentials=credentials)
        
        st.session_state.credentials = credentials
        st.session_state.service = service
        st.session_state.gdrive_authenticated = True
        
        try:
            # Test basic Drive access first
            test_response = service.files().list(pageSize=1, fields="files(id, name)").execute()
            print(f"[v0] Basic Drive access successful: {len(test_response.get('files', []))} files found")
            
            # Now try to create/find the app folder
            app_folder_id = create_app_folder()
            if app_folder_id:
                print(f"[v0] App folder created/found: {app_folder_id}")
            else:
                print(f"[v0] Warning: Could not create app folder, but Drive access works")
                
        except Exception as test_e:
            error_msg = str(test_e)
            print(f"[v0] Drive access test warning: {error_msg}")
            
            if "insufficient" in error_msg.lower() or "permission" in error_msg.lower():
                # Permission error - auth worked but limited access
                st.warning("⚠️ Drive connected but with limited permissions. You can still use public folders.")
                return True, "Connected with limited permissions. Public folders will work."
            elif "quota" in error_msg.lower():
                st.warning("⚠️ Drive quota exceeded. Using public folders only.")
                return True, "Connected but quota exceeded. Using public folders."
            else:
                # Unknown error - still allow connection for public folder access
                st.warning(f"⚠️ Drive connected but folder creation failed: {error_msg}")
                return True, "Drive connected. Using public folders for now."

        return True, "Successfully authenticated with Google Drive!"
        
    except Exception as e:
        error_msg = str(e)
        print(f"[v0] Service account authentication failed: {error_msg}")
        
        st.session_state.gdrive_authenticated = False
        st.session_state.service = None
        st.session_state.credentials = None
        
        return False, f"Authentication failed: {error_msg}"

def create_app_folder():
    """Creates a folder for the app in Google Drive if it doesn't exist."""
    if not st.session_state.get('service'):
        print("[v0] No Drive service available for folder creation")
        return None
    
    folder_name = "AI_Slideshow_Generator_Content"
    
    try:
        # Check if folder already exists
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        response = st.session_state.service.files().list(
            q=query, 
            spaces="drive", 
            fields="files(id, name)",
            pageSize=10
        ).execute()
        
        if response.get("files"):
            folder_id = response["files"][0]["id"]
            print(f"[v0] App folder '{folder_name}' found with ID: {folder_id}")
        else:
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            
            try:
                folder = st.session_state.service.files().create(
                    body=file_metadata, 
                    fields="id"
                ).execute()
                folder_id = folder.get("id")
                print(f"[v0] Created app folder '{folder_name}' with ID: {folder_id}")
                
                try:
                    # Attempt to make it public for easier sharing of uploaded items
                    st.session_state.service.permissions().create(
                        fileId=folder_id,
                        body={'type': 'anyone', 'role': 'reader'},
                        fields='id'
                    ).execute()
                    print(f"[v0] Made folder '{folder_name}' public")
                except Exception as perm_e:
                    print(f"[v0] Could not make folder public (OK): {str(perm_e)}")
                    
            except Exception as create_e:
                error_msg = str(create_e)
                print(f"[v0] Could not create folder: {error_msg}")
                
                if "insufficient" in error_msg.lower() or "permission" in error_msg.lower():
                    print(f"[v0] Insufficient permissions to create folder - will use public folders only")
                    return None
                raise  # Re-raise other errors

        st.session_state.gdrive_folder_id = folder_id
        return folder_id
        
    except Exception as e:
        error_msg = str(e)
        print(f"[v0] Error with app folder: {error_msg}")
        
        st.session_state.gdrive_folder_id = None
        return None

def upload_to_drive(file_path_or_url, filename, parent_folder_id=None):
    """Upload a file to Google Drive from a URL or local path."""
    if not st.session_state.get('service'):
        st.error("❌ Not authenticated with Google Drive. Please connect in Settings.")
        return None
    
    if parent_folder_id is None:
        parent_folder_id = st.session_state.get('gdrive_folder_id')
    
    if not parent_folder_id:
        st.warning("⚠️ No Drive folder available. Ensure Drive is properly set up in Settings.")
        return None
    
    print(f"[v0] Uploading '{filename}' to Drive folder '{parent_folder_id}'...")
    
    try:
        # Download the file if it's a URL
        if file_path_or_url.startswith("http"):
            response = requests.get(file_path_or_url, stream=True, timeout=60)
            response.raise_for_status()
            file_content = io.BytesIO(response.content)
            mime_type = response.headers.get('content-type', 'image/png').split(';')[0]
        else:
            # If it's a local path (less likely in this app context)
            with open(file_path_or_url, "rb") as f:
                file_content = io.BytesIO(f.read())
            # Infer mime type from filename
            if filename.lower().endswith(".png"):
                mime_type = "image/png"
            elif filename.lower().endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            elif filename.lower().endswith(".webp"):
                mime_type = "image/webp"
            else:
                mime_type = "application/octet-stream"

        file_metadata = {
            "name": filename,
            "parents": [parent_folder_id]
        }
        
        media = MediaIoBaseUpload(file_content, mimetype=mime_type, resumable=True)
        
        file = st.session_state.service.files().create(
            body=file_metadata, media_body=media, fields="id, webViewLink, webContentLink"
        ).execute()
        
        print(f"[v0] Successfully uploaded '{filename}'. File ID: {file.get('id')}")
        
        # Optionally, make the uploaded file public for easier sharing
        try:
            st.session_state.service.permissions().create(
                fileId=file.get("id"),
                body={'type': 'anyone', 'role': 'reader'},
                fields='id'
            ).execute()
            print(f"[v0] Made uploaded file '{filename}' public.")
        except Exception as perm_e:
            print(f"[v0] Failed to make uploaded file public (OK): {str(perm_e)}")
            
        # Increment stats if upload is successful
        st.session_state.stats['uploaded_images'] += 1
        
        # Return the webViewLink for easy access and linking
        return file.get("webViewLink")
        
    except requests.exceptions.Timeout:
        st.error("Timeout downloading image for upload.")
        return None
    except Exception as e:
        error_msg = str(e)
        print(f"[v0] Error uploading file: {error_msg}")
        st.error(f"Error uploading '{filename}' to Google Drive: {error_msg}")
        return None

def list_gdrive_images(folder_id=None, fetch_all=False):
    """List images from a specific folder - tries authenticated access first, then public scraping."""
    
    # Try authenticated Drive access first if available
    if st.session_state.get('service'):
        print("[v0] Using authenticated Drive service to list images")
        
        if folder_id is None:
            folder_id = st.session_state.get('gdrive_folder_id')
        
        if not folder_id:
            print("[v0] No folder ID available")
            return []

        images = []
        try:
            query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed=false"
            
            page_token = None
            pages_fetched = 0
            max_pages = 10
            
            while True:
                if pages_fetched >= max_pages:
                    print(f"[v0] Reached max pages ({max_pages})")
                    break
                    
                response = st.session_state.service.files().list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, thumbnailLink, webContentLink)",
                    pageSize=100,
                    pageToken=page_token
                ).execute()
                
                for file in response.get("files", []):
                    image_data = {
                        "id": file["id"],
                        "file_id": file["id"],
                        "name": file.get("name", "Unknown Image"),
                        "mimeType": file.get("mimeType", ""),
                        "size": file.get("size", 0),
                        "createdTime": file.get("createdTime", ""),
                        "modifiedTime": file.get("modifiedTime", ""),
                        "webViewLink": file.get("webViewLink", ""),
                        "thumbnailLink": file.get("thumbnailLink", ""),
                        "webContentLink": file.get("webContentLink", ""),
                        "source": "gdrive_storage",
                        "folder_id": folder_id,
                        "folder_name": "Drive Storage",
                        "url": file.get("webContentLink", ""),
                        "original_url": file.get("webContentLink", ""),
                        "original_generation_url": file.get("webContentLink", ""),
                    }
                    images.append(normalize_image_urls(image_data))
                
                page_token = response.get("nextPageToken", None)
                pages_fetched += 1
                
                if page_token is None:
                    break
                    
            print(f"[v0] Listed {len(images)} images from authenticated Drive")
            return images
            
        except Exception as e:
            print(f"[v0] Error with authenticated access: {str(e)}")
            # Fall through to public scraping method
    
    # Fallback to public scraping method
    print("[v0] Attempting public folder scraping method")
    if folder_id:
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
        return load_images_from_folder(folder_url)
    
    return []

# ============================================================================
# Main Application Pages
# ============================================================================
def render_slideshow_page():
    """Main slideshow interface with enhanced selection persistence."""
    st.title("🎬 Google Drive Slideshow")
    
    render_selection_preview_banner()
    
    # Folder selection dropdown at top
    st.markdown("### 🗂️ Quick Load Folders")
    
    saved_folders_list = st.session_state.get('saved_folders', [])
    if isinstance(saved_folders_list, dict): # Convert dict to list if it's still in old format
        saved_folders_list = [{"name": k, "url": v} for k, v in saved_folders_list.items()]
        st.session_state.saved_folders = saved_folders_list

    if saved_folders_list:
        folder_options_map = {"": "Select a folder..."} # Default option
        for folder_config in saved_folders_list:
            folder_options_map[folder_config['name']] = folder_config['url']
        
        selected_folder_name = st.selectbox(
            "Choose a saved folder to load:",
            options=list(folder_options_map.keys()),
            format_func=lambda x: folder_options_map[x] if x else "Select a folder...",
            key="quick_folder_selector_slideshow" # Unique key
        )
        
        if selected_folder_name and selected_folder_name != "":
            folder_url = folder_options_map[selected_folder_name]
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"📁 {selected_folder_name}: {folder_url}")
            with col2:
                if st.button("📥 Load This Folder", use_container_width=True):
                    with st.spinner(f"Loading images from {selected_folder_name}..."):
                        try:
                            folder_id = extract_folder_id(folder_url)
                            if folder_id:
                                images = get_gdrive_image_urls(folder_id, selected_folder_name)
                                if images:
                                    st.session_state.images = images
                                    st.session_state.current_index = 0
                                    st.session_state.default_folder_url = folder_url # Update default URL
                                    st.success(f"✅ Loaded {len(images)} images from {selected_folder_name}")
                                    st.rerun()
                                else:
                                    st.error("No images found in this folder")
                            else:
                                st.error("Invalid folder URL")
                        except Exception as e:
                            st.error(f"Error loading folder: {str(e)}")

    st.markdown("---")

    # Manual URL input section
    with st.expander("🔗 Or Enter Custom Drive Folder URL", expanded=False):
        input_col1, input_col2 = st.columns([3, 1])
        with input_col1:
            folder_url = st.text_input(
                "Google Drive Folder URL",
                value=st.session_state.get('default_folder_url', DEFAULT_FOLDER_URL),
                help="Paste a public Google Drive folder URL"
            )
        with input_col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            load_btn = st.button("📥 Load Images", use_container_width=True)

        if load_btn:
            if folder_url:
                with st.spinner('Loading images from Google Drive...'):
                    try:
                        folder_id = extract_folder_id(folder_url)
                        if not folder_id:
                            st.error("❌ Invalid folder URL. Please check and try again.")
                        else:
                            images = get_gdrive_image_urls(folder_url) # Rely on default name extraction
                            if images:
                                st.session_state.images = images
                                st.session_state.current_index = 0
                                st.session_state.default_folder_url = folder_url
                                st.success(f'✅ Loaded {len(images)} images!')
                                st.rerun()
                            else:
                                st.warning("⚠️ No images found in this folder. Make sure it's public and contains images.")
                    except Exception as e:
                        st.error(f'❌ Error loading Google Drive: {str(e)}')
            else:
                st.warning("Please enter a folder URL")

    # Slideshow display section
    imgs = st.session_state.images
    
    if not imgs or len(imgs) == 0:
        st.info("No images loaded. Please enter a Google Drive folder URL above.")
        return
    
    # Ensure current_index is within valid range
    if st.session_state.current_index >= len(imgs):
        st.session_state.current_index = 0
    elif st.session_state.current_index < 0:
        st.session_state.current_index = 0
    
    idx = st.session_state.current_index
    total = len(imgs)
    
    # Validate that current_item is a valid dictionary with normalization
    if idx >= total:
        st.error(f"Invalid image index: {idx} >= {total}")
        st.session_state.current_index = 0
        st.rerun()
        return
    
    current_item = imgs[idx]
    
    if not current_item or not isinstance(current_item, dict):
        st.error(f"Invalid image data at index {idx}")
        # Try to fix by normalizing
        if isinstance(current_item, str):
            current_item = normalize_image_urls({'url': current_item, 'name': f'Image_{idx+1}'})
            imgs[idx] = current_item # Update in place
        else:
            st.warning("Skipping invalid image...")
            if idx + 1 < total:
                st.session_state.current_index = idx + 1
                st.rerun()
            return
    
    # Normalize current item to ensure all URL fields are present
    current_item = normalize_image_urls(current_item)
    imgs[idx] = current_item  # Update in place

    # Use unified selection count
    selected_count = get_total_selected_count()

    # Stats bar
    st.markdown("""
    <div class="stats-bar">
        <div class="stat-box">
            <h2>{idx}</h2>
            <p>Current</p>
        </div>
        <div class="stat-box">
            <h2>{total}</h2>
            <p>Total Images</p>
        </div>
        <div class="stat-box">
            <h2>{progress:.0f}%</h2>
            <p>Progress</p>
        </div>
        <div class="stat-box">
            <h2>{selected_count}</h2>
            <p>Selected</p>
        </div>
    </div>
    """.format(
        idx=idx + 1,  # Display 1-based indexing
        total=total, 
        progress=((idx + 1) / total * 100) if total > 0 else 0, 
        selected_count=selected_count
    ), unsafe_allow_html=True)

    # Autoplay logic
    if st.session_state.autoplay and total > 0:
        time.sleep(st.session_state.slideshow_speed)
        if st.session_state.loop_mode:
            st.session_state.current_index = (idx + 1) % total
        else:
            st.session_state.current_index = min(idx + 1, total - 1)
            if idx + 1 >= total: # If we reached the end and loop is off
                st.session_state.autoplay = False # Stop autoplay
        st.rerun()

    # Main image display
    st.markdown('<div class="slideshow-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="image-frame">', unsafe_allow_html=True)
    display_image_with_fallback(current_item, caption="", show_source=False)
    st.markdown('</div>', unsafe_allow_html=True)
    
    image_name = current_item.get("name") or current_item.get("title") or f"Image_{idx+1}"
    
    # Image caption with slide counter
    st.markdown("""
    <div class="image-caption">
        <span class="slide-counter">{idx} / {total}</span>
        <span>{name}</span>
    </div>
    """.format(idx=idx+1, total=total, name=image_name), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Selection controls
    st.markdown("### 🎯 Select for AI Generation")
    
    is_selected = is_image_selected(current_item, 'slideshow')

    col1, col2 = st.columns([3, 2])
    with col1:
        if is_selected:
            if st.button("✓ Selected - Click to Remove", type="secondary", use_container_width=True):
                remove_from_selection(current_item, 'slideshow')
                st.rerun()
        else:
            if st.button("➕ Add to Selection", type="primary", use_container_width=True):
                # Check against total limit across all sources
                if get_total_selected_count() < 10:
                    if add_to_selection(current_item, 'slideshow'):
                        st.success("✓ Image added!")
                        st.rerun()
                    else:
                        st.error("Could not add image: Invalid data.")
                else:
                    st.warning("⚠️ Maximum 10 images can be selected across all pages")
    
    with col2:
        st.metric("Total Selected", f"{get_total_selected_count()}/10")
    
    slideshow_selected = st.session_state.get('selected_slideshow_images', [])
    if slideshow_selected:
        st.markdown("#### 📋 Selected from Slideshow")
        selected_preview_cols = st.columns(min(6, len(slideshow_selected)))
        for i, sel_img in enumerate(slideshow_selected[:6]):
            with selected_preview_cols[i]:
                # Ensure images are normalized before display
                display_image_with_fallback(sel_img, caption=f"#{i+1}", show_source=False, width=80)
        if len(slideshow_selected) > 6:
            st.info(f"... and {len(slideshow_selected) - 6} more from slideshow")
    
    # Navigation buttons for slideshow
    st.markdown("---")
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 1])
    with nav_col1:
        if st.button("⏪ Previous", use_container_width=True):
            if st.session_state.images:
                if st.session_state.loop_mode:
                    st.session_state.current_index = (idx - 1 + total) % total
                else:
                    st.session_state.current_index = max(0, idx - 1)
                st.rerun()
    with nav_col2:
        if st.button("⏩ Next", use_container_width=True):
            if st.session_state.images:
                if st.session_state.loop_mode:
                    st.session_state.current_index = (idx + 1) % total
                else:
                    st.session_state.current_index = min(total - 1, idx + 1)
                st.rerun()
    with nav_col3:
        if st.button("⏯️ Play/Pause", use_container_width=True):
            st.session_state.autoplay = not st.session_state.autoplay
            st.rerun()
    with col4: # Corrected column assignment for the last button
        # Clear only slideshow selection here
        if st.button("🗑️ Clear Slideshow Selection", use_container_width=True, disabled=not slideshow_selected):
            st.session_state.selected_slideshow_images = []
            sync_master_selection()
            st.rerun()
    
    # Button to navigate to Generate page
    # Use unified count for button enablement
    if get_total_selected_count() > 0:
        if st.button("➡️ Go to Generate Page", type="primary", use_container_width=True, help="Navigate to the Generate page with your selected images"):
            st.session_state.current_page = "Generate"
            st.rerun()


def display_generate_page():
    st.title("🎨 Generate New Images")
    
    render_selection_preview_banner()
    
    sync_master_selection()
    all_selected = st.session_state.get('selected_images', [])
    
    if all_selected:
        st.markdown("""
        <div style='background:linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                    color:white;padding:16px;border-radius:12px;margin-bottom:20px;
                    box-shadow:0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='margin:0;'>✓ {count} Images Ready for Generation</h3>
            <p style='margin:4px 0 0 0;opacity:0.9;font-size:14px;'>These images can be used as reference or edit sources</p>
        </div>
        """.format(count=len(all_selected)), unsafe_allow_html=True)
        
        with st.expander("📸 View All Selected Images", expanded=True):
            cols = st.columns(min(5, len(all_selected)))
            for i, img in enumerate(all_selected):
                col_idx = i % 5
                with cols[col_idx]:
                    display_image_with_fallback(img, caption=f"#{i+1}", show_source=False)
                    # Show source badge
                    source = img.get('selection_source', 'unknown')
                    st.markdown(f"<small style='color:#888;'>From: {source}</small>", unsafe_allow_html=True)
        
        # Clear all selections button
        if st.button("Clear All Selections"):
            clear_all_selections()
            st.rerun()

    # API Key check
    if not st.session_state.api_key:
        st.error("Please configure your API Key in the sidebar to start generating images.")
        return

    tab1, tab2, tab3 = st.tabs(["Text-to-Image", "Image Edit (Qwen)", "Image Edit (Seedream)"])

    with tab1:
        st.header("Text-to-Image Generation")
        
        with st.form("text_to_image_form"):
            prompt = st.text_area("Prompt", "A photorealistic image of a majestic lion wearing a crown, digital art, highly detailed")
            negative_prompt = st.text_area("Negative Prompt (Optional)", "blurry, low quality, bad anatomy, deformed")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                model = st.selectbox("Model", ["stable-diffusion-xl", "dall-e-3", "midjourney-v6"], index=0)
            with col2:
                width = st.slider("Width", 512, 1024, 1024, step=64)
            with col3:
                height = st.slider("Height", 512, 1024, 1024, step=64)
            
            num_images = st.slider("Number of Images", 1, 4, 1)
            
            submitted = st.form_submit_button("Generate Image")
            
            if submitted:
                input_params = {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "num_images": num_images
                }
                
                with st.spinner("Creating task..."):
                    result = create_task(st.session_state.api_key, model, input_params)
                
                if result["success"]:
                    task_id = result["task_id"]
                    st.success(f"Task created successfully. Task ID: `{task_id}`")
                    
                    # Add task to history with initial status
                    st.session_state.task_history.insert(0, {
                        "id": task_id,
                        "model": model,
                        "prompt": prompt,
                        "status": "waiting",
                        "created_at": datetime.now().isoformat(),
                        "results": []
                    })
                    st.session_state.current_task = task_id # Mark current task for potential polling
                    st.rerun()
                else:
                    display_error_with_help(result.get('error', 'Unknown error')) # Use enhanced error display

    with tab2:
        st.header("✏️ Image Edit - Qwen Model")
        st.info("Edit images using AI-powered Qwen model")
        
        default_qwen_url = "https://file.aiquickdraw.com/custom-page/akr/section-images/1755603225969i6j87xnw.jpg"
        selected_image_data = None
        image_url_input = default_qwen_url # Default value for input field

        # Prioritize image selected from Slideshow page
        if st.session_state.selected_slideshow_images:
            selected_image_data = st.session_state.selected_slideshow_images[0]
            image_url_input = get_best_streamlit_url(selected_image_data) or default_qwen_url
        # Then prioritize image selected for edit (e.g. from Library)
        elif st.session_state.selected_image_for_edit:
            selected_image_data = st.session_state.selected_image_for_edit
            image_url_input = get_best_streamlit_url(selected_image_data) or default_qwen_url
            
        with st.form("qwen_image_edit_form"):
            prompt = st.text_area("Prompt", "Make the image more vibrant and colorful, add a subtle glow")
            negative_prompt = st.text_area("Negative Prompt (Optional)", "blurry, ugly, low quality, distorted")
            
            # If image is selected from Slideshow, display it and allow choosing from selection
            if st.session_state.selected_slideshow_images:
                image_to_edit_display = selected_image_data
                st.success(f"Using image from selection: {st.session_state.selected_slideshow_images[0].get('name', 'Unknown')}")
                
                # Allow selecting a different image from the slideshow selection
                if len(st.session_state.selected_slideshow_images) > 1:
                    # Create a mapping of display names to indices for the selectbox
                    image_options = {f"Image {i+1}: {img.get('name', 'Unknown')[:30]}": i 
                                    for i, img in enumerate(st.session_state.selected_slideshow_images)}
                    selected_idx_name = st.selectbox("Choose image to edit", options=list(image_options.keys()), key="qwen_img_select_from_list")
                    selected_index = image_options[selected_idx_name]
                    image_to_edit_display = st.session_state.selected_slideshow_images[selected_index]
                    image_url_input = get_best_streamlit_url(image_to_edit_display) or default_qwen_url
                
                # Show preview of the selected image for editing
                display_image_with_fallback(image_to_edit_display, caption="Image to Edit", show_source=True, width=300)
                
            # If no slideshow image selected, offer library or manual URL
            else:
                use_library_image = False
                # Only show library option if authenticated and library has images
                if st.session_state.gdrive_authenticated and st.session_state.library_images:
                    # Check if an image was selected for edit from library previously
                    use_library_image = st.checkbox("Use image from library", value=bool(st.session_state.selected_image_for_edit), key="qwen_lib_check")
                
                if use_library_image:
                    library_options = {img.get('name', f"Image {i}"): img for i, img in enumerate(st.session_state.library_images) if img.get('name')}
                    
                    if library_options:
                        selected_name = st.selectbox("Select Image", options=list(library_options.keys()), key="qwen_lib_select")
                        selected_img_data = library_options[selected_name]
                        selected_img_data = normalize_image_urls(selected_img_data) # Normalize for display
                        image_url_input = get_best_streamlit_url(selected_img_data) or default_qwen_url
                        # Display preview from library
                        display_image_with_fallback(selected_img_data, caption=selected_name, show_source=True, width=200)
                    else:
                        st.warning("No images found in library.")
                        image_url_input = st.text_input("Image URL", default_qwen_url, key="qwen_url_input_fallback")
                else:
                    # Manual URL input
                    image_url_input = st.text_input("Image URL", image_url_input, key="qwen_url_input")
                    st.caption("💡 Or select images from Slideshow page first, or use the library option")

            col1, col2, col3 = st.columns(3)
            with col1:
                image_size = st.selectbox("Image Size", ["square", "square_hd", "portrait_4_3", "portrait_16_9", "landscape_4_3", "landscape_16_9"], index=1)
            with col2:
                num_steps = st.slider("Inference Steps", 2, 49, 25)
            with col3:
                guidance_scale = st.slider("Guidance Scale", 0.0, 20.0, 4.0)
            
            submitted = st.form_submit_button("Edit Image (Qwen)")
            
            if submitted:
                if not image_url_input:
                    st.error("Please provide an image URL or select an image from the library/selection.")
                else:
                    input_params = {
                        "prompt": prompt,
                        "image_url": image_url_input,
                        "negative_prompt": negative_prompt,
                        "image_size": image_size,
                        "num_inference_steps": num_steps,
                        "guidance_scale": guidance_scale,
                        "enable_safety_checker": True,
                        "output_format": "png" # Assuming PNG is default/preferred
                    }
                    
                    with st.spinner("Creating edit task..."):
                        result = create_task(st.session_state.api_key, "qwen/image-edit", input_params)
                    
                    if result["success"]:
                        task_id = result["task_id"]
                        st.success(f"Task created successfully. Task ID: `{task_id}`")
                        
                        # Add task to history
                        st.session_state.task_history.insert(0, {
                            "id": task_id,
                            "model": "qwen/image-edit",
                            "prompt": prompt,
                            "status": "waiting",
                            "created_at": datetime.now().isoformat(),
                            "results": []
                        })
                        st.session_state.current_task = task_id
                        # Clear selected image for edit after task creation
                        st.session_state.selected_image_for_edit = None
                        st.session_state.edit_mode = None
                        st.rerun()
                    else:
                        display_error_with_help(result.get('error', 'Unknown error')) # Use enhanced error display

    with tab3:
        st.header("✨ Image Edit - Seedream Model")
        st.info("Advanced image editing with Seedream AI")
        
        default_seedream_url = "https://file.aiquickdraw.com/custom-page/akr/section-images/1755603225969i6j87xnw.jpg"
        selected_image_data = None
        image_url_input = default_seedream_url
        
        # Prioritize image selected from Slideshow page
        if st.session_state.selected_slideshow_images:
            selected_image_data = st.session_state.selected_slideshow_images[0]
            image_url_input = get_best_streamlit_url(selected_image_data) or default_seedream_url
        # Then prioritize image selected for edit (e.g. from Library)
        elif st.session_state.selected_image_for_edit:
            selected_image_data = st.session_state.selected_image_for_edit
            image_url_input = get_best_streamlit_url(selected_image_data) or default_seedream_url
            
        with st.form("seedream_image_edit_form"):
            prompt = st.text_area("Prompt", "Transform the image with dramatic lighting and enhanced details")
            negative_prompt = st.text_area("Negative Prompt (Optional)", "blurry, distorted, low quality")
            
            # If image is selected from Slideshow, display it and allow choosing from selection
            if st.session_state.selected_slideshow_images:
                image_to_edit_display = selected_image_data
                st.success(f"Using image from selection: {st.session_state.selected_slideshow_images[0].get('name', 'Unknown')}")

                if len(st.session_state.selected_slideshow_images) > 1:
                    image_options = {f"Image {i+1}: {img.get('name', 'Unknown')[:30]}": i 
                                    for i, img in enumerate(st.session_state.selected_slideshow_images)}
                    selected_idx_name = st.selectbox("Choose image to edit", options=list(image_options.keys()), key="seedream_img_select_from_list")
                    selected_index = image_options[selected_idx_name]
                    image_to_edit_display = st.session_state.selected_slideshow_images[selected_index]
                    image_url_input = get_best_streamlit_url(image_to_edit_display) or default_seedream_url
                
                display_image_with_fallback(image_to_edit_display, caption="Image to Edit", show_source=True, width=300)
                
            # If no slideshow image selected, offer library or manual URL
            else:
                use_library_image = False
                if st.session_state.gdrive_authenticated and st.session_state.library_images:
                    use_library_image = st.checkbox("Use image from library", value=bool(st.session_state.selected_image_for_edit), key="seedream_lib_check")
                
                if use_library_image:
                    library_options = {img.get('name', f"Image {i}"): img for i, img in enumerate(st.session_state.library_images) if img.get('name')}
                    
                    if library_options:
                        selected_name = st.selectbox("Select Image", options=list(library_options.keys()), key="seedream_lib_select")
                        selected_img_data = library_options[selected_name]
                        selected_img_data = normalize_image_urls(selected_img_data)
                        image_url_input = get_best_streamlit_url(selected_img_data) or default_seedream_url
                        display_image_with_fallback(selected_img_data, caption=selected_name, show_source=True, width=200)
                    else:
                        st.warning("No images found in library.")
                        image_url_input = st.text_input("Image URL", default_seedream_url, key="seedream_url_input_fallback")
                else:
                    image_url_input = st.text_input("Image URL", image_url_input, key="seedream_url_input")
                    st.caption("💡 Or select images from Slideshow page first, or use the library option")

            col1, col2 = st.columns(2)
            with col1:
                image_size = st.selectbox("Image Size", ["square", "square_hd", "portrait_4_3", "landscape_4_3"], index=1, key="seedream_size")
            with col2:
                image_resolution = st.selectbox("Image Resolution", ["1K", "2K", "4K"], index=0, key="seedream_res")
            
            submitted = st.form_submit_button("Edit Image (Seedream)")
            
            if submitted:
                if not image_url_input:
                    st.error("Please provide an image URL or select an image from the library/selection.")
                else:
                    input_params = {
                        "prompt": prompt,
                        "image_url": image_url_input,
                        "negative_prompt": negative_prompt,
                        "image_size": image_size,
                        "image_resolution": image_resolution
                    }
                    
                    with st.spinner("Creating edit task..."):
                        result = create_task(st.session_state.api_key, "seedream/image-edit-v4", input_params)
                    
                    if result["success"]:
                        task_id = result["task_id"]
                        st.success(f"Task created successfully. Task ID: `{task_id}`")
                        
                        st.session_state.task_history.insert(0, {
                            "id": task_id,
                            "model": "seedream/image-edit-v4",
                            "prompt": prompt,
                            "status": "waiting",
                            "created_at": datetime.now().isoformat(),
                            "results": []
                        })
                        st.session_state.current_task = task_id
                        st.session_state.selected_image_for_edit = None
                        st.session_state.edit_mode = None
                        st.rerun()
                    else:
                        display_error_with_help(result.get('error', 'Unknown error')) # Use enhanced error display

def display_history_page():
    """History page with selection capability."""
    st.title("📜 Task History")
    
    render_selection_preview_banner()
    
    if not st.session_state.task_history:
        st.info("No tasks yet. Create your first generation task to get started!")
        return
    
    for i, task in enumerate(st.session_state.task_history):
        task_id = task['id']
        status = task['status']
        
        st.markdown(f"<div class='image-card' style='margin-bottom:15px;'>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([0.5, 2, 1, 1])
        col1.markdown(f"**{i+1}.**")
        col2.markdown(f"**Prompt:** `{task['prompt'][:60]}{'...' if len(task['prompt']) > 60 else ''}`")
        col3.markdown(f"**Model:** `{task['model']}`")
        col4.markdown(f"**Status:** <span class='status-badge status-{status}'>{status.upper()}</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        if status == 'waiting' or status == 'processing':
            if st.button("🔄 Check Status", key=f"check_{task_id}"):
                st.session_state.polling_active = True
                st.session_state.current_task = task_id
                st.rerun()
            
            if st.session_state.polling_active and st.session_state.current_task == task_id:
                st.info("⏳ Polling for task status...")
                
                result = poll_task_until_complete(st.session_state.api_key, task_id)
                
                st.session_state.polling_active = False
                st.session_state.current_task = None
                
                if result["success"]:
                    try:
                        # Safely get resultJson from data
                        result_json_str = result.get('data', {}).get('resultJson', '{}')
                        result_data = json.loads(result_json_str)
                        result_urls = result_data.get('resultUrls', [])
                        
                        if result_urls: # Proceed only if there are URLs
                            save_and_upload_results(task_id, task['model'], task['prompt'], result_urls)
                            st.success("✅ Task completed and results updated!")
                            st.rerun()
                        else:
                            # Task succeeded but returned no URLs
                            st.warning("⚠️ Task completed but no result URLs found")
                            st.session_state.task_history[i]['status'] = 'fail' # Mark as fail if no results
                            st.session_state.task_history[i]['error'] = 'No result URLs returned'
                            st.session_state.stats['failed_tasks'] += 1 # Count as failed if no results
                            st.rerun()
                    except json.JSONDecodeError as e:
                        st.error(f"❌ Failed to parse task results: {str(e)}")
                        st.session_state.task_history[i]['status'] = 'fail'
                        st.session_state.task_history[i]['error'] = f'JSON Decode Error: {str(e)}'
                        st.session_state.stats['failed_tasks'] += 1
                        st.rerun()
                else:
                    fail_msg = result.get('error', 'Unknown error')
                    st.session_state.task_history[i]['status'] = 'fail'
                    st.session_state.task_history[i]['error'] = fail_msg
                    st.session_state.stats['failed_tasks'] += 1
                    display_error_with_help(fail_msg)
                    st.rerun()
        
        elif status == 'success':
            st.markdown("#### ✨ Results")
            if task.get('results'): # Safely check if results exist
                result_grid_cols = 3
                
                for res_idx, result_item in enumerate(task['results']):
                    if res_idx % result_grid_cols == 0:
                        cols = st.columns(result_grid_cols)
                    
                    with cols[res_idx % result_grid_cols]:
                        result_url = None
                        img_data_for_display = {}

                        if isinstance(result_item, str):
                            # Legacy string URL format
                            result_url = result_item
                            img_data_for_display = {
                                'original_generation_url': result_url,
                                'url': result_url,
                                'name': f"Result {res_idx+1}",
                                'task_id': task_id,
                                'source': 'ai_generated_legacy' # Indicate legacy format
                            }
                        else:
                            # New normalized dict format
                            img_data_for_display = result_item.copy() # Use a copy
                            result_url = img_data_for_display.get('url', img_data_for_display.get('original_generation_url', ''))
                        
                        # Normalize and display the image data
                        img_data_for_display = normalize_image_urls(img_data_for_display)
                        
                        display_image_with_fallback(img_data_for_display, caption=f"Result {res_idx+1}", show_source=True)
                        
                        # Show URL options for debugging
                        with st.expander("🔗 View All URLs"):
                            display_url_options_card(img_data_for_display)
                        
                        # Download button
                        try:
                            # Use the best available URL for download
                            download_url = get_best_streamlit_url(img_data_for_display)
                            if not download_url:
                                download_url = result_url  # Fallback to original if best URL not found
                            
                            if download_url: # Proceed only if we have a download URL
                                img_response = requests.get(download_url, timeout=15)
                                img_response.raise_for_status()
                                
                                # Determine file extension
                                file_extension = 'png'  # Default
                                parts = download_url.split('.')
                                if len(parts) > 1:
                                    potential_ext = parts[-1].split('?')[0].lower()
                                    if potential_ext in ['png', 'jpg', 'jpeg', 'webp']:
                                        file_extension = potential_ext
                                
                                st.download_button(
                                    label="⬇️ Download",
                                    data=img_response.content,
                                    file_name=f"{task['model'].replace('/', '_')}_{task_id}_{res_idx+1}.{file_extension}",
                                    mime=f"image/{file_extension}",
                                    key=f"download_{task_id}_{res_idx}",
                                    use_container_width=True
                                )
                        except requests.exceptions.Timeout:
                            print(f"[v0] Download timed out for {download_url}")
                            st.warning("⚠️ Download timed out")
                        except Exception as e:
                            print(f"[v0] Download failed for {download_url}: {str(e)}")
                            st.warning("⚠️ Download unavailable")
                        
                        # Upload to Drive button
                        if st.session_state.gdrive_authenticated:
                            # Check if this image is already in the library based on its URL
                            is_uploaded = any(
                                lib_img.get('url') == result_url or lib_img.get('original_url') == result_url
                                for lib_img in st.session_state.library_images
                            )
                            
                            if not is_uploaded:
                                if st.button("☁️ Upload to Drive", key=f"upload_{task_id}_{res_idx}", use_container_width=True):
                                    # Determine file extension for upload
                                    file_extension = 'png'
                                    parts = result_url.split('.') if result_url else []
                                    if len(parts) > 1:
                                        potential_ext = parts[-1].split('?')[0].lower()
                                        if potential_ext in ['png', 'jpg', 'jpeg', 'webp']:
                                            file_extension = potential_ext
                                    
                                    # Generate a sensible filename
                                    file_name = f"{task['model'].replace('/', '_')}_{task_id}_{res_idx+1}.{file_extension}"
                                    
                                    with st.spinner(f"Uploading '{file_name}'..."):
                                        upload_info = upload_to_drive(result_url, file_name, task_id)
                                        if upload_info: # upload_to_drive returns the webViewLink on success
                                            # Add the uploaded item to the library session state for immediate visual feedback
                                            # Create a normalized representation for the library
                                            uploaded_image_data = normalize_image_urls({
                                                'url': upload_info,
                                                'name': file_name,
                                                'source': 'gdrive_upload',
                                                'folder_name': 'Drive Storage', # Generic for uploaded files
                                                'webViewLink': upload_info
                                            })
                                            st.session_state.library_images.insert(0, uploaded_image_data)
                                            st.session_state.all_library_images.insert(0, uploaded_image_data) # Also add to the main library list
                                            st.session_state.stats['uploaded_images'] += 1
                                            st.success(f"✅ Uploaded '{file_name}' to Drive!")
                                            st.rerun()
                                        else:
                                            st.error("❌ Upload failed")
                            else:
                                st.success("✓ Already in Drive")
            else:
                st.info("ℹ️ No results found for this task")
        
        elif status == 'fail':
            error_msg = task.get('error', 'Unknown error')
            display_error_with_help(error_msg)
        
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# Library Page
# ============================================================================
def list_all_drive_folders_images():
    """Fetch images from all saved folders (public folders via scraping)."""
    all_images = []
    
    print(f"[v0] Fetching images from {len(st.session_state.saved_folders)} saved folders...")
    
    # Ensure saved_folders is a list of dicts with 'name' and 'url'
    if not isinstance(st.session_state.saved_folders, list):
        st.session_state.saved_folders = [{"name": k, "url": v} for k, v in st.session_state.saved_folders.items()]

    for folder_config in st.session_state.saved_folders:
        folder_name = folder_config['name']
        folder_url = folder_config['url']
        
        try:
            folder_id = extract_folder_id(folder_url)
            print(f"[v0] Loading images from '{folder_name}' (ID: {folder_id})")
            
            # Get images from public folder using the scraping method
            folder_images = get_gdrive_image_urls(folder_id, folder_name)
            
            if folder_images:
                print(f"[v0] Found {len(folder_images)} images in '{folder_name}'")
                all_images.extend(folder_images)
            else:
                print(f"[v0] No images found in '{folder_name}'")
                
        except Exception as e:
            print(f"[v0] Error loading folder '{folder_name}': {str(e)}")
            st.warning(f"Could not load images from '{folder_name}': {str(e)}")
    
    print(f"[v0] Total images loaded from all public folders: {len(all_images)}")
    return all_images

def load_complete_library():
    """Load all images from both authenticated Drive storage and public folders."""
    all_library_images = []
    
    # Part 1: Get images from authenticated Google Drive (uploaded generations)
    if st.session_state.gdrive_authenticated and st.session_state.service and st.session_state.gdrive_folder_id:
        with st.spinner("📥 Loading images from your Google Drive storage..."):
            drive_images = list_gdrive_images(folder_id=st.session_state.gdrive_folder_id, fetch_all=True)
            if drive_images:
                all_library_images.extend(drive_images)
                st.success(f"✓ Loaded {len(drive_images)} images from your Drive storage")
    
    # Part 2: Get images from all saved public folders
    with st.spinner("📂 Loading images from saved public folders..."):
        public_folder_images = list_all_drive_folders_images()
        if public_folder_images:
            all_library_images.extend(public_folder_images)
            st.success(f"✓ Loaded {len(public_folder_images)} images from {len(st.session_state.saved_folders)} public folder(s)")
    
    # Remove duplicates based on file_id, id, or url
    seen_identifiers = set()
    unique_images = []
    for img in all_library_images:
        # Create a unique identifier for deduplication
        img_identifier = get_image_id(img) # Use helper for robust ID generation
        if img_identifier and img_identifier not in seen_identifiers:
            seen_identifiers.add(img_identifier)
            # Ensure normalization for all library images
            unique_images.append(normalize_image_urls(img))
    
    st.session_state.all_library_images = unique_images # Store in session state for library page
    st.session_state.library_loaded = True # Mark as loaded
    print(f"[v0] Total unique images loaded into library: {len(unique_images)}")
    return unique_images

def display_library_page():
    """Library page with enhanced selection persistence."""
    st.title("📚 Image Library")
    
    render_selection_preview_banner()
    
    # Auto-load library on first visit or when explicitly reloaded
    if not st.session_state.get('library_loaded'):
        with st.spinner("Loading complete library from all sources..."):
            load_complete_library()
            # No rerun here, allow other parts of the page to render based on loaded data
    
    # Get all images from library
    all_library_images = st.session_state.get('all_library_images', [])
    
    if not all_library_images:
        st.info("No images in library. Load folders from Slideshow page to populate library, or connect Google Drive to upload generated images.")
        
        if st.button("🔄 Reload Library", use_container_width=True):
            with st.spinner("Reloading library..."):
                load_complete_library()
            st.rerun()
        return
    
    # Get total count for stats
    total_images_overall = len(all_library_images)
    
    # Get current sort preference from session state or default to "newest"
    current_sort = st.session_state.get('library_sort_by', 'Newest First')
    
    # Sorting options
    sort_options = ["Newest First", "Oldest First", "Name (A-Z)", "Name (Z-A)", "Size (Largest)", "Size (Smallest)"]
    
    # Render sort control
    sort_by = st.selectbox("Sort by", sort_options, key="library_sort_selector", 
                           index=sort_options.index(current_sort) if current_sort in sort_options else 0)
    
    # Update session state only if the value has changed from the widget
    if sort_by != st.session_state.get('library_sort_by'):
        st.session_state.library_sort_by = sort_by
        st.rerun() # Rerun to apply sorting immediately

    # Apply sorting
    sorted_images = all_library_images.copy()
    if sort_by == "Newest First":
        sorted_images.sort(key=lambda x: x.get('createdTime', ''), reverse=True)
    elif sort_by == "Oldest First":
        sorted_images.sort(key=lambda x: x.get('createdTime', ''), reverse=False)
    elif sort_by == "Name (A-Z)":
        sorted_images.sort(key=lambda x: x.get('name', '').lower())
    elif sort_by == "Name (Z-A)":
        sorted_images.sort(key=lambda x: x.get('name', '').lower(), reverse=True)
    elif sort_by == "Size (Largest)":
        sorted_images.sort(key=lambda x: int(x.get('size', 0)), reverse=True)
    elif sort_by == "Size (Smallest)":
        sorted_images.sort(key=lambda x: int(x.get('size', 0)), reverse=False)
    
    # Search and filter section
    st.markdown("---")
    search_col, filter_col, space_col = st.columns([3, 2, 1])
    with search_col:
        search_query = st.text_input("🔍 Search images by name", value="", key="lib_search")
    with filter_col:
        filter_options = ["All", "Drive Storage", "Public Folders"]
        current_filter_type = st.session_state.get('library_filter_type', 'All')
        
        source_filter = st.selectbox("Filter by source", filter_options, key="library_source_filter", 
                                     index=filter_options.index(current_filter_type) if current_filter_type in filter_options else 0)
        
        # Update session state only if value changed from widget
        if source_filter != st.session_state.get('library_filter_type'):
            st.session_state.library_filter_type = source_filter
            st.rerun() # Rerun to apply filter immediately

    
    filtered_images = sorted_images
    if search_query:
        filtered_images = [img for img in filtered_images if search_query.lower() in img.get('name', '').lower()]
    
    # Apply source filter
    if source_filter == "Drive Storage":
        # Filter for images uploaded to authenticated Drive
        filtered_images = [img for img in filtered_images if img.get('source') in ['gdrive_upload', 'gdrive_storage']]
    elif source_filter == "Public Folders":
        # Filter for images loaded from public folders (excluding authenticated uploads)
        filtered_images = [img for img in filtered_images if img.get('source') == 'gdrive_public']
    
    st.markdown(f"**Showing {len(filtered_images):,} of {total_images_overall:,} images**")
    
    # Display options
    st.markdown("---")
    
    # View mode selection
    view_mode_options = ["Grid", "List", "By Folder"]
    current_view_mode = st.session_state.get('library_view_mode', 'Grid')
    
    view_mode = st.radio(
        "Display Mode", 
        view_mode_options, 
        key="library_view_mode",
        horizontal=True,
        index=view_mode_options.index(current_view_mode) if current_view_mode in view_mode_options else 0
    )
    
    # Update session state if view mode changed
    if view_mode != st.session_state.get('library_view_mode'):
        st.session_state.library_view_mode = view_mode
        st.rerun()

    # Display by folder view
    if view_mode == "By Folder":
        st.markdown("### 📁 Images Organized by Folder")
        
        # Organize images by folder
        folders_dict = organize_images_by_folder(filtered_images)
        
        # Display each folder
        for folder_name, folder_images in folders_dict.items():
            with st.expander(f"📁 {folder_name} ({len(folder_images)} images)", expanded=True):
                cols = st.columns(4)
                for i, img in enumerate(folder_images):
                    with cols[i % 4]:
                        display_image_with_fallback(img, caption=img.get('name', 'Image'), show_source=True)
                        
                        # Selection checkbox
                        img_id_for_key = get_image_id(img) or f'unknown_{i}'
                        is_selected = is_image_selected(img, 'library')
                        
                        # Use a unique key for each checkbox
                        if st.checkbox(f"Select", key=f"lib_img_{img_id_for_key}", value=is_selected):
                            if not is_selected:
                                add_to_selection(img, 'library')
                        else:
                            if is_selected:
                                remove_from_selection(img, 'library')

    elif view_mode == "List":
        # List view with detailed URLs
        for idx, image_data in enumerate(filtered_images):
            with st.container():
                st.markdown("---")
                
                col_img, col_info = st.columns([1, 2])
                
                with col_img:
                    display_image_with_fallback(image_data, caption=image_data.get('name', f'Image {idx+1}'), show_source=True)
                
                with col_info:
                    st.markdown(f"### {image_data.get('name', f'Image {idx+1}')}")
                    
                    # Metadata badges
                    metadata_html = "<div style='margin:12px 0;'>"
                    
                    if image_data.get('folder_name'):
                        metadata_html += f"<span style='background:#6c757d;color:white;padding:4px 8px;border-radius:4px;font-size:11px;margin-right:6px;'>📁 {image_data.get('folder_name')}</span>"
                    
                    if image_data.get('size'):
                        try:
                            size_bytes = int(image_data['size'])
                            if size_bytes >= 1024 * 1024:
                                size_str = f"{size_bytes / (1024*1024):.2f} MB"
                            elif size_bytes >= 1024:
                                size_str = f"{size_bytes / 1024:.1f} KB"
                            else:
                                size_str = f"{size_bytes} B"
                            metadata_html += f"<span style='background:#17a2b8;color:white;padding:4px 8px;border-radius:4px;font-size:11px;margin-right:6px;'>💾 {size_str}</span>"
                        except (ValueError, TypeError):
                            pass

                    if image_data.get('createdTime'):
                        try:
                            created_dt_str = image_data['createdTime']
                            if created_dt_str.endswith('Z'):
                                created_dt_str = created_dt_str[:-1] + '+00:00'
                            created_date = datetime.fromisoformat(created_dt_str)
                            date_str = created_date.strftime('%Y-%m-%d %H:%M')
                            metadata_html += f"<span style='background:#28a745;color:white;padding:4px 8px;border-radius:4px;font-size:11px;margin-right:6px;'>📅 {date_str}</span>"
                        except: # Handle potential datetime parsing errors
                            pass
                    
                    metadata_html += "</div>"
                    st.markdown(metadata_html, unsafe_allow_html=True)
                    
                    # URLs section
                    with st.expander("🔗 View All URLs & Test", expanded=False):
                        display_url_options_card(image_data)
                    
                    # Action buttons
                    st.markdown("### Actions")
                    act_col1, act_col2, act_col3 = st.columns(3)
                    
                    with act_col1:
                        if st.button("✏️ Qwen Edit", key=f"lib_qwen_{idx}", use_container_width=True):
                            st.session_state.selected_image_for_edit = image_data
                            st.session_state.edit_mode = 'qwen'
                            st.session_state.current_page = "Generate"
                            st.rerun()
                    
                    with act_col2:
                        if st.button("🎨 Seedream", key=f"lib_seedream_{idx}", use_container_width=True):
                            st.session_state.selected_image_for_edit = image_data
                            st.session_state.edit_mode = 'seedream'
                            st.session_state.current_page = "Generate"
                            st.rerun()
                    
                    with act_col3:
                        download_url = get_best_streamlit_url(image_data) or image_data.get('url')
                        if download_url:
                            # Directly create a markdown link for download
                            st.markdown(f"[⬇️ Download]({download_url})", unsafe_allow_html=True)
                            st.caption("Click to download")
    
    else:  # Grid view (default)
        display_image_grid(filtered_images, columns=4, show_metadata=True, show_actions=True)
    
    # Action bar for selected library images
    # Use new selection management functions and show library-specific actions
    library_selected = st.session_state.get('selected_library_images', [])
    if library_selected:
        st.markdown("---")
        st.markdown("### Selected Library Images")
        sel_preview_cols = st.columns(min(6, len(library_selected)))
        for i, sel_img in enumerate(library_selected[:6]):
            with sel_preview_cols[i]:
                # Use cached normalized image
                normalized_sel_img = get_or_cache_normalized_image(sel_img)
                if normalized_sel_img:
                    display_image_with_fallback(normalized_sel_img, caption=f"#{i+1}", show_source=False, width=80)
        if len(library_selected) > 6:
            st.info(f"... and {len(library_selected) - 6} more selected from library")

        act_col1, act_col2, act_col3 = st.columns(3)
        with act_col1:
            if st.button("Qwen Edit Selected", use_container_width=True):
                if library_selected:
                    # Take the first selected image for editing
                    st.session_state.selected_image_for_edit = library_selected[0] 
                    st.session_state.edit_mode = 'qwen'
                    st.session_state.current_page = "Generate"
                    st.rerun()
        with act_col2:
            if st.button("Seedream Selected", use_container_width=True):
                if library_selected:
                    st.session_state.selected_image_for_edit = library_selected[0] # Take the first selected
                    st.session_state.edit_mode = 'seedream'
                    st.session_state.current_page = "Generate"
                    st.rerun()
        with act_col3:
            if st.button("Clear Library Selection", use_container_width=True):
                st.session_state.selected_library_images = []
                sync_master_selection()
                st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Library Statistics")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("Displayed Images", f"{len(filtered_images):,}")
    with stat_col2:
        folders_count = len(organize_images_by_folder(filtered_images))
        st.metric("Folders Shown", folders_count)
    with stat_col3:
        total_size = sum(int(img.get('size', 0)) for img in filtered_images if img.get('size'))
        total_size_mb = total_size / (1024*1024) if total_size > 0 else 0
        st.metric("Total Size", f"{total_size_mb:.1f} MB")
    with stat_col4:
        avg_size = total_size_mb / len(filtered_images) if filtered_images else 0
        st.metric("Avg Size", f"{avg_size:.2f} MB")

# ============================================================================
# Utility Functions for Error Display
# ============================================================================
def display_error_with_help(error_message):
    """Display error with helpful troubleshooting information."""
    st.error(f"❌ Error: {error_message}")
    
    with st.expander("🔧 Troubleshooting Tips"):
        st.markdown(f"""
        **Common Issues and Solutions:**
        
        1. **Network/Connection Errors:**
           - Check your internet connection.
           - Try again in a few moments.
           - The API service may be temporarily unavailable or overloaded.
        
        2. **API Key Issues:**
           - Verify your API key is correct in the sidebar settings.
           - Check if your API account has sufficient credits or has expired.
        
        3. **Timeout Errors:**
           - The server may be under heavy load.
           - Try with simpler prompts, lower resolutions, or fewer images.
           - Wait a few minutes and try again.
        
        4. **DNS/Resolution Errors:**
           - The API endpoint may be temporarily unreachable.
           - Your network might be blocking the API domain.
           - Try using a different network connection if possible.
           
        5. **Quota Exceeded:**
           - Your account may have reached its generation or upload quota. Check your API provider's dashboard.
        
        **Current Configuration:**
        - Primary Endpoint: `{API_BASE_URL}`
        - Fallback Endpoint: `{API_FALLBACK_URL}`
        - Retry Attempts: {MAX_RETRIES}
        - Timeout: 30 seconds (for API calls)
        """)

# ============================================================================
# Main Page Router
# ============================================================================
if st.session_state.current_page == "Slideshow":
    render_slideshow_page()
elif st.session_state.current_page == "Generate":
    display_generate_page()
elif st.session_state.current_page == "History":
    display_history_page()
elif st.session_state.current_page == "Library":
    display_library_page()
