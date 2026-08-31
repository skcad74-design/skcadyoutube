import os
import time
import random
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy import ImageClip

# জুয়েলারির বিভিন্ন উপাদানের তালিকা (যা থেকে স্বয়ংক্রিয়ভাবে প্রম্পট তৈরি হবে)
JEWELRY_TYPES = [
    "diamond ring", "gold necklace", "royal emerald pendant", 
    "ruby bracelet", "sapphire earrings", "luxury gold bangle"
]

STYLES = [
    "luxurious cinematic lighting", "royal elegance style", 
    "ultra high-end fashion photorealistic", "sparkling glow in dark studio background"
]

def generate_and_upload(video_num):
    print(f"--- Starting Video #{video_num} ---")
    
    # ১. র‍্যান্ডম প্রম্পট ও মেটাডেটা তৈরি
    item = random.choice(JEWELRY_TYPES)
    style = random.choice(STYLES)
    
    image_prompt = f"A masterpiece {item}, {style}, 8k resolution, detailed craftsmanship, macro view."
    
    title = f"Exclusive Luxury {item.title()} Design ✨ #shorts #jewelry"
    description = f"Check out this breathtaking {item}! Perfect for luxury lovers.\n\n#jewelry #gold #{item.replace(' ', '')} #fashion #luxury #shorts"

    # ২. Pollinations AI দিয়ে ফ্রি ইমেজ তৈরি
    print(f"Generating Image for: {item}...")
    img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(image_prompt)}?width=1080&height=1920&nologo=true"
    
    # ব্যাকআপ ইমেজ ট্রাই করা
    try:
        img_data = requests.get(img_url, timeout=30).content
    except Exception as e:
        print(f"Image generation failed, retrying... Error: {e}")
        time.sleep(5)
        img_data = requests.get(img_url, timeout=30).content
    
    image_filename = f"jewelry_{video_num}.jpg"
    video_filename = f"final_shorts_{video_num}.mp4"

    with open(image_filename, "wb") as handler:
        handler.write(img_data)

    # ৩. MoviePy দিয়ে শর্ট ভিডিও তৈরি (৫ সেকেন্ড)
    print("Creating Video...")
    clip = ImageClip(image_filename).with_duration(5)
    clip.write_videofile(video_filename, fps=24, codec="libx264")

    # ৪. YouTube API দিয়ে আপলোড
    print("Uploading to YouTube...")
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
            "title": title[:100],
            "description": description,
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

    print(f"Video #{video_num} uploaded successfully! Video ID: {response.get('id')}\n")

if __name__ == "__main__":
    for i in range(1, 3):
        generate_and_upload(i)
        if i == 1:
            print("Waiting 30 seconds before generating next video...")
            time.sleep(30)
