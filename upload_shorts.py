import os
import time
import requests
from google import genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import ImageClip

def generate_and_upload(video_num):
    print(f"--- Starting Video #{video_num} ---")
    
    # ১. জেমিনি এপিআই দিয়ে প্রম্পট ও মেটাডেটা তৈরি
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    prompt_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Generate a detailed unique text-to-image prompt for a high-end luxury jewelry piece (like a gold necklace, diamond ring, or royal bracelet) on a dark cinematic background.",
    )
    image_prompt = prompt_response.text

    meta_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Write an engaging YouTube Shorts Title and Description with hashtags for this jewelry concept: '{image_prompt}'. Format as TITLE: <title> \n DESCRIPTION: <description>",
    )
    meta_text = meta_response.text

    title = meta_text.split("DESCRIPTION:")[0].replace("TITLE:", "").strip()
    description = meta_text.split("DESCRIPTION:")[1].strip() if "DESCRIPTION:" in meta_text else meta_text

    # ২. Pollinations AI দিয়ে ইমেজ তৈরি
    print("Generating Image...")
    img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(image_prompt)}?width=1080&height=1920&nologo=true"
    img_data = requests.get(img_url).content
    
    image_filename = f"jewelry_{video_num}.jpg"
    video_filename = f"final_shorts_{video_num}.mp4"

    with open(image_filename, "wb") as handler:
        handler.write(img_data)

    # ৩. MoviePy দিয়ে ভিডিও তৈরি (৫ সেকেন্ড)
    print("Creating Video...")
    clip = ImageClip(image_filename).set_duration(5)
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

# প্রতি রানে ২টি ভিডিও তৈরির জন্য লুপ (১ ও ২)
if __name__ == "__main__":
    for i in range(1, 3):
        generate_and_upload(i)
        if i == 1:
            print("Waiting 30 seconds before generating next video...")
            time.sleep(30) # ২য় ভিডিও তৈরির আগে ৩০ সেকেন্ডের বিরতি
