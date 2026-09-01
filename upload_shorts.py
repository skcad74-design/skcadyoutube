import os
import time
import subprocess
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

JEWELRY_PROMPT = (
    "Create a premium photorealistic 3D jewelry product shot of a luxurious solitaire diamond ring "
    "made of highly polished white gold/platinum with a round brilliant-cut center diamond surrounded by a delicate halo of small diamonds. "
    "Positioned upright and centered on a clean pure white studio background with soft realistic shadows. "
    "Ultra-realistic jewelry CGI, luxury jewelry advertisement, 4K quality, sharp focus, isolated centered view."
)

def generate_video_with_ffmpeg():
    print("--- 1. Generating Free Image via Pollinations AI ---")
    img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(JEWELRY_PROMPT)}?width=1080&height=1920&nologo=true"
    
    img_data = requests.get(img_url, timeout=40).content
    image_filename = "ring_temp.jpg"
    video_filename = "final_shorts_temp.mp4"

    with open(image_filename, "wb") as f:
        f.write(img_data)

    print("--- 2. Converting Image to Cinematic Video using FFmpeg (No API Needed) ---")
    
    # FFmpeg Command: 10 seconds slow zoom-in effect (Ken Burns Style)
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', image_filename,
        '-vf', "zoompan=z='min(zoom+0.0015,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=300:s=1080x1920",
        '-c:v', 'libx264',
        '-t', '10',
        '-pix_fmt', 'yuv420p',
        '-r', '30',
        video_filename
    ]
    
    subprocess.run(ffmpeg_cmd, check=True)
    print("Video Created Successfully with FFmpeg!")
    
    return image_filename, video_filename

def upload_to_youtube(video_filename):
    print("--- 3. Uploading Short to YouTube ---")
    creds = Credentials(
        token=None,
        refresh_token=os.environ.get("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("YOUTUBE_CLIENT_ID"),
        client_secret=os.environ.get("YOUTUBE_CLIENT_SECRET"),
    )

    youtube = build("youtube", "v3", credentials=creds)

    request_body = {
        "snippet": {
            "title": "360° Luxury Diamond Solitaire Ring Showcase ✨ #shorts #jewelry",
            "description": "Experience the luxury view of this stunning solitaire diamond ring.\n\n#jewelry #diamondring #shorts #luxury #cgi",
            "tags": ["jewelry", "shorts", "luxury", "gold", "diamond"],
            "categoryId": "26"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video_filename, chunksize=-1, resumable=True)
    response = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    ).execute()

    print(f"Video uploaded successfully! Video ID: {response.get('id')}\n")

if __name__ == "__main__":
    img_file, vid_file = generate_video_with_ffmpeg()
    
    try:
        upload_to_youtube(vid_file)
    finally:
        # Cleanup local files
        if os.path.exists(img_file):
            os.remove(img_file)
        if os.path.exists(vid_file):
            os.remove(vid_file)
