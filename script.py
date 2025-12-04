# 🍪 Cookie 匯出備忘錄 — yt-dlp 私密/年齡限制影片下載建議流程
#
# 1. 開啟瀏覽器的無痕／隱身視窗，**僅開啟一個分頁**，並登入你的 Google/YouTube 帳號。
# 2. 在同一個分頁中，前往 https://www.youtube.com/robots.txt
#    - 只開 robots.txt 可避免主頁影音自動刷新 cookie，增加 cookie 有效性。
#    - 更好的方式是直接前往你想下載的影片頁面，因為會自動請求該影片的特別權限cookie，以確保獲得足夠的存取權限。
# 3. 安裝並啟用 cookie 匯出擴充工具（推薦）：
#    - Chrome: 「Get cookies.txt LOCALLY」
#    - Firefox: 「cookies.txt」擴充套件
# 4. 使用擴充工具，將目前分頁（youtube.com）的 cookie 匯出，儲存為 cookies.txt
#    - 檔案必須為 Netscape HTTP Cookie File 格式，檔案開頭通常為：# Netscape HTTP Cookie File
# 5. 關閉該無痕視窗，確保 session 不會繼續被更新或覆寫。
# 6. 使用 yt-dlp 執行下載，指定 cookie 路徑：
#    yt-dlp --cookies "cookies.txt" "<影片網址>"
#
# 7. 注意事項：
#    - 匯出後請盡快使用，cookie 若過期需重新導出。
#    - 若仍無法下載，請確認：
#      a. 你用的是正確登入帳號
#      b. cookies.txt 為正確格式且有內容
#      c. yt-dlp 已升級到最新版 (py -m pip install -U yt-dlp)
#    - 亦可嘗試 --cookies-from-browser 功能自動讀取本地瀏覽器 cookie。
import os
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resolve_path(path_str):
    if not path_str:
        return ""
    if os.path.isabs(path_str):
        return path_str
    return os.path.join(BASE_DIR, path_str)

DOWNLOAD_DIR = resolve_path(os.getenv("DOWNLOAD_DIR", "Download_Folder"))
COOKIE_FILE = resolve_path(os.getenv("COOKIE_FILE", "www.youtube.com_cookies.txt"))
# -------------------

def get_video_info(url, auth_options=None):
    """Get video information including available formats"""
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': False,
    }

    # Apply authentication options if provided
    if auth_options:
        ydl_opts.update(auth_options)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        return info_dict

def list_quality_options(info_dict):
    """List available quality options for the user"""
    formats = info_dict.get('formats', [])
    title = info_dict.get('title', 'Unknown')

    print(f"\nVideo Title: {title}")
    print("-" * 50)
    
    # Group formats by quality
    video_formats = {}
    audio_formats = []
    
    for f in formats:
        # Skip formats without required info
        if not f.get('format_id'):
            continue
            
        # Check if it's a video format
        if f.get('vcodec') and f.get('vcodec') != 'none':
            height = f.get('height', 0)
            fps = f.get('fps', 0)
            vcodec = f.get('vcodec', 'unknown')
            
            # Create quality key
            quality_key = f"{height}p{fps if fps and fps != 30 else ''}"
            if quality_key not in video_formats:
                video_formats[quality_key] = []
            
            video_formats[quality_key].append({
                'format_id': f.get('format_id'),
                'ext': f.get('ext'),
                'vcodec': vcodec,
                'filesize': f.get('filesize', 0) or f.get('filesize_approx', 0),
                'has_audio': f.get('acodec') != 'none'
            })
        
        # Check if it's an audio-only format
        elif f.get('acodec') and f.get('acodec') != 'none' and (not f.get('vcodec') or f.get('vcodec') == 'none'):
            audio_formats.append({
                'format_id': f.get('format_id'),
                'ext': f.get('ext'),
                'acodec': f.get('acodec', 'unknown'),
                'abr': f.get('abr', 0),
                'filesize': f.get('filesize', 0) or f.get('filesize_approx', 0)
            })
    
    # Sort and display video formats
    print("\nAvailable video qualities:")
    all_sorted_qualities = sorted(video_formats.keys(), key=lambda x: int(x.split('p')[0]), reverse=True)
    
    # Filter for 1080p and above
    high_qualities = [q for q in all_sorted_qualities if int(q.split('p')[0]) >= 1080]
    
    # If high qualities exist, show them. Otherwise, show only the best available.
    qualities_to_display = high_qualities
    if not qualities_to_display and all_sorted_qualities:
        qualities_to_display = [all_sorted_qualities[0]]
        
    
    for idx, quality in enumerate(qualities_to_display, 1):
        formats_for_quality = video_formats[quality]
        best_format = max(formats_for_quality, key=lambda x: x['filesize'])
        audio_indicator = " (includes audio)" if best_format['has_audio'] else ""
        print(f"  - {quality} ({best_format['vcodec']}){audio_indicator}")
    
    # Display best audio format
    if audio_formats:
        best_audio = max(audio_formats, key=lambda x: x['abr'])
        print(f"\nBest audio: {best_audio['abr']}kbps ({best_audio['acodec']})")
    
    return all_sorted_qualities, video_formats

