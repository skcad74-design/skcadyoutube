import os
import time
import random
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy import ImageClip

JEWELRY_TYPES = [
    "diamond ring with sparkling gems", 
    "royal gold necklace with detailed craftsmanship", 
    "emerald pendant with platinum chain", 
    "ruby bracelet with vintage engraving", 
    "sapphire luxury earrings", 
    "antique wedding gold bangle"
]

STYLES = [
    "on a dark reflective turntable, 360 degree turntable view, studio lighting, 8k resolution, luxury jewelry display",
    "on a velvet rotating display stand, cinematic turntable shot, photorealistic, ultra detailed 4k studio setup"
]

def generate_and_upload(video_num):
    print(f"--- Starting Video #{video_num} ---")
    
    item = random.choice(JEWELRY_TYPES)
    style = random.choice(STYLES)
    
    # ৩৬০ ডিগ্রি টার্নটেবল লুকের জন্য প্রম্পট
    image_prompt = f"360 degree turntable product shot of a luxury {item}, {style}, isolated centered view, sharp focus."
    
    title = f"360° Luxury {item.title()} Showcase ✨ #shorts #jewelry"
    description = f"Experience the 360-degree turntable view of this stunning luxury {item}.\n\n#jewelry #360view #turntable #gold #{item.replace(' ', '')} #shorts #luxury"

    print(f"Generating 4K Image Prompt for: {item}...")
    # 4K resolution aspect ratio (Vertical Shorts 2160x3840)
    img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(image_prompt)}?width=2160&height=3840&nologo=true"
    
    try:
        img_data = requests.get(img_url, timeout=40).content
    except Exception as e:
        print(f"Image generation failed, retrying... Error: {e}")
        time.sleep(5)
        img_data = requests.get(img_url, timeout=40).content
    
    image_filename = f"jewelry_{video_num}.jpg"
    video_filename = f"final_shorts_{video_num}.mp4"

    with open(image_filename, "wb") as handler:
        handler.write(img_data)

    # ১৫ থেকে ২৫ সেকেন্ডের ভিডিও দৈর্ঘ্য
    video_duration = random.randint(18, 25) 
    print(f"Creating 4K 360-degree Animated Video ({video_duration} seconds)...")
    
    # স্মুথ রোটেশন ও জুম ইফেক্ট (360 Degree Turntable Animation Effect)
    clip = ImageClip(image_filename).with_duration(video_duration)
    
    # রোটেট এবং প্যান/জুম অ্যানিমেশন প্রয়োগ
    def rotate_effect(get_frame, t):
        # সময় অনুসারে স্মুথলি অ্যাঙ্গেল পরিবর্তন
        angle = (t / video_duration) * 360
        frame = get_frame(t)
        return frame

    animated_clip = clip.resized(height=3840).rotated(lambda t: (t / video_duration) * 360, expand=False)
    
    # 24 FPS 4K Ultra HD ভিডিও রেন্ডারিং
    animated_clip.write_videofile(video_filename, fps=24, codec="libx264", bitrate="12000k")

    print("Uploading 4K Short to YouTube...")
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
            "tags": ["jewelry 360", "turntable", "jewelry", "shorts", "luxury", "gold", "4k shorts"],
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
