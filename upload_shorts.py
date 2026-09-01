import os
import sys
import time
import random
import subprocess
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# আপনার ছবির সম্পূর্ণ ডিটেইলিং সহ 4K Ultra-HD প্রম্পট লিস্ট
PROMPTS = [
    # ১. Cushion-cut Blue Sapphire & Triangular Diamonds (আপনার ১ নম্বর ছবির হুবহু ডিটেইলস)
    (
        "A hyperrealistic 4k UHD photorealistic 3D CAD render of a luxury 18k yellow gold trilogy engagement ring. "
        "Center stone is a large, vibrant, cushion-cut natural blue sapphire with intricate brilliant facets. "
        "Flanked by two bright white triangle trillion-cut side diamonds set in yellow gold prongs. "
        "Isolated on a pristine seamless solid white studio background, ultra-sharp focus, professional macro jewelry photography, "
        "realistic glossy gold reflections, raytraced lighting, 8k detail, no blur, no humans"
    ),
    # ২. Leaf Pattern Eternity Band with Diamonds (আপনার ২ নম্বর ছবির হুবহু ডিটেইলস)
    (
        "A hyperrealistic 4k UHD photorealistic 3D CAD render of a delicate 18k yellow gold nature-inspired eternity band. "
        "Designed with intricate carved gold leaves wrapped around the ring, with small round brilliant-cut diamonds prong-set between the leaf patterns. "
        "Upright angle, centered on a pure solid white background with subtle realistic shadow underneath. "
        "High polish yellow gold texture, macro lens shot, pin-sharp detail, professional studio light, 8k render, no blur"
    ),
    # ৩. Hammered Textured Gold Band with Flush-set Diamond (আপনার ৩ নম্বর ছবির হুবহু ডিটেইলস)
    (
        "A hyperrealistic 4k UHD photorealistic 3D CAD render of a premium 18k yellow gold unisex wedding band. "
        "The outer surface features a finely detailed hammered and brushed gold texture with smooth polished outer bevel edges. "
        "Flush-set with a single round sparkling diamond embedded seamlessly on the textured band. "
        "Angled shot on a clean pure white background with realistic soft reflections, ultra-detailed metal surface, crisp focus, studio lighting"
    )
]

def generate_video_with_ffmpeg():
    print("--- 1. Generating 4K Ultra HD Image via Pollinations AI ---")
    
    selected_prompt = random.choice(PROMPTS)
    seed = random.randint(1, 99999)
    
    # Ultra HD High Resolution Query (2160x3840) with flux model
    img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(selected_prompt)}?width=2160&height=3840&nologo=true&seed={seed}&model=flux"
    
    try:
        response = requests.get(img_url, timeout=120)
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

    print("--- 2. Converting Image to High-Bitrate 4K Video via FFmpeg ---")
    
    # Lossless Quality FFmpeg Video Encoding (CRF 16, Bitrate 40M)
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', image_filename,
        '-vf', "zoompan=z='min(zoom+0.001,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=300:s=2160x3840",
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '16',
        '-b:v', '40M',
        '-t', '10',
        '-pix_fmt', 'yuv420p',
        '-r', '30',
        video_filename
    ]
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg Error: {result.stderr}")
        sys.exit(1)
        
    print("Full HD/4K Detailed Video Created Successfully!")
    return image_filename, video_filename

def upload_to_youtube(video_filename):
    print("--- 3. Uploading High Quality Short to YouTube ---")
    
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
            "title": "Ultra 4K Luxury Fine Jewelry Design Showcase ✨ #shorts #jewelry",
            "description": "Experience the ultra-HD 4K view of this handcrafted 18k gold ring design.\n\n#jewelry #goldring #shorts #luxury #4k #craftsmanship #ring",
            "tags": ["jewelry", "shorts", "luxury", "gold", "ring", "4k"],
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
