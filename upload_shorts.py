import os
import time
import requests
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy import ImageClip

# ১. Gemini API কনফিগার করা
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_and_upload(video_num):
    print(f"--- Starting Video #{video_num} ---")
    
    # ২. প্রম্পট ও ভিডিওর টাইটেল/ডেসক্রিপশন তৈরি
    prompt_response = model.generate_content(
        "Generate a detailed unique text-to-image prompt for a high-end luxury jewelry piece (like a gold necklace, diamond ring, or royal bracelet) on a dark cinematic background."
    )
    image_prompt = prompt_response.text

    meta_response = model.generate_content(
        f"Write an engaging YouTube Shorts Title and Description with hashtags for this jewelry concept: '{image_prompt}'. Format as TITLE: <title> \n DESCRIPTION: <description>"
    )
    meta_text = meta_response.text

    title = meta_text.split("DESCRIPTION:")[0].replace("TITLE:", "").strip()
    description = meta_text.split("DESCRIPTION:")[1].strip() if "DESCRIPTION:" in meta_text else meta_text

    # ৩. Pollinations AI দিয়ে ইমেজ তৈরি
    print("Generating Image...")
    img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(image_prompt)}?width=1080&height=1920&nologo=true"
    img_data = requests.get(img_url).content
    
    image_filename = f"jewelry_{video_num}.jpg"
    video_filename = f"final_shorts_{video_num}.mp4"

    with open(image_filename, "wb") as handler:
        handler.write(img_data)

    # ৪. MoviePy দিয়ে ভিডিও তৈরি (৫ সেকেন্ড)
    print("Creating Video...")
    clip = ImageClip(image_filename).with_duration(5)
    clip.write_videofile(video_filename, fps=24, codec="libx264")

    # ৫. YouTube API দিয়ে আপলোড
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
