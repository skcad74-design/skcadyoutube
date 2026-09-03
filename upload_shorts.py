import os
import sys
import random
import subprocess
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

IMAGE_FOLDER = "images"
AUDIO_FILE = "bg_music.mp3"

# রেজোলিউশন কনফিগারেশন (প্রয়োজন অনুযায়ী পরিবর্তন করতে পারেন)
# HD Formats: "1080x1920" | 4K Formats: "2160x3840"
RESOLUTION = "1080x1920" 
WIDTH, HEIGHT = RESOLUTION.split('x')

def process_multi_image_video():
    print("--- 1. Selecting Images for Multi-Photo Video ---")
    
    if not os.path.exists(IMAGE_FOLDER):
        print(f"Error: Folder '{IMAGE_FOLDER}' not found!")
        sys.exit(1)

    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if len(images) < 3:
        print("Error: Need at least 3 images in the 'images' folder!")
        sys.exit(1)

    # ৩ থেকে ৫টি ছবি র্যান্ডমলি সিলেক্ট করা
    select_count = random.randint(3, 5)
    num_to_select = min(select_count, len(images))
    
    selected_images = [os.path.join(IMAGE_FOLDER, img) for img in random.sample(images, num_to_select)]
    print(f"Selected {len(selected_images)} Images: {selected_images}")

    # ১৫-৩০ সেকেন্ডের মধ্যে ভিডিও রাখতে প্রতি ছবির সময় নির্ধারণ (৫ থেকে ৬ সেকেন্ড)
    per_clip_duration = random.choice([5, 6])
    frames_count = per_clip_duration * 60  # 60 FPS

    temp_clips = []
    for idx, img_path in enumerate(selected_images):
        clip_name = f"temp_clip_{idx}.mp4"
        
        # জুম ইন এবং জুম আউট এফেক্ট
        if idx % 2 == 0:
            zoom_expr = "min(1.0+0.0005*on,1.15)"
        else:
            zoom_expr = "max(1.15-0.0005*on,1.0)"

        # Aspect Ratio 9:16 ফিক্স করে নির্ধারিত রেজোলিউশনে ক্রপ ও স্কেল করা
        zoom_filter = (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_count}:s={RESOLUTION}:fps=60"
        )

        ffmpeg_clip_cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', img_path,
            '-vf', zoom_filter,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '18',
            '-t', str(per_clip_duration),
            '-pix_fmt', 'yuv420p',
            clip_name
        ]
        
        res = subprocess.run(ffmpeg_clip_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"FFmpeg Clip Creation Error: {res.stderr}")
            sys.exit(1)
            
        temp_clips.append(clip_name)

    # ভিডিও মার্জ করার তালিকা তৈরি
    concat_list = "concat_list.txt"
    with open(concat_list, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip}'\n")

    combined_video = "combined_temp.mp4"
    concat_cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list,
        '-c', 'copy',
        combined_video
    ]
    subprocess.run(concat_cmd, capture_output=True, text=True)

    final_output = "final_shorts_temp.mp4"

    # ব্যাকগ্রাউন্ড মিউজিক যুক্ত করা
    if os.path.exists(AUDIO_FILE):
        ffmpeg_final = [
            'ffmpeg', '-y',
            '-i', combined_video,
            '-stream_loop', '-1',
            '-i', AUDIO_FILE,
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            final_output
        ]
        res = subprocess.run(ffmpeg_final, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"FFmpeg Final Merge Error: {res.stderr}")
            sys.exit(1)
    else:
        final_output = combined_video

    # টেম্পোরারি ফাইল রিমুভ করা
    for clip in temp_clips:
        if os.path.exists(clip):
            os.remove(clip)
    if os.path.exists(concat_list):
        os.remove(concat_list)
    if os.path.exists(combined_video) and combined_video != final_output:
        os.remove(combined_video)

    print("Ultra-Smooth Multi-Photo HD Video Created Successfully!")
    return final_output, selected_images

def upload_to_youtube(video_filename):
    print("--- 2. Uploading Video to YouTube ---")
    
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")

    if not all([refresh_token, client_id, client_secret]):
        print("Error: YouTube secrets are missing!")
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
            "title": "360° Luxury Handcrafted Jewelry Showcase ✨ #shorts #jewelry",
            "description": "Exclusive luxury handcrafted gold & diamond jewelry design showcase.\n\n#jewelry #shorts #luxury #goldring #cad",
            "tags": ["jewelry", "shorts", "luxury", "gold", "ring"],
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

    print(f"Uploaded successfully! Video ID: {response.get('id')}\n")

if __name__ == "__main__":
    vid_file, used_images = process_multi_image_video()
    try:
        upload_to_youtube(vid_file)
        
        # আপলোড সফল হওয়ার পর ব্যবহৃত ছবি ডিলিট করা
        print("Cleaning up used images from repository...")
        for img_path in used_images:
            if os.path.exists(img_path):
                os.remove(img_path)
                print(f"Deleted used image: {img_path}")
                
    finally:
        if os.path.exists(vid_file):
            os.remove(vid_file)
