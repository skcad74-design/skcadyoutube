import os
import sys
import time
import random
import subprocess
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# আপনার ছবির সাথে পুরোপুরি মানানসই সহজ ও নিখুঁত ৩টি প্রম্পট
PROMPTS = [
    # ১. Blue Sapphire with Triangles (আপনার ১ নং ছবি)
    (
        "3d cad render of a high polish 18k yellow gold ring, cushion blue sapphire center stone, "
        "two white triangle side diamonds, gold prongs, white background, studio light, jewelry photo"
    ),
    # ২. Leaf Pattern Stacking Band (আপনার ২ নং ছবি)
    (
        "3d cad render of a polished 18k yellow gold eternity ring with small gold leaves and sparkling round diamonds, "
        "nature floral design band, white background, realistic jewelry photo"
    ),
    # ৩. Gold Band with Small Diamond (আপনার ৩ নং ছবি)
    (
        "3d cad render of a simple smooth shiny 18k yellow gold wedding band, set with one tiny small diamond, "
        "minimalist luxury gold ring, white studio background, high quality jewelry photography"
    )
]

def generate_video_with_ffmpeg():
    print("--- 1. Generating Image via Pollinations AI ---")
    
    selected_prompt = random.choice(PROMPTS)
    seed = random.randint(1, 99999)
    
    # রেজোলিউশন ১০৮০x১৯২০ রাখা হয়েছে যাতে নিখুঁত ও স্পষ্ট রেন্ডার হয়
    img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(selected_prompt)}?width=1080&height=1920&nologo=true&seed={seed}&model=flux"
    
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

    print("--- 2. Converting Image to HD Video using FFmpeg ---")
    
    # FFmpeg zoom effect to create video
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', image_filename,
        '-vf', "zoompan=z='min(zoom+0.0015,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=300:s=1080x1920",
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-t', '10',
        '-pix_fmt', 'yuv420p',
        '-r', '30',
        video_filename
    ]
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg Error: {result.stderr}")
        sys.exit(1)
        
    print("Video Created Successfully!")
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
            "title": "Luxury 18k Gold Ring Design Showcase ✨ #shorts #jewelry",
            "description": "Explore this stunning 3D CAD rendered gold jewelry design.\n\n#jewelry #goldring #shorts #luxury #cad #engagementring",
            "tags": ["jewelry", "shorts", "luxury", "gold", "ring", "cad"],
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
