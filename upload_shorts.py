import os
import sys
import time
import random
import subprocess
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# HD ও Ultra-Detailed প্রম্পট
JEWELRY_PROMPT = (
    "A 4k UHD photorealistic product shot of a luxury solitaire diamond ring with white gold band, "
    "centered on a clean pure white studio background, soft realistic reflection, studio softbox lighting, "
    "sharp focus on diamond facets, 8k render, professional jewelry photography, no hands, no person, no model"
)

def generate_video_with_ffmpeg():
    print("--- 1. Generating 4K HD Image via Pollinations AI ---")
    seed = random.randint(1, 99999)
    
    # Ultra HD 4K Resolution (2160x3840)
    img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(JEWELRY_PROMPT)}?width=2160&height=3840&nologo=true&seed={seed}&quality=100"
    
    try:
        response = requests.get(img_url, timeout=90)
        if response.status_code != 200:
            raise Exception(f"Image generation failed with status code: {response.status_code}")
        img_data = response.content
    except Exception as e:
        print(f"Error fetching image: {e}")
        sys.exit(1)

    image_filename = "ring_temp.jpg"
    video_filename = "final_shorts_temp.mp4"

    with open(image_filename, "wb") as f:
        f.write(img_data)

    print("--- 2. Converting Image to 4K Video using High-Bitrate FFmpeg ---")
    
    # 4K Rendering Command with High Bitrate (30M) and CRf 17 (Visually Lossless Quality)
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', image_filename,
        '-vf', "zoompan=z='min(zoom+0.0012,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=300:s=2160x3840",
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '17',
        '-b:v', '30M',
        '-t', '10',
        '-pix_fmt', 'yuv420p',
        '-r', '30',
        video_filename
    ]
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg Error: {result.stderr}")
        sys.exit(1)
        
    print("4K Ultra HD Video Created Successfully!")
    return image_filename, video_filename

def upload_to_youtube(video_filename):
    print("--- 3. Uploading 4K Short to YouTube ---")
    
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    
    if not all([refresh_token, client_id, client_secret]):
        print("Error: YouTube credentials (Secrets) are missing!")
        sys.exit(1)

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )

    youtube = build("youtube", "v3", credentials=creds)

    request_body = {
        "snippet": {
            "title": "4K 360° Luxury Diamond Solitaire Ring Showcase ✨ #shorts #jewelry",
            "description": "Experience the ultra-HD 4K view of this luxury solitaire diamond ring.\n\n#jewelry #diamondring #shorts #luxury #4k",
            "tags": ["jewelry", "shorts", "luxury", "gold", "diamond", "4k"],
            "categoryId": "26"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video_filename, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print(f"4K Video uploaded successfully! Video ID: {response.get('id')}\n")

if __name__ == "__main__":
    img_file, vid_file = generate_video_with_ffmpeg()
    
    try:
        upload_to_youtube(vid_file)
    finally:
        if os.path.exists(img_file):
            os.remove(img_file)
        if os.path.exists(vid_file):
            os.remove(vid_file)