def download_video(url, quality_choice='best', auth_options=None):
    """Download video with specified quality"""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Set format selection based on quality choice
    if quality_choice == 'best':
        # This will select the best video and best audio, then merge them
        format_selection = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
    elif quality_choice == 'best_single':
        # This selects the best single file (video+audio combined)
        format_selection = 'best[ext=mp4]/best'
    elif quality_choice == '1080p':
        format_selection = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
    elif quality_choice == '720p':
        format_selection = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
    else:
        format_selection = quality_choice
    
    # Define the download options
    ydl_opts = {
        'format': format_selection,
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',  # Ensure output is MP4 after merging
        'noplaylist': True,
        
        # Bypass options
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        
        # Download settings
        'extractor_retries': 3,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'concurrent_fragment_downloads': 5,  # Speed up fragment downloads
        
        # User agent to appear more like a normal browser
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        
        # Network settings
        'socket_timeout': 30,
        'quiet': False,
        'progress': True,
        
        # Prefer ffmpeg for merging (better quality)
        'prefer_ffmpeg': True,
        
        # Keep original video and audio after merging (optional, set to False to save space)
        'keepvideo': False,
    }
    
    # Apply authentication options if provided
    if auth_options:
        ydl_opts.update(auth_options)
    
    print(f"\nDownloading with format selection: {format_selection}")
    print("This may take a moment as yt-dlp downloads the best video and audio streams separately and merges them...")
    
    # Use yt-dlp to download the video
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def select_and_download(url, info_dict, auth_options=None):
    """Download video with user-selected quality options"""
    try:
        # List available qualities
        sorted_qualities, video_formats = list_quality_options(info_dict)
        
        # --- Simplified Menu Generation ---
        menu_options = {
            0: ('best', "Best available quality (recommended, merges video+audio)"),
            1: ('1080p', "Best 1080p"),
            2: ('best_single', "Best single file (pre-merged, might be lower quality)"),
            3: ('custom', "Custom format string")
        }

        print("\n--- Select Quality ---")
        for key, (_, text) in menu_options.items():
            print(f"  {key}. {text}")

        choice_str = input(f"\nSelect an option (0-3, default=0): ").strip()
        choice = int(choice_str) if choice_str.isdigit() and int(choice_str) in menu_options else 0

        quality_choice, _ = menu_options[choice]
        
        if quality_choice == 'custom':
            print("\nEnter custom format string (e.g., '299+140' or 'bestvideo[height<=1080]+bestaudio'):")
            quality_choice = input("Format: ").strip() or 'best' # Fallback to best if empty
        else:
            print(f"Selected: {menu_options[choice][1]}")
        
        download_video(url, quality_choice, auth_options)
        return True
        
    except Exception as e:
        print(f"An error occurred during selection or download: {e}")
        return False

def download_with_fallback(url):
    """
    Attempt to download video, falling back to cookie authentication if initial attempt fails
    """
    auth_options = None
    info_dict = None

    # 1. First attempt: Try to get video info without any authentication.
    try:
        print("\nFetching video info (no authentication)...")
        info_dict = get_video_info(url, auth_options=None)
    except Exception as e:
        error_msg = str(e).lower()
        # 2. If getting info fails with an auth error, start the fallback process.
        if any(keyword in error_msg for keyword in ['age', 'restricted', 'sign in', 'login', 'private', 'unavailable']):
            print(f"\nInitial attempt failed: This video seems to require authentication.")
            print("--- Authentication Options ---")
            print("1. Use cookies.txt file (recommended for automation)")
            print("2. Use cookies from browser (most reliable, requires browser login)")
            auth_choice = input("Select an option (1-2, default=1): ").strip()

            if auth_choice == '2':
                browser = input("Enter browser (e.g., chrome, firefox, edge): ").strip().lower()
                profile = input("Enter profile (optional, e.g., 'Profile 1', press Enter for default): ").strip()
                if browser:
                    cookie_source = f"{browser}:{profile}" if profile else browser
                    auth_options = {'cookies_from_browser': (cookie_source,)}
                    print(f"\nRetrying with cookies from {cookie_source}...")
                else:
                    print("No browser specified. Falling back to cookies.txt.")
                    auth_options = {'cookiefile': COOKIE_FILE}
            else:
                auth_options = {'cookiefile': COOKIE_FILE}
                if not os.path.exists(COOKIE_FILE):
                    print(f"\nWarning: Cookie file not found at {COOKIE_FILE}")
                    print("Please ensure the file exists and is correctly placed.")
                    return False
                print(f"\nRetrying with cookies from {COOKIE_FILE}...")

            # 3. Second attempt: Retry getting info with authentication.
            try:
                info_dict = get_video_info(url, auth_options=auth_options)
            except Exception as cookie_error:
                print(f"\n✗ Authentication failed: {cookie_error}")
                print("Possible reasons:")
                print("- Cookies are expired, invalid, or do not have sufficient permissions.")
                print("- If using a browser, ensure you are logged into YouTube.")
                print("- The video may be region-locked or completely private.")
        else:
            print(f"\n✗ An unexpected error occurred: {e}")

    # 4. If we have the info_dict (from either the first or second attempt), proceed to selection and download.
    if info_dict:
        return select_and_download(url, info_dict, auth_options)
    else:
        return False

def main():
    print("YouTube Video Downloader - Best Quality Edition")
    print("=" * 50)
    print("This tool will automatically download the highest quality video and audio available.")
    
    while True:
        # Get URL from the user
        url = input("\nPlease paste the URL of the video you want to download (or type 'exit' to quit): ")
        
        if url.lower() == 'exit':
            print("Exiting the downloader. Goodbye!")
            break
        elif url:
            try:
                success = download_with_fallback(url)
                if success:
                    print("✓ Download completed successfully!")
                else:
                    print("✗ Download failed after trying all available methods.")
            except KeyboardInterrupt:
                print("\nDownload interrupted by user.")
            except Exception as e:
                print(f"✗ An unexpected error occurred: {e}")
        else:
            print("URL cannot be empty. Please try again.")

if __name__ == "__main__":
    main()