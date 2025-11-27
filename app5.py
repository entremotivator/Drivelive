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
API_BASE_URL = "https://zyloai.xyz"
API_HEADERS = {"Content-Type": "application/json"}

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
    """Initialize all session state variables."""
    defaults = {
        'default_folder_url': DEFAULT_FOLDER_URL,
        'current_index': 0,
        'autoplay': False,
        'images': [],
        'slideshow_speed': 3,
        'loop_mode': True,
        'api_key': "",
        'task_history': [],
        'current_task': None,
        'authenticated': False,
        'service': None,
        'credentials': None,
        'generated_images': [],
        'library_images': [],
        'gdrive_folder_id': None,
        'auto_upload': True,
        'polling_active': False,
        'service_account_info': None,
        'upload_queue': [],
        'stats': {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_images': 0,
            'uploaded_images': 0
        },
        'current_page': "Slideshow",
        'selected_image_for_edit': None,
        'edit_mode': None,
        'library_view_mode': 'grid',
        'library_sort_by': 'date_desc',
        'library_search_query': '',
        'library_filter_type': 'all',
        'selected_images': [],
        'show_image_modal': False,
        'modal_image_data': None,
        'selected_slideshow_images': [],
        'saved_folders': DEFAULT_FOLDERS.copy(),
        'editing_folder': None,
        'show_folder_manager': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# Drive Functions - Public Folder Access (No Auth Required)
# ============================================================================

def get_folder_name_from_id(folder_id: str) -> str:
    """Get a friendly folder name from the stored folders dictionary."""
    for name, url in st.session_state.saved_folders.items():
        if folder_id in url:
            return name
    return "Unknown Folder"

def organize_images_by_folder(images):
    """Organize images by their source folder."""
    folders = {}
    for img in images:
        folder_id = img.get('folder_id', 'unknown')
        folder_name = img.get('folder_name', get_folder_name_from_id(folder_id))
        
        if folder_name not in folders:
            folders[folder_name] = []
        folders[folder_name].append(img)
    
    return folders

def display_url_options_card(image_data):
    """Display a comprehensive card showing all available URLs for an image."""
    st.markdown("""
        <div style='background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;padding:16px;margin:12px 0;'>
            <div style='font-weight:600;font-size:14px;margin-bottom:12px;color:#212529;'>
                📎 Available Image URLs
            </div>
    """, unsafe_allow_html=True)
    
    url_types = []
    
    if image_data.get('original_generation_url'):
        url_types.append({
            'label': 'Original Generation URL',
            'url': image_data['original_generation_url'],
            'color': '#FF6B6B',
            'icon': '⭐',
            'desc': 'Best quality from AI generation'
        })
    
    if image_data.get('drive_public_url'):
        url_types.append({
            'label': 'Drive Public URL',
            'url': image_data['drive_public_url'],
            'color': '#4285F4',
            'icon': '☁️',
            'desc': 'Direct view link'
        })
    
    if image_data.get('drive_direct_link'):
        url_types.append({
            'label': 'Drive CDN Link',
            'url': image_data['drive_direct_link'],
            'color': '#34A853',
            'icon': '🚀',
            'desc': 'Fast CDN delivery'
        })
    
    if image_data.get('drive_thumbnail_url'):
        url_types.append({
            'label': 'Thumbnail URL',
            'url': image_data['drive_thumbnail_url'],
            'color': '#FBBC04',
            'icon': '🖼️',
            'desc': 'Smaller preview size'
        })
    
    if image_data.get('url'):
        url_types.append({
            'label': 'Standard URL',
            'url': image_data['url'],
            'color': '#6c757d',
            'icon': '🔗',
            'desc': 'Default image URL'
        })
    
    if image_data.get('webViewLink'):
        url_types.append({
            'label': 'Drive Web View',
            'url': image_data['webViewLink'],
            'color': '#17a2b8',
            'icon': '🌐',
            'desc': 'Open in Drive'
        })
    
    for url_info in url_types:
        st.markdown(f"""
            <div style='background:white;border-left:4px solid {url_info['color']};padding:10px;margin:8px 0;border-radius:4px;'>
                <div style='display:flex;align-items:center;margin-bottom:6px;'>
                    <span style='font-size:18px;margin-right:8px;'>{url_info['icon']}</span>
                    <span style='font-weight:600;font-size:13px;color:#212529;'>{url_info['label']}</span>
                </div>
                <div style='font-size:11px;color:#6c757d;margin-bottom:6px;'>{url_info['desc']}</div>
                <div style='background:#f8f9fa;padding:8px;border-radius:4px;font-family:monospace;font-size:10px;color:#495057;word-break:break-all;'>
                    {url_info['url'][:100]}{'...' if len(url_info['url']) > 100 else ''}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        copy_col, test_col = st.columns([1, 1])
        with copy_col:
            if st.button(f"📋 Copy", key=f"copy_{url_info['label']}_{image_data.get('id', 'unknown')}", use_container_width=True):
                st.code(url_info['url'], language="text")
        with test_col:
            if st.button(f"🧪 Test", key=f"test_{url_info['label']}_{image_data.get('id', 'unknown')}", use_container_width=True):
                try:
                    st.image(url_info['url'], caption=f"Testing {url_info['label']}", use_container_width=True)
                    st.success(f"✓ {url_info['label']} works!")
                except Exception as e:
                    st.error(f"✗ Failed: {str(e)[:50]}")
    
    st.markdown("</div>", unsafe_allow_html=True)

def extract_folder_id(url: str):
    """Extract folder ID from various Google Drive URL formats"""
    print(f"[v0] Extracting folder ID from: {url}")
    patterns = [
        r'/folders/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'^([a-zA-Z0-9_-]+)$'
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            folder_id = m.group(1)
            print(f"[v0] Found folder ID: {folder_id}")
            return folder_id
    raise ValueError("Invalid Google Drive folder link.")

def get_gdrive_image_urls(folder_id: str, folder_name: str = None):
    """
    Extract individual image URLs from a public Google Drive folder.
    Uses multiple methods to reliably fetch images from public folders.
    """
    print(f"[v0] Fetching images from folder ID: {folder_id}")
    images = []
    
    # Determine folder name
    if not folder_name:
        folder_name = get_folder_name_from_id(folder_id)
    
    try:
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(folder_url, headers=headers, timeout=15)
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
                    
                    image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
                    direct_link = f"https://lh3.googleusercontent.com/d/{file_id}"
                    thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                    
                    images.append({
                        "name": f"Image {len(images)+1}.jpg",
                        "url": image_url,
                        "source": "gdrive",
                        "file_id": file_id,
                        "folder_id": folder_id,
                        "folder_name": folder_name,
                        
                        # Multiple URL formats for reliability
                        "public_image_url": image_url,
                        "drive_public_url": image_url,
                        "drive_direct_link": direct_link,
                        "drive_thumbnail_url": thumbnail_url,
                        "original_generation_url": image_url,
                        
                        # Additional metadata
                        "webViewLink": f"https://drive.google.com/file/d/{file_id}/view",
                        "id": file_id
                    })
            
            # Method 2: 28-character file IDs
            if len(images) < 50:
                alt_file_ids = re.findall(r'"([a-zA-Z0-9_-]{28})"', html_content)
                print(f"[v0] Found {len(alt_file_ids)} additional file IDs (28 chars)")
                for file_id in alt_file_ids:
                    if file_id != folder_id and file_id not in seen and len(file_id) == 28:
                        seen.add(file_id)
                        
                        image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
                        direct_link = f"https://lh3.googleusercontent.com/d/{file_id}"
                        thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                        
                        images.append({
                            "name": f"Image {len(images)+1}.jpg",
                            "url": image_url,
                            "source": "gdrive",
                            "file_id": file_id,
                            "folder_id": folder_id,
                            "folder_name": folder_name,
                            "public_image_url": image_url,
                            "drive_public_url": image_url,
                            "drive_direct_link": direct_link,
                            "drive_thumbnail_url": thumbnail_url,
                            "original_generation_url": image_url,
                            "webViewLink": f"https://drive.google.com/file/d/{file_id}/view",
                            "id": file_id
                        })
            
            # Method 3: JSON structures
            if len(images) < 50:
                json_pattern = r'\["([a-zA-Z0-9_-]{25,})"'
                json_ids = re.findall(json_pattern, html_content)
                print(f"[v0] Found {len(json_ids)} file IDs from JSON (25+ chars)")
                for file_id in json_ids:
                    if file_id != folder_id and file_id not in seen and len(file_id) >= 25:
                        seen.add(file_id)
                        
                        image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
                        direct_link = f"https://lh3.googleusercontent.com/d/{file_id}"
                        thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                        
                        images.append({
                            "name": f"Image {len(images)+1}.jpg",
                            "url": image_url,
                            "source": "gdrive",
                            "file_id": file_id,
                            "folder_id": folder_id,
                            "folder_name": folder_name,
                            "public_image_url": image_url,
                            "drive_public_url": image_url,
                            "drive_direct_link": direct_link,
                            "drive_thumbnail_url": thumbnail_url,
                            "original_generation_url": image_url,
                            "webViewLink": f"https://drive.google.com/file/d/{file_id}/view",
                            "id": file_id
                        })
        
        print(f"[v0] Total images found: {len(images)}")
        if images:
            st.success(f"✓ Found {len(images)} images in '{folder_name}'")
            with st.expander("📋 View All Image URLs & Details", expanded=False):
                for idx, img in enumerate(images[:5], 1):  # Show first 5
                    st.markdown(f"**{idx}. {img['name']}** (Folder: {img['folder_name']})")
                    st.code(f"Original: {img['original_generation_url']}\nDirect CDN: {img['drive_direct_link']}\nThumbnail: {img['drive_thumbnail_url']}", language="text")
                if len(images) > 5:
                    st.info(f"... and {len(images) - 5} more images")
            return images
        else:
            st.warning("Could not find images. Please ensure folder has 'Anyone with the link can view' permission")
        
        return []
        
    except Exception as e:
        print(f"[v0] Error loading from Drive: {str(e)}")
        st.error(f"Error loading from Google Drive: {str(e)}")
        return []

def get_public_drive_images(folder_id: str, folder_name: str = None):
    """Get publicly accessible images from Google Drive folder."""
    return get_gdrive_image_urls(folder_id, folder_name)

# ============================================================================
# Google Drive Functions - Service Account (For Uploads)
# ============================================================================
def authenticate_with_service_account(service_account_json):
    """Authenticate with Google Drive using service account."""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            service_account_json,
            scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=credentials)
        st.session_state.credentials = credentials
        st.session_state.service = service
        st.session_state.authenticated = True
        return True, "Successfully authenticated with Google Drive"
    except Exception as e:
        return False, f"Authentication failed: {str(e)}"

def create_app_folder():
    """Create or get the app's folder in Google Drive."""
    if not st.session_state.service:
        return None
    
    try:
        results = st.session_state.service.files().list(
            q="name='AI_Image_Editor_Pro' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()
        
        files = results.get('files', [])
        if files:
            st.session_state.gdrive_folder_id = files[0]['id']
            return files[0]['id']
        
        file_metadata = {
            'name': 'AI_Image_Editor_Pro',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = st.session_state.service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        folder_id = folder.get('id')
        st.session_state.gdrive_folder_id = folder_id
        return folder_id
    except Exception as e:
        st.error(f"Error creating folder: {str(e)}")
        return None

def upload_to_gdrive(image_url: str, file_name: str, task_id: str = None):
    """Download image from URL and upload to Google Drive with public access."""
    if not st.session_state.service:
        return None
    
    try:
        folder_id = st.session_state.gdrive_folder_id or create_app_folder()
        if not folder_id:
            return None
        
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image_data = response.content
        
        mime_type = 'image/png'
        if file_name.lower().endswith('.jpg') or file_name.lower().endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif file_name.lower().endswith('.webp'):
            mime_type = 'image/webp'
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id],
            'description': f'Task ID: {task_id or "N/A"} | Original URL: {image_url}'
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(image_data),
            mimetype=mime_type,
            resumable=True
        )
        
        file = st.session_state.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, webContentLink, mimeType, size, createdTime'
        ).execute()
        
        file_id = file.get('id')
        
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        st.session_state.service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()
        
        # Added more URL formats and folder tracking metadata for uploaded file
        uploaded_info = {
            'file_id': file_id,
            'file_name': file.get('name'),
            'drive_web_link': file.get('webViewLink'),
            'drive_content_link': file.get('webContentLink'),
            'drive_public_url': f"https://drive.google.com/uc?export=view&id={file_id}",
            'drive_thumbnail_url': f"https://drive.google.com/thumbnail?id={file_id}&sz=w400",
            'drive_direct_link': f"https://lh3.googleusercontent.com/d/{file_id}",
            'original_generation_url': image_url,
            'mime_type': file.get('mimeType'),
            'file_size': file.get('size'),
            'uploaded_at': datetime.now().isoformat(),
            'created_time': file.get('createdTime'),
            'task_id': task_id,
            'id': file_id,
            'name': file.get('name'),
            'public_image_url': f"https://drive.google.com/uc?export=view&id={file_id}",
            'thumbnail_url': f"https://drive.google.com/thumbnail?id={file_id}&sz=w400",
            'original_url': image_url,
            'webViewLink': file.get('webViewLink'),
            'mimeType': file.get('mimeType'),
            'createdTime': file.get('createdTime'),
            'size': file.get('size'),
            'folder_id': st.session_state.gdrive_folder_id,
            'folder_name': get_folder_name_from_id(st.session_state.gdrive_folder_id)
        }
        
        st.session_state.stats['uploaded_images'] += 1
        return uploaded_info
        
    except Exception as e:
        st.error(f"Error uploading to Google Drive: {str(e)}")
        return None

def list_gdrive_images(folder_id: Optional[str] = None, fetch_all: bool = True):
    """
    List all images in Google Drive folder with pagination support.
    
    Args:
        folder_id: The folder ID to fetch from. If None, uses default app folder.
        fetch_all: If True, fetches all images using pagination. If False, limits to 200.
    """
    if not st.session_state.service:
        return []
    
    try:
        if not folder_id:
            folder_id = st.session_state.gdrive_folder_id or create_app_folder()
        
        all_files = []
        page_token = None
        page_count = 0
        
        while True:
            page_count += 1
            print(f"[v0] Fetching page {page_count} of images from Drive...")
            
            query_params = {
                'q': f"'{folder_id}' in parents and trashed=false and (mimeType contains 'image')",
                'spaces': 'drive',
                'fields': 'nextPageToken, files(id, name, webContentLink, webViewLink, createdTime, size, mimeType, thumbnailLink, description)',
                'pageSize': 1000,  # Max allowed by API
                'orderBy': 'createdTime desc'
            }
            
            if page_token:
                query_params['pageToken'] = page_token
            
            results = st.session_state.service.files().list(**query_params).execute()
            
            files = results.get('files', [])
            all_files.extend(files)
            
            print(f"[v0] Page {page_count}: Found {len(files)} images (Total so far: {len(all_files)})")
            
            page_token = results.get('nextPageToken')
            
            if not page_token or not fetch_all:
                break
        
        print(f"[v0] Completed fetching {len(all_files)} total images from {page_count} page(s)")
        
        processed_files = []
        for file in all_files:
            file_id = file['id']
            
            original_url = None
            description = file.get('description', '')
            if 'Original URL:' in description:
                try:
                    original_url = description.split('Original URL:')[1].strip().split(' |')[0]
                except Exception:
                    pass
            
            # Populate full set of URL formats and folder metadata
            file['drive_web_link'] = file.get('webViewLink')
            file['drive_content_link'] = file.get('webContentLink')
            file['drive_public_url'] = f"https://drive.google.com/uc?export=view&id={file_id}"
            file['drive_thumbnail_url'] = f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"
            file['drive_direct_link'] = f"https://lh3.googleusercontent.com/d/{file_id}"
            file['original_generation_url'] = original_url
            file['public_image_url'] = file['drive_public_url']
            file['thumbnail_url'] = file['drive_thumbnail_url']
            file['original_url'] = original_url
            file['direct_link'] = file['drive_direct_link']
            file['createdTime'] = file.get('createdTime', datetime.now().isoformat())
            file['size'] = file.get('size', 0)
            file['folder_id'] = folder_id
            file['folder_name'] = get_folder_name_from_id(folder_id)
            
            processed_files.append(file)
        
        return processed_files
        
    except Exception as e:
        st.error(f"Error listing images: {str(e)}")
        print(f"[v0] Error in list_gdrive_images: {str(e)}")
        return []

def delete_gdrive_file(file_id: str):
    """Delete a file from Google Drive."""
    if not st.session_state.service:
        return False
    
    try:
        st.session_state.service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting file: {str(e)}")
        return False

# ============================================================================
# API Functions - All Generation Models
# ============================================================================
def create_task(api_key, model, input_params, callback_url=None):
    """Create a generation task."""
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
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/createTask", # Changed from BASE_URL
            headers=headers,
            json=payload,
            timeout=30
        )
        
        data = response.json()
        if response.status_code == 200:
            if data.get("code") == 200:
                st.session_state.stats['total_tasks'] += 1
                return {"success": True, "task_id": data["data"]["taskId"]}
            else:
                return {"success": False, "error": data.get('msg', 'Unknown API error')}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Network error: {str(e)}"}
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON response from API"}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

def check_task_status(api_key, task_id):
    """Check task status."""
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/recordInfo", # Changed from BASE_URL
            headers=headers,
            params={"taskId": task_id},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                return {"success": True, "data": data["data"]}
            else:
                return {"success": False, "error": data.get('msg', 'Unknown API error')}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Network error: {str(e)}"}
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON response from API"}
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
            state = task_data["state"]
            
            progress_val = min((attempt + 1) / max_attempts, 0.95)
            progress_bar.progress(progress_val)
            status_text.text(f"Status: {state.upper()} | Attempt {attempt + 1}/{max_attempts}")
            
            if state == "success":
                progress_bar.progress(1.0)
                status_text.text("Task completed successfully!")
                return {"success": True, "data": task_data}
            elif state == "fail":
                progress_bar.empty()
                status_text.text("Task failed")
                return {"success": False, "error": task_data.get('failMsg', 'Unknown failure reason'), "data": task_data}
            
            time.sleep(delay)
        else:
            status_text.text(f"Error checking status: {result.get('error', 'Unknown error')}")
            time.sleep(delay)
    
    progress_bar.empty()
    status_text.text("Task timed out")
    return {"success": False, "error": "Task polling timeout"}

def save_and_upload_results(task_id, model, prompt, result_urls):
    """Save results to task history and auto-upload if enabled."""
    updated = False
    for i, task in enumerate(st.session_state.task_history):
        if task['id'] == task_id:
            st.session_state.task_history[i]['status'] = 'success'
            st.session_state.task_history[i]['results'] = result_urls
            st.session_state.stats['successful_tasks'] += 1
            st.session_state.stats['total_images'] += len(result_urls)
            updated = True
            
            if st.session_state.auto_upload and st.session_state.authenticated:
                for idx, result_url in enumerate(result_urls):
                    file_extension = result_url.split('.')[-1].split('?')[0]
                    if file_extension.lower() not in ['png', 'jpg', 'jpeg', 'webp']:
                        file_extension = 'png'
                    file_name = f"{model.replace('/', '_')}_{task_id}_{idx+1}.{file_extension}"
                    
                    # Check if image already exists in library to prevent duplicates
                    if not any(img.get('original_url') == result_url for img in st.session_state.library_images):
                        with st.spinner(f"Auto-uploading {file_name}..."):
                            upload_info = upload_to_gdrive(result_url, file_name, task_id)
                            if upload_info:
                                st.session_state.library_images.insert(0, upload_info)
                                st.toast(f"Auto-uploaded {file_name} to Google Drive!", icon="☁️")
                            else:
                                st.warning(f"Failed to auto-upload {file_name}")
            break
    
    if updated:
        st.success("Results saved to task history.")

# ============================================================================
# Image Display Helper Functions
# ============================================================================
def display_image_with_fallback(image_data, caption="", use_container_width=True, width=None, show_source=True):
    """
    Display image with intelligent fallback through multiple URL options.
    Priority: original_generation_url > drive_public_url > drive_direct_link > thumbnail
    """
    if not image_data:
        st.warning("No image data provided")
        return False
    
    urls_to_try = []
    
    if image_data.get('original_generation_url'):
        urls_to_try.append(('Original Quality', image_data['original_generation_url'], '#FF6B6B'))
    elif image_data.get('original_url'):
        urls_to_try.append(('Original', image_data['original_url'], '#FF6B6B'))
    elif image_data.get('url'):
        urls_to_try.append(('Drive URL', image_data['url'], '#4285F4'))
    
    if image_data.get('drive_public_url'):
        urls_to_try.append(('Drive Public', image_data['drive_public_url'], '#4285F4'))
    elif image_data.get('public_image_url'):
        urls_to_try.append(('Drive', image_data['public_image_url'], '#4285F4'))
    
    if image_data.get('drive_direct_link'):
        urls_to_try.append(('Drive CDN', image_data['drive_direct_link'], '#34A853'))
    elif image_data.get('direct_link'):
        urls_to_try.append(('Direct', image_data['direct_link'], '#34A853'))
    
    if image_data.get('drive_thumbnail_url'):
        urls_to_try.append(('Thumbnail', image_data['drive_thumbnail_url'], '#FBBC04'))
    elif image_data.get('thumbnail_url'):
        urls_to_try.append(('Thumb', image_data['thumbnail_url'], '#FBBC04'))
    
    if not urls_to_try:
        st.error("No valid image URLs found in the provided data.")
        print(f"[v0] No URLs found in image_data: {list(image_data.keys())}")
        return False
    
    displayed = False
    used_source_info = None
    
    for source_label, url, badge_color in urls_to_try:
        try:
            print(f"[v0] Trying {source_label}: {url[:100]}")
            if width:
                st.image(url, caption=caption, width=width)
            else:
                st.image(url, caption=caption, use_container_width=use_container_width)
            
            displayed = True
            used_source_info = (source_label, badge_color)
            print(f"[v0] Successfully displayed from {source_label}")
            break
            
        except Exception as e:
            print(f"[v0] Failed {source_label}: {str(e)[:100]}")
            continue
    
    if displayed and show_source and used_source_info:
        source_label, badge_color = used_source_info
        st.markdown(
            f"<div style='margin-top:-10px;margin-bottom:10px;'>"
            f"<span style='background:{badge_color};color:white;padding:4px 8px;border-radius:4px;font-size:11px;font-weight:600;'>"
            f"{source_label}</span></div>",
            unsafe_allow_html=True
        )
        return True
    
    if not displayed:
        print("[v0] All URLs failed, showing placeholder")
        st.markdown(
            f"<div style='padding:40px;background:#f8f9fa;border:2px dashed #dee2e6;border-radius:12px;text-align:center;color:#6c757d;'>"
            f"<div style='font-size:48px;margin-bottom:10px;'>🖼️</div>"
            f"<div style='font-size:16px;font-weight:600;margin-bottom:5px;'>Image Preview Unavailable</div>"
            f"<div style='font-size:12px;margin-bottom:5px;'>'{image_data.get('name', 'Unknown')}'</div>"
            f"<div style='font-size:11px;color:#adb5bd;'>Tried {len(urls_to_try)} source(s)</div>"
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
                display_image_with_fallback(image_data, caption=file_name, show_source=True)
                
                if show_metadata:
                    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                    
                    metadata_badges = []
                    
                    if image_data.get('original_generation_url') or image_data.get('original_url'):
                        metadata_badges.append("<span style='background:#FF6B6B;color:white;padding:3px 6px;border-radius:4px;font-size:10px;margin-right:4px;'>Original</span>")
                    
                    if image_data.get('drive_public_url') or image_data.get('public_image_url'):
                        metadata_badges.append("<span style='background:#4285F4;color:white;padding:3px 6px;border-radius:4px;font-size:10px;margin-right:4px;'>Drive</span>")
                    
                    if image_data.get('createdTime'):
                        try:
                            created_dt_str = image_data['createdTime']
                            if created_dt_str.endswith('Z'):
                                created_dt_str = created_dt_str[:-1] + '+00:00'
                            created_date = datetime.fromisoformat(created_dt_str)
                            date_str = created_date.strftime('%m/%d %H:%M')
                            metadata_badges.append(f"<span style='background:#6c757d;color:white;padding:3px 6px;border-radius:4px;font-size:10px;margin-right:4px;'>{date_str}</span>")
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
                            metadata_badges.append(f"<span style='background:#6c757d;color:white;padding:3px 6px;border-radius:4px;font-size:10px;margin-right:4px;'>{size_str}</span>")
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
                        if image_data.get('url'):
                            st.code(f"Primary URL:\n{image_data['url']}", language="text")
                        if image_data.get('drive_public_url'):
                            st.code(f"Drive Public:\n{image_data['drive_public_url']}", language="text")
                        if image_data.get('drive_direct_link'):
                            st.code(f"Drive Direct:\n{image_data['drive_direct_link']}", language="text")
                        if image_data.get('drive_thumbnail_url'):
                            st.code(f"Thumbnail:\n{image_data['drive_thumbnail_url']}", language="text")
                
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
    st.session_state.saved_folders[folder_name] = folder_url
    st.success(f"Saved folder: {folder_name}")

def delete_folder_config(folder_name: str):
    """Delete a folder configuration."""
    if folder_name in st.session_state.saved_folders:
        del st.session_state.saved_folders[folder_name]
        st.success(f"Deleted folder: {folder_name}")

def rename_folder_config(old_name: str, new_name: str):
    """Rename a folder configuration."""
    if old_name in st.session_state.saved_folders:
        folder_url = st.session_state.saved_folders[old_name]
        del st.session_state.saved_folders[old_name]
        st.session_state.saved_folders[new_name] = folder_url
        st.success(f"Renamed folder: {old_name} → {new_name}")

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
    
    if not st.session_state.saved_folders:
        st.info("No saved folders. Add one above to get started!")
        return
    
    for idx, (folder_name, folder_url) in enumerate(st.session_state.saved_folders.items()):
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
                            gdrive_imgs = get_public_drive_images(folder_id, folder_name) # Pass folder_name
                            st.session_state.images = gdrive_imgs
                            st.session_state.current_index = 0
                            st.session_state.default_folder_url = folder_url
                            st.session_state.show_folder_manager = False
                            if gdrive_imgs:
                                st.balloons()
                                st.success(f"Loaded {len(gdrive_imgs)} images!")
                                st.rerun()
                            else:
                                st.error("No images found.")
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
    
    # API Configuration
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
    
    if not st.session_state.authenticated:
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
            if st.button("Refresh", use_container_width=True):
                with st.spinner("Refreshing library..."):
                    st.session_state.library_images = list_gdrive_images()
                st.success("Library refreshed!")
        
        if st.button("Disconnect", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.service = None
            st.session_state.credentials = None
            st.session_state.service_account_info = None
            st.session_state.gdrive_folder_id = None
            st.rerun()
    
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
# Main Application Pages
# ============================================================================

# Renamed from display_slideshow_page to render_slideshow_page for consistency
def render_slideshow_page():
    """Render the main slideshow interface."""
    # st.title("Google Drive Image Slideshow with AI Generation") # Removed, replaced by main-header
    
    st.markdown("## Select or Manage Folders")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Quick folder selector
        folder_options = list(st.session_state.saved_folders.keys())
        if folder_options:
            selected_folder = st.selectbox(
                "Quick Select Folder",
                options=folder_options,
                help="Select from your saved folders"
            )
            selected_folder_url = st.session_state.saved_folders[selected_folder]
        else:
            selected_folder_url = DEFAULT_FOLDER_URL
    
    with col2:
        # Custom URL input
        custom_folder_url = st.text_input(
            "Or Enter Custom URL",
            value=selected_folder_url if 'selected_folder' in locals() else DEFAULT_FOLDER_URL,
            placeholder="Paste your public folder link here...",
            help="Folder must have 'Anyone with the link can view' permission"
        )
    
    with col3:
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        if st.button("Manage Folders", use_container_width=True):
            st.session_state.show_folder_manager = not st.session_state.show_folder_manager
            st.rerun()
    
    if st.session_state.show_folder_manager:
        render_folder_manager()
        st.divider()
    
    # Load button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Load Images")
    with col2:
        if st.button("Load Gallery", type="primary", use_container_width=True):
            with st.spinner("Loading images..."):
                try:
                    folder_id = extract_folder_id(custom_folder_url)
                    gdrive_imgs = get_public_drive_images(folder_id, custom_folder_url) # Pass folder name if available
                    st.session_state.images = gdrive_imgs
                    st.session_state.current_index = 0
                    st.session_state.default_folder_url = custom_folder_url
                    if gdrive_imgs:
                        st.balloons()
                        st.success(f"Loaded {len(gdrive_imgs)} images!")
                    else:
                        st.error("No images found. Check folder permissions.")
                except Exception as e:
                    st.error(f"Error loading Google Drive: {str(e)}")
    
    if not st.session_state.images:
        st.info("Select a folder and click 'Load Gallery' to start viewing images")
        
        # Show preview of saved folders
        if st.session_state.saved_folders:
            st.markdown("### Your Saved Folders")
            for folder_name, folder_url in list(st.session_state.saved_folders.items())[:3]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{folder_name}**")
                    st.caption(folder_url[:60] + "..." if len(folder_url) > 60 else folder_url)
                with col2:
                    if st.button("Load", key=f"quick_load_{folder_name}", use_container_width=True):
                        with st.spinner("Loading..."):
                            try:
                                folder_id = extract_folder_id(folder_url)
                                gdrive_imgs = get_public_drive_images(folder_id, folder_name) # Pass folder_name
                                st.session_state.images = gdrive_imgs
                                st.session_state.current_index = 0
                                st.session_state.default_folder_url = folder_url
                                if gdrive_imgs:
                                    st.balloons()
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        return

    # Slideshow controls
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
        <div class="stat-box">
            <h2>{len(st.session_state.selected_slideshow_images)}</h2>
            <p>Selected</p>
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
    
    # Display current image
    st.markdown('<div class="image-frame">', unsafe_allow_html=True)
    display_image_with_fallback(current_item, caption="", show_source=False)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="image-caption">
        <span class="slide-counter">{idx + 1} / {total}</span>
        <span>{current_item.get("name", "Unknown")}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### Select for AI Generation")
    
    is_selected = any(img.get('file_id') == current_item.get('file_id') for img in st.session_state.selected_slideshow_images)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if is_selected:
            if st.button("Remove from Selection", type="secondary", use_container_width=True):
                st.session_state.selected_slideshow_images = [
                    img for img in st.session_state.selected_slideshow_images
                    if img.get('file_id') != current_item.get('file_id')
                ]
                st.rerun()
        else:
            if st.button("Add to Selection", type="primary", use_container_width=True):
                if len(st.session_state.selected_slideshow_images) < 10:
                    st.session_state.selected_slideshow_images.append(current_item)
                    st.success("Image added to selection!")
                    st.rerun()
                else:
                    st.warning("Maximum 10 images can be selected")
    
    with col2:
        if st.session_state.selected_slideshow_images:
            if st.button(f"Send {len(st.session_state.selected_slideshow_images)} to Generate", use_container_width=True):
                st.session_state.current_page = "Generate"
                st.rerun()
    
    with col3:
        if st.session_state.selected_slideshow_images:
            if st.button("Clear All", use_container_width=True):
                st.session_state.selected_slideshow_images = []
                st.rerun()
    
    # Display selected images
    if st.session_state.selected_slideshow_images:
        st.markdown("#### Selected Images")
        selected_cols = st.columns(min(5, len(st.session_state.selected_slideshow_images)))
        for i, sel_img in enumerate(st.session_state.selected_slideshow_images[:5]):
            with selected_cols[i]:
                display_image_with_fallback(sel_img, caption=f"Image {i+1}", show_source=False, width=100)
        if len(st.session_state.selected_slideshow_images) > 5:
            st.info(f"... and {len(st.session_state.selected_slideshow_images) - 5} more")
    
    # Slideshow controls
    st.markdown("### Slideshow Controls")
    col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 1.5])
    
    with col1:
        if st.button("First", use_container_width=True):
            st.session_state.current_index = 0
            st.rerun()
    
    with col2:
        if st.button("Prev", use_container_width=True):
            if idx == 0 and st.session_state.loop_mode:
                st.session_state.current_index = total - 1
            else:
                st.session_state.current_index = max(0, idx - 1)
            st.rerun()
    
    with col3:
        if st.button("Pause" if st.session_state.autoplay else "Play", use_container_width=True, type="primary"):
            st.session_state.autoplay = not st.session_state.autoplay
            st.rerun()
    
    with col4:
        if st.button("Next", use_container_width=True):
            if idx == total - 1 and st.session_state.loop_mode:
                st.session_state.current_index = 0
            else:
                st.session_state.current_index = min(total - 1, idx + 1)
            st.rerun()
    
    with col5:
        if st.button("Last", use_container_width=True):
            st.session_state.current_index = total - 1
            st.rerun()
    
    # Settings
    col1, col2, col3 = st.columns(3)
    
    with col1:
        slideshow_speed = st.slider(
            "Slide Duration (seconds)",
            min_value=1,
            max_value=15,
            value=st.session_state.slideshow_speed
        )
        st.session_state.slideshow_speed = slideshow_speed
    
    with col2:
        loop_mode = st.checkbox(
            "Loop Slideshow",
            value=st.session_state.loop_mode
        )
        st.session_state.loop_mode = loop_mode
    
    with col3:
        jump_to = st.selectbox(
            "Jump to slide:",
            range(1, total + 1),
            index=idx
        )
        if jump_to != idx + 1:
            st.session_state.current_index = jump_to - 1
            st.rerun()
    
    # Autoplay logic
    if st.session_state.autoplay:
        time.sleep(slideshow_speed)
        if idx == total - 1 and st.session_state.loop_mode:
            st.session_state.current_index = 0
        elif idx < total - 1:
            st.session_state.current_index = idx + 1
        else:
            st.session_state.autoplay = False
        st.rerun()


def display_generate_page():
    st.title("Generate New Image")
    
    if st.session_state.selected_image_for_edit and st.session_state.edit_mode:
        st.info(f"Image selected for editing ({st.session_state.edit_mode}): {st.session_state.selected_image_for_edit.get('name', 'Unknown')}")
        if st.button("Clear Image Selection for Edit"):
            st.session_state.selected_image_for_edit = None
            st.session_state.edit_mode = None
            st.rerun()
    
    if not st.session_state.api_key:
        st.error("Please configure your API Key in the sidebar to start generating images.")
        return

    if st.session_state.selected_slideshow_images:
        st.success(f"{len(st.session_state.selected_slideshow_images)} images selected from slideshow")
        with st.expander("View Selected Images"):
            cols = st.columns(min(5, len(st.session_state.selected_slideshow_images)))
            for i, img in enumerate(st.session_state.selected_slideshow_images[:5]):
                with cols[i]:
                    display_image_with_fallback(img, caption=f"Image {i+1}", show_source=False, width=150)

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
                    
                    st.session_state.task_history.insert(0, {
                        "id": task_id,
                        "model": model,
                        "prompt": prompt,
                        "status": "waiting",
                        "created_at": datetime.now().isoformat(),
                        "results": []
                    })
                    st.session_state.current_task = task_id
                    st.rerun()
                else:
                    st.error(f"Failed to create task: {result.get('error', 'Unknown error')}")

    with tab2:
        st.header("Image Edit - Qwen Model")
        st.info("Edit images using the Qwen Image Edit model.")
        
        default_qwen_url = "https://file.aiquickdraw.com/custom-page/akr/section-images/1755603225969i6j87xnw.jpg"
        if st.session_state.selected_image_for_edit:
            default_qwen_url = st.session_state.selected_image_for_edit.get('public_image_url') or st.session_state.selected_image_for_edit.get('url', default_qwen_url)
        elif st.session_state.selected_slideshow_images:
            default_qwen_url = st.session_state.selected_slideshow_images[0].get('url', default_qwen_url)
            
        with st.form("qwen_image_edit_form"):
            prompt = st.text_area("Edit Prompt", "Make the image more vibrant and colorful, add a subtle glow")
            negative_prompt = st.text_area("Negative Prompt (Optional)", "blurry, ugly, low quality, distorted")
            
            use_library_image = False
            if st.session_state.authenticated and st.session_state.library_images:
                use_library_image = st.checkbox("Use image from library", value=bool(st.session_state.selected_image_for_edit))
            
            image_url_input = None
            if use_library_image:
                library_options = {img.get('name', f"Image {i}"): img for i, img in enumerate(st.session_state.library_images) if img.get('name')}
                
                if library_options:
                    selected_name = st.selectbox("Select Image", options=list(library_options.keys()))
                    selected_img_data = library_options[selected_name]
                    image_url_input = selected_img_data.get('public_image_url', '')
                    st.image(image_url_input, caption=selected_name, width=200)
                else:
                    st.warning("No images found in library.")
                    image_url_input = st.text_input("Image URL", default_qwen_url)
            else:
                image_url_input = st.text_input("Image URL", default_qwen_url)
            
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
                    st.error("Please provide an image URL or select an image from the library.")
                else:
                    input_params = {
                        "prompt": prompt,
                        "image_url": image_url_input,
                        "negative_prompt": negative_prompt,
                        "image_size": image_size,
                        "num_inference_steps": num_steps,
                        "guidance_scale": guidance_scale,
                        "enable_safety_checker": True,
                        "output_format": "png"
                    }
                    
                    with st.spinner("Creating edit task..."):
                        result = create_task(st.session_state.api_key, "qwen/image-edit", input_params)
                    
                    if result["success"]:
                        task_id = result["task_id"]
                        st.success(f"Task created successfully. Task ID: `{task_id}`")
                        
                        st.session_state.task_history.insert(0, {
                            "id": task_id,
                            "model": "qwen/image-edit",
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
                        st.error(f"Failed to create task: {result.get('error', 'Unknown error')}")

    with tab3:
        st.header("Image Edit - Seedream V4 Model")
        st.info("Advanced image editing using Seedream V4.")
        
        default_seedream_url = "https://file.aiquickdraw.com/custom-page/akr/section-images/1757930552966e7f2on7s.png"
        if st.session_state.selected_image_for_edit:
            default_seedream_url = st.session_state.selected_image_for_edit.get('public_image_url') or st.session_state.selected_image_for_edit.get('url', default_seedream_url)
        elif st.session_state.selected_slideshow_images:
            default_seedream_url = st.session_state.selected_slideshow_images[0].get('url', default_seedream_url)
            
        with st.form("seedream_image_edit_form"):
            prompt = st.text_area("Edit Prompt", "Create a tshirt mock up with this logo on a plain white background")
            
            use_library_image = False
            if st.session_state.authenticated and st.session_state.library_images:
                use_library_image = st.checkbox("Use image from library", value=bool(st.session_state.selected_image_for_edit), key="seedream_use_lib")
            
            image_url_input = None
            if use_library_image:
                library_options = {img.get('name', f"Image {i}"): img for i, img in enumerate(st.session_state.library_images) if img.get('name')}
                
                if library_options:
                    selected_name = st.selectbox("Select Image", options=list(library_options.keys()), key="seedream_select")
                    selected_img_data = library_options[selected_name]
                    image_url_input = selected_img_data.get('public_image_url', '')
                    st.image(image_url_input, caption=selected_name, width=200)
                else:
                    st.warning("No images found in library.")
                    image_url_input = st.text_input("Image URL", default_seedream_url, key="seedream_url")
            else:
                image_url_input = st.text_input("Image URL", default_seedream_url, key="seedream_url")
            
            col1, col2 = st.columns(2)
            with col1:
                image_size = st.selectbox("Image Size", ["square", "square_hd", "portrait_4_3", "landscape_4_3"], index=1, key="seedream_size")
            with col2:
                image_resolution = st.selectbox("Image Resolution", ["1K", "2K", "4K"], index=0, key="seedream_res")
            
            submitted = st.form_submit_button("Edit Image (Seedream)")
            
            if submitted:
                if not image_url_input:
                    st.error("Please provide an image URL or select an image from the library.")
                else:
                    input_params = {
                        "prompt": prompt,
                        "image_url": image_url_input,
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
                        st.error(f"Failed to create task: {result.get('error', 'Unknown error')}")

def display_history_page():
    st.title("Task History")
    
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
            if st.button("Check Status", key=f"check_{task_id}"):
                st.session_state.polling_active = True
                st.session_state.current_task = task_id
                st.rerun()
            
            if st.session_state.polling_active and st.session_state.current_task == task_id:
                st.info("Polling for task status...")
                
                result = poll_task_until_complete(st.session_state.api_key, task_id)
                
                st.session_state.polling_active = False
                st.session_state.current_task = None
                
                if result["success"]:
                    try:
                        result_json_str = result['data'].get('resultJson', '{}')
                        result_data = json.loads(result_json_str)
                        result_urls = result_data.get('resultUrls', [])
                        
                        save_and_upload_results(task_id, task['model'], task['prompt'], result_urls)
                        
                        st.success("Task completed and results updated!")
                        st.rerun()
                    except json.JSONDecodeError:
                        st.error("Failed to parse task results from API.")
                        st.session_state.task_history[i]['status'] = 'fail'
                        st.session_state.stats['failed_tasks'] += 1
                        st.rerun()
                else:
                    fail_msg = result.get('error', 'Unknown error')
                    st.session_state.task_history[i]['status'] = 'fail'
                    st.session_state.task_history[i]['error'] = fail_msg
                    st.session_state.stats['failed_tasks'] += 1
                    st.error(f"Task failed: {fail_msg}")
                    st.rerun()
        
        elif status == 'success':
            st.markdown("#### Results")
            if task['results']:
                result_grid_cols = 3
                
                for res_idx, result_url in enumerate(task['results']):
                    if res_idx % result_grid_cols == 0:
                        cols = st.columns(result_grid_cols)
                    
                    with cols[res_idx % result_grid_cols]:
                        img_data_for_display = {
                            'original_generation_url': result_url,
                            'name': f"Result {res_idx+1} ({task['model']})",
                            'task_id': task_id,
                            'url': result_url
                        }
                        
                        display_image_with_fallback(img_data_for_display, caption=f"Result {res_idx+1}", show_source=False)
                        
                        try:
                            img_response = requests.get(result_url, timeout=15)
                            img_response.raise_for_status()
                            
                            file_extension = result_url.split('.')[-1].split('?')[0]
                            if file_extension.lower() not in ['png', 'jpg', 'jpeg', 'webp']:
                                file_extension = 'png'
                                
                            st.download_button(
                                label="Download",
                                data=img_response.content,
                                file_name=f"{task['model'].replace('/', '_')}_{task_id}_{res_idx+1}.{file_extension}",
                                mime=f"image/{file_extension}",
                                key=f"download_{task_id}_{res_idx}",
                                use_container_width=True
                            )
                        except Exception:
                            st.warning("Download unavailable")
                            
                        if st.session_state.authenticated:
                            is_uploaded = any(
                                lib_img.get('original_url') == result_url
                                for lib_img in st.session_state.library_images
                            )
                            
                            if not is_uploaded:
                                if st.button("Upload to Drive", key=f"upload_{task_id}_{res_idx}", use_container_width=True):
                                    file_extension = result_url.split('.')[-1].split('?')[0]
                                    if file_extension.lower() not in ['png', 'jpg', 'jpeg', 'webp']:
                                        file_extension = 'png'
                                    file_name = f"{task['model'].replace('/', '_')}_{task_id}_{res_idx+1}.{file_extension}"
                                    
                                    with st.spinner(f"Uploading '{file_name}'..."):
                                        upload_info = upload_to_gdrive(result_url, file_name, task_id)
                                        if upload_info:
                                            st.session_state.library_images.insert(0, upload_info)
                                            st.success(f"Uploaded '{file_name}' to Drive!")
                                            st.rerun()
                                        else:
                                            st.error("Upload failed.")
                            else:
                                st.success("Already in Drive")
            else:
                st.info("No results found for this task.")
        
        elif status == 'fail':
            st.error(f"Failure reason: `{task.get('error', 'Unknown error')}`")
            
        st.markdown("</div>", unsafe_allow_html=True)

def load_complete_library():
    """Load all images from both authenticated Drive storage and public folders."""
    all_library_images = []
    
    # Part 1: Get images from authenticated Google Drive (uploaded generations)
    if st.session_state.service and st.session_state.gdrive_folder_id:
        with st.spinner("📥 Loading images from your Google Drive storage..."):
            drive_images = list_gdrive_images(fetch_all=True)
            if drive_images:
                all_library_images.extend(drive_images)
                st.success(f"✓ Loaded {len(drive_images)} images from your Drive storage")
    
    # Part 2: Get images from all saved public folders
    with st.spinner("📂 Loading images from saved public folders..."):
        public_folder_images = list_all_drive_folders_images()
        if public_folder_images:
            all_library_images.extend(public_folder_images)
            st.success(f"✓ Loaded {len(public_folder_images)} images from {len(st.session_state.saved_folders)} public folder(s)")
    
    # Remove duplicates based on file_id or url
    seen_ids = set()
    unique_images = []
    for img in all_library_images:
        img_id = img.get('file_id') or img.get('id') or img.get('url')
        if img_id and img_id not in seen_ids:
            seen_ids.add(img_id)
            unique_images.append(img)
    
    print(f"[v0] Total unique images in library: {len(unique_images)}")
    return unique_images

def list_all_drive_folders_images():
    """Fetch images from all saved folders (public folders via scraping)."""
    all_images = []
    
    print(f"[v0] Fetching images from {len(st.session_state.saved_folders)} saved folders...")
    
    for folder_name, folder_url in st.session_state.saved_folders.items():
        try:
            folder_id = extract_folder_id(folder_url)
            print(f"[v0] Loading images from '{folder_name}' (ID: {folder_id})")
            
            # Get images from public folder
            folder_images = get_gdrive_image_urls(folder_id, folder_name)
            
            if folder_images:
                print(f"[v0] Found {len(folder_images)} images in '{folder_name}'")
                all_images.extend(folder_images)
            else:
                print(f"[v0] No images found in '{folder_name}'")
                
        except Exception as e:
            print(f"[v0] Error loading folder '{folder_name}': {str(e)}")
            st.warning(f"Could not load images from '{folder_name}': {str(e)}")
    
    print(f"[v0] Total images loaded from all folders: {len(all_images)}")
    return all_images

def display_library_page():
    st.title("📚 Complete Image Library")
    
    # Header with stats and controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        total_images = len(st.session_state.library_images)
        st.markdown(f"### {total_images:,} images total")
    with col2:
        view_mode = st.selectbox("View", ["By Folder", "All Images", "Grid"], key="library_view_mode")
    with col3:
        sort_by = st.selectbox("Sort", ["Newest First", "Oldest First", "Name A-Z", "Size"], key="library_sort")
    with col4:
        if st.button("🔄 Refresh All", use_container_width=True):
            with st.spinner("Refreshing complete library..."):
                st.session_state.library_images = load_complete_library()
            st.success(f"Library refreshed! {len(st.session_state.library_images):,} images loaded")
            st.rerun()
    
    if not st.session_state.library_images:
        with st.spinner("Loading complete library..."):
            st.session_state.library_images = load_complete_library()
        if st.session_state.library_images:
            st.success(f"Loaded {len(st.session_state.library_images):,} images!")
            st.rerun()
    
    if not st.session_state.library_images:
        st.info("📭 Your library is empty. Add images by:\n- Loading from saved public folders\n- Generating and uploading new images\n- Connecting Google Drive to access uploaded images")
        return
    
    sorted_images = st.session_state.library_images.copy()
    if sort_by == "Newest First":
        sorted_images.sort(key=lambda x: x.get('createdTime', ''), reverse=True)
    elif sort_by == "Oldest First":
        sorted_images.sort(key=lambda x: x.get('createdTime', ''))
    elif sort_by == "Name A-Z":
        sorted_images.sort(key=lambda x: x.get('name', ''))
    elif sort_by == "Size":
        sorted_images.sort(key=lambda x: int(x.get('size', 0)), reverse=True)
    
    # Search and filter section
    st.markdown("---")
    search_col, filter_col = st.columns([3, 1])
    with search_col:
        search_query = st.text_input("🔍 Search images by name", value="", key="lib_search")
    with filter_col:
        source_filter = st.selectbox("Filter by source", ["All", "Drive Storage", "Public Folders"], key="lib_filter")
    
    filtered_images = sorted_images
    if search_query:
        filtered_images = [img for img in filtered_images if search_query.lower() in img.get('name', '').lower()]
    
    if source_filter == "Drive Storage":
        filtered_images = [img for img in filtered_images if img.get('folder_id') == st.session_state.gdrive_folder_id]
    elif source_filter == "Public Folders":
        filtered_images = [img for img in filtered_images if img.get('folder_id') != st.session_state.gdrive_folder_id]
    
    st.markdown(f"**Showing {len(filtered_images):,} of {total_images:,} images**")
    
    # Display options
    st.markdown("---")
    
    if view_mode == "By Folder":
        folders_dict = organize_images_by_folder(filtered_images)
        
        st.markdown(f"### 📂 {len(folders_dict)} Folders")
        
        for folder_name, folder_images in folders_dict.items():
            folder_size = sum(int(img.get('size', 0)) for img in folder_images if img.get('size'))
            folder_size_mb = folder_size / (1024*1024) if folder_size > 0 else 0
            
            with st.expander(f"📁 **{folder_name}** ({len(folder_images)} images, {folder_size_mb:.1f} MB)", expanded=True):
                st.markdown(f"""
                    <div style='background:#e3f2fd;padding:12px;border-radius:8px;margin-bottom:16px;'>
                        <div style='font-size:13px;color:#1565c0;'>
                            <strong>Folder:</strong> {folder_name}<br>
                            <strong>Images:</strong> {len(folder_images)}<br>
                            <strong>Total Size:</strong> {folder_size_mb:.2f} MB<br>
                            <strong>Source:</strong> {'Google Drive Storage' if folder_images[0].get('folder_id') == st.session_state.gdrive_folder_id else 'Public Folder'}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                display_image_grid(folder_images, columns=3, show_metadata=True, show_actions=True)
    
    elif view_mode == "All Images":
        # List view with detailed URLs
        for idx, image_data in enumerate(filtered_images):
            with st.container():
                st.markdown(f"---")
                
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
                        size_mb = int(image_data['size']) / (1024*1024)
                        metadata_html += f"<span style='background:#17a2b8;color:white;padding:4px 8px;border-radius:4px;font-size:11px;margin-right:6px;'>💾 {size_mb:.2f} MB</span>"
                    
                    if image_data.get('createdTime'):
                        try:
                            created_dt_str = image_data['createdTime']
                            if created_dt_str.endswith('Z'):
                                created_dt_str = created_dt_str[:-1] + '+00:00'
                            created_date = datetime.fromisoformat(created_dt_str)
                            date_str = created_date.strftime('%Y-%m-%d %H:%M')
                            metadata_html += f"<span style='background:#28a745;color:white;padding:4px 8px;border-radius:4px;font-size:11px;margin-right:6px;'>📅 {date_str}</span>"
                        except:
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
                        download_url = image_data.get('drive_direct_link') or image_data.get('url')
                        if download_url:
                            st.markdown(f"[⬇️ Download]({download_url})", unsafe_allow_html=True)
    
    else:  # Grid view
        display_image_grid(filtered_images, columns=4, show_metadata=True, show_actions=True)
    
    st.markdown("---")
    st.markdown("### 📊 Library Statistics")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("Total Images", f"{len(filtered_images):,}")
    with stat_col2:
        folders_count = len(organize_images_by_folder(filtered_images))
        st.metric("Folders", folders_count)
    with stat_col3:
        total_size = sum(int(img.get('size', 0)) for img in filtered_images if img.get('size'))
        total_size_mb = total_size / (1024*1024) if total_size > 0 else 0
        st.metric("Total Size", f"{total_size_mb:.1f} MB")
    with stat_col4:
        avg_size = total_size_mb / len(filtered_images) if filtered_images else 0
        st.metric("Avg Size", f"{avg_size:.2f} MB")

# ============================================================================
# Main Page Router
# ============================================================================
# </CHANGE> Fixed duplicate lines causing syntax error
if st.session_state.current_page == "Slideshow":
    render_slideshow_page()
elif st.session_state.current_page == "Generate":
    display_generate_page()
elif st.session_state.current_page == "History":
    display_history_page()
elif st.session_state.current_page == "Library":
    display_library_page()
