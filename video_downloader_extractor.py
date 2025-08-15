import os
import cv2
import requests
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"

# Function to print colored text
def colored_print(text, color=Colors.RESET, bold=False, underline=False):
    style = Colors.BOLD if bold else ""
    style += Colors.UNDERLINE if underline else ""
    print(f"{style}{color}{text}{Colors.RESET}")

# Configure requests session for better performance
def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=100))
    session.mount('https://', HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=100))
    return session

# Global session for downloads
download_session = create_session()

def display_banner():
    border = f"{Colors.CYAN}{'=' * 60}{Colors.RESET}"
    banner_lines = [
        f"{Colors.BLUE}🎥🎬 Welcome to Video Downloader & Frame Extractor! 🎬🎥{Colors.RESET}",
        border,
        "This tool allows you to download videos from links and extract frames ",
        "in your chosen orientation (portrait or landscape).",
        "Note: Use direct video URLs. For YouTube/etc., consider tools like yt-dlp.",
        border
    ]
    for line in banner_lines:
        if line == border:
            print(line)
        else:
            colored_print(line, Colors.MAGENTA)

def display_developer_info():
    border = f"{Colors.YELLOW}{'─' * 30}{Colors.RESET}"
    colored_print("🛠️ Developer Information:", Colors.GREEN, bold=True)
    print(border)
    colored_print("   Created by: Priyam Tiwari", Colors.CYAN)
    colored_print("   Version: 1.0.0 | License: MIT", Colors.CYAN)
    colored_print("   Email: priyam.kumari.tiwari@gmail.com", Colors.CYAN)
    print(border + "\n")

def download_video(url, save_path):
    """
    Optimized video download function with larger chunks and connection reuse.
    """
    try:
        CHUNK_SIZE = 8192  # Increased chunk size for better throughput
        
        with download_session.get(url, stream=True) as response:
            response.raise_for_status()
            total_length = int(response.headers.get('content-length', 0))
            
            with open(save_path, 'wb') as f:
                colored_print(f"🚀 Starting download: {url}", Colors.BLUE)
                if total_length == 0:
                    colored_print("⚠️ No content length available, downloading without progress bar.", Colors.YELLOW)
                    f.write(response.content)
                else:
                    with tqdm(total=total_length, unit='iB', unit_scale=True, 
                             desc="Downloading video", 
                             bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}{postfix}]") as pbar:
                        for data in response.iter_content(chunk_size=CHUNK_SIZE):
                            f.write(data)
                            pbar.update(len(data))
        colored_print(f"✅ Download complete: {save_path}", Colors.GREEN)
    except Exception as e:
        colored_print(f"❌ Error downloading {url}: {e}", Colors.RED)

def main_menu():
    while True:
        colored_print("\n📋 Main Menu:", Colors.MAGENTA, bold=True)
        colored_print("1. Download Videos", Colors.CYAN)
        colored_print("2. Extract Frames from Videos", Colors.CYAN)
        colored_print("Q. Quit", Colors.CYAN)
        choice = input(f"{Colors.YELLOW}Enter your choice (1/2/Q): {Colors.RESET}").strip().upper()
        
        if choice == '1':
            download_menu()
        elif choice == '2':
            extract_frames()
        elif choice == 'Q':
            colored_print("\n👋 Thank you for using the tool! Goodbye.", Colors.GREEN)
            break
        else:
            colored_print("❌ Invalid choice. Please try again.", Colors.RED)

