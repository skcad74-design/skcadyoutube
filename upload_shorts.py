import os
import sys
import time
import random
import subprocess
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 360-Degree CAD Rotation Video Prompts
PROMPTS = [
    (
        "A 360-degree seamless rotating turntable video of a luxury 18k yellow gold halo diamond signet ring, "
        "large center round diamond with surrounding pavé diamonds, pristine pure white studio background, "
        "realistic metallic reflections, raytraced lighting, 4k 60fps, smooth 3d cad product animation"
    ),
    (
        "A 360-degree turntable camera rotation around a luxury 18k yellow gold trilogy ring with cushion blue sapphire "
        "and triangle diamond side stones, isolated on solid white studio background, sharp focus, 8k render, professional jewelry animation"
    )
]

def generate_video_with_ffmpeg():
    print("--- 1. Generating High-Detail Base Frame ---")
    
    selected_prompt = random.choice(PROMPTS)
    seed = random.randint(1, 99999)
    
    # Ultra HD 4K Quality Base Rendering
    img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(selected_prompt)}?width=2160&height=3840&nologo=true&seed={seed}&model=flux"
    
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

    print("--- 2. Encoding 60FPS High-Bitrate Video ---")
    
    # 60FPS High-Quality Smooth Video Encoding
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', image_filename,
        '-vf', "zoompan=z='min(zoom+0.001,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=600:s=2160x3840",
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '15',
        '-b:v', '50M',
        '-t', '10',
        '-pix_fmt', 'yuv420p',
        '-r', '60',
        video_filename
    ]
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg Error: {result.stderr}")
        sys.exit(1)
        
    print("Ultra-HD 60FPS Video Created Successfully!")
    return image_filename, video_filename

def upload_to_youtube(video_filename):
    print("--- 3. Uploading Short to YouTube ---")
    
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
            "title": "360° Luxury 18k Gold Diamond Ring Showcase ✨ #shorts #jewelry",
            "description": "Experience the 360-degree Ultra-HD view of this luxury handcrafted gold diamond ring.\n\n#jewelry #goldring #shorts #luxury #4k #cad",
            "tags": ["jewelry", "shorts", "luxury", "gold", "ring", "4k", "cad"],
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

    print(f"Video uploaded successfully! Video ID: {response.get('id')}\n")

if __name__ == "__main__":
    img_file, vid_file = generate_video_with_ffmpeg()
    
    try:
        upload_to_youtube(vid_file)
    finally:
        if os.path.exists(img_file):
            os.remove(img_file)
        if os.path.exists(vid_file):
            os.remove(vid_file)
