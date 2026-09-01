import os
import random
import time
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy import ImageClip

# বিস্তারিত জুয়েলারি প্রম্পট
DETAILED_JEWELRY_PROMPT = (
    "Create a premium photorealistic 3D jewelry product video of the exact ring design shown in the reference image. "
    "A luxurious solitaire diamond ring made of highly polished white gold/platinum, featuring one large round brilliant-cut center diamond surrounded by a delicate halo of small diamonds, with additional small diamonds set along both shoulders of the ring. "
    "The ring is positioned upright and centered on a completely clean pure white studio background. Slowly rotate the ring smoothly around its vertical axis, showing the front, side, three-quarter and rear views naturally. Complete a slow elegant 360-degree rotation in approximately 10 seconds. "
    "Keep the camera completely stable and centered. Use a subtle premium jewelry commercial camera style with a very slight cinematic perspective. Realistic studio lighting, soft shadows underneath the ring, accurate white-metal reflections, realistic diamond refraction and dispersion, crisp facets, natural sparkling highlights and beautiful controlled diamond flashes. "
    "The ring must remain perfectly centered, sharp and unchanged throughout the entire video. Preserve the exact jewelry design, proportions, stone positions, prongs, halo and band shape from the reference image. "
    "Ultra-realistic jewelry CGI, luxury jewelry advertisement, high-end product visualization, photorealistic materials, 4K/8K quality, clean minimal background, smooth motion, realistic reflections, professional jewelry rendering. "
    "No hands, no person, no model, no text, no logo, no extra jewelry, no background objects, no camera shake, no deformation, no morphing, no change in ring design."
)

def generate_and_upload():
    print("--- Starting Jewelry Video Generation ---")
    
    title = "360° Luxury Diamond Solitaire Ring Showcase ✨ #shorts #jewelry"
    description = (
        "Experience the 360-degree turntable view of this stunning luxury solitaire diamond ring.\n\n"
        "#jewelry #360view #turntable #diamondring #shorts #luxury #cgi"
    )

    print("Generating 4K Image Prompt...")
    # Vertical Shorts resolution (2160x3840)
    img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(DETAILED_JEWELRY_PROMPT)}?width=2160&height=3840&nologo=true"
    
    try:
        img_data = requests.get(img_url, timeout=40).content
    except Exception as e:
        print(f"Image generation failed, retrying... Error: {e}")
        time.sleep(5)
        img_data = requests.get(img_url, timeout=40).content

    image_filename = "jewelry_temp.jpg"
    video_filename = "final_shorts_temp.mp4"

    with open(image_filename, "wb") as handler:
        handler.write(img_data)

    # ১০ সেকেন্ডের ভিডিও দৈর্ঘ্য
    video_duration = 10 
    print(f"Creating 4K 360-degree Animated Video ({video_duration} seconds)...")
    
    clip = ImageClip(image_filename).with_duration(video_duration)
    
    # ৩৬০ ডিগ্রি স্লো রোটেশন অ্যানিমেশন
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
            "tags": ["jewelry 360", "turntable", "jewelry", "shorts", "luxury", "gold", "4k shorts", "diamond"],
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

    # ফাইলগুলো মুছে ফেলার মাধ্যমে স্থান ফাঁকা করা
    if os.path.exists(image_filename):
        os.remove(image_filename)
    if os.path.exists(video_filename):
        os.remove(video_filename)

if __name__ == "__main__":
    # প্রতিবার রান হলে ঠিক ১টি করে ভিডিও জেনারেট ও আপলোড হবে
    generate_and_upload()