def download_menu():
    colored_print("\n📥 Download Options:", Colors.MAGENTA, bold=True)
    colored_print("S. Single Link Download", Colors.CYAN)
    colored_print("F. Folder with TXT Files (each TXT contains links)", Colors.CYAN)
    colored_print("B. Back to Main Menu", Colors.CYAN)
    sub_choice = input(f"{Colors.YELLOW}Enter your choice (S/F/B): {Colors.RESET}").strip().upper()
    
    if sub_choice == 'S':
        link = input(f"{Colors.YELLOW}Enter the video link: {Colors.RESET}").strip()
        if not link:
            colored_print("❌ No link provided. Returning to menu.", Colors.RED)
            return
        video_path_folder = input(f"{Colors.YELLOW}Enter folder path to save the video: {Colors.RESET}").strip()
        os.makedirs(video_path_folder, exist_ok=True)
        
        # Determine filename
        filename = link.split('/')[-1].split('?')[0]
        if not filename:
            filename = 'downloaded_video.mp4'
        save_path = os.path.join(video_path_folder, filename)
        
        download_video(link, save_path)
    
    elif sub_choice == 'F':
        video_path_folder = input(f"{Colors.YELLOW}Enter path to folder with .txt files (each line in TXT is a link): {Colors.RESET}").strip()
        
        txt_files = [f for f in os.listdir(video_path_folder) if f.lower().endswith('.txt')]
        if not txt_files:
            colored_print("❌ No .txt files found in the folder.", Colors.RED)
            return
        
        colored_print(f"📁 Found {len(txt_files)} .txt files.", Colors.BLUE)
        for txt_file in txt_files:
            txt_path = os.path.join(video_path_folder, txt_file)
            with open(txt_path, 'r') as ff:
                links = [line.strip() for line in ff if line.strip()]
            
            if not links:
                colored_print(f"⚠️ No links found in {txt_file}. Skipping.", Colors.YELLOW)
                continue
            
            for idx, link in enumerate(links):
                # Determine unique filename
                base_name = os.path.splitext(txt_file)[0]
                url_filename = link.split('/')[-1].split('?')[0]
                ext = os.path.splitext(url_filename)[1] if url_filename else '.mp4'
                if url_filename:
                    filename = url_filename
                else:
                    filename = f"{base_name}_{idx+1}{ext}" if len(links) > 1 else f"{base_name}{ext}"
                
                # Check for existing file to avoid overwrite
                save_path = os.path.join(video_path_folder, filename)
                counter = 1
                while os.path.exists(save_path):
                    save_path = os.path.join(video_path_folder, f"{os.path.splitext(filename)[0]}_{counter}{ext}")
                    counter += 1
                
                download_video(link, save_path)
    
    elif sub_choice == 'B':
        return
    else:
        colored_print("❌ Invalid choice. Returning to menu.", Colors.RED)

def extract_frames():
    video_path_folder = input(f"\n{Colors.YELLOW}Enter path to folder containing videos: {Colors.RESET}").strip()
    if not os.path.exists(video_path_folder):
        colored_print("❌ Folder does not exist. Returning to menu.", Colors.RED)
        return
    
    orientation = input(f"{Colors.YELLOW}Enter desired orientation (portrait or landscape): {Colors.RESET}").strip().lower()
    if orientation not in ["portrait", "landscape"]:
        colored_print("❌ Invalid orientation. Returning to menu.", Colors.RED)
        return
    
    os.makedirs(video_path_folder, exist_ok=True)
    
    # Get list of videos
    video_list = sorted([
        f for f in os.listdir(video_path_folder)
        if os.path.isfile(os.path.join(video_path_folder, f)) and f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))
    ])
    
    if not video_list:
        colored_print("❌ No videos found in the folder. Returning to menu.", Colors.RED)
        return
    
    colored_print(f"📹 Found {len(video_list)} videos to process.", Colors.BLUE)
    
    # Configure OpenCV for better performance
    cv2.setNumThreads(4)  # Use multiple threads for processing
    
    for idx, video_file in enumerate(video_list, start=1):
        colored_print(f"\n[{idx}/{len(video_list)}] Starting with {video_file}", Colors.MAGENTA)
    
        video_path = os.path.join(video_path_folder, video_file)
        cap = cv2.VideoCapture(video_path)
        
        # Check if hardware acceleration is available
        if cv2.ocl.haveOpenCL():
            cv2.ocl.setUseOpenCL(True)
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Determine if resizing is needed
        need_resize = (orientation == "portrait" and width > height) or \
                     (orientation == "landscape" and height > width)
        
        if need_resize:
            target_width, target_height = height, width if orientation == "portrait" else width, height
        else:
            target_width, target_height = width, height
        
        # Create output directory
        video_name = os.path.splitext(video_file)[0]
        video_output_folder = os.path.join(video_path_folder, video_name)
        os.makedirs(video_output_folder, exist_ok=True)
        
        frame_idx = 0
        
        with tqdm(total=total_frames, desc=f"Extracting frames for {video_name}", 
                 unit="frame", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}{postfix}]") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if need_resize:
                    frame = cv2.resize(frame, (target_width, target_height))
                
                frame_path = os.path.join(video_output_folder, f"{video_name}_{frame_idx:05d}.jpg")
                # Using default JPEG quality (95)
                cv2.imwrite(frame_path, frame)
                frame_idx += 1
                pbar.update(1)
        
        cap.release()
        colored_print(f"✅ Completed {video_name} with {frame_idx} frames.", Colors.GREEN)
    
    colored_print("\n🎉 All videos processed successfully!", Colors.GREEN, bold=True)

if __name__ == "__main__":
    display_banner()
    display_developer_info()
    main_menu()