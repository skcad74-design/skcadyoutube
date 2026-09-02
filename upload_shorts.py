import os
import sys
import random
import subprocess
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

IMAGE_FOLDER = "images"
AUDIO_FILE = "bg_music.mp3"

def process_multi_image_video():
    print("--- 1. Selecting Images for Multi-Photo Video ---")
    
    if not os.path.exists(IMAGE_FOLDER):
        print(f"Error: Folder '{IMAGE_FOLDER}' not found!")
        sys.exit(1)

    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if len(images) < 3:
        print("Error: Need at least 3 images in the 'images' folder!")
        sys.exit(1)

    # ৩ থেকে ৪টি ছবি র্যান্ডমলি সিলেক্ট করা
    num_to_select = min(random.randint(3, 4), len(images))
    selected_images = [os.path.join(IMAGE_FOLDER, img) for img in random.sample(images, num_to_select)]
    print(f"Selected {len(selected_images)} Images: {selected_images}")

    temp_clips = []
    for idx, img_path in enumerate(selected_images):
        clip_name = f"temp_clip_{idx}.mp4"
        
        # অত্যন্ত স্মুথ জুম ইন এবং জুম আউট ক্যালকুলেশন (৬০ FPS - ৫ সেকেন্ড)
        if idx % 2 == 0:
            # Smooth Zoom In
            zoom_filter = "zoompan=z='min(1.0+0.0005*on,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=300:s=1080x1920:fps=60"
        else:
            # Smooth Zoom Out
            zoom_filter = "zoompan=z='max(1.15-0.0005*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=300:s=1080x1920:fps=60"

        ffmpeg_clip_cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', img_path,
            '-vf', zoom_filter,
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '16',
            '-t', '5',
            '-pix_fmt', 'yuv420p',
            '-r', '60',
            clip_name
        ]
        
        res = subprocess.run(ffmpeg_clip_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"FFmpeg Clip Creation Error: {res.stderr}")
            sys.exit(1)
            
        temp_clips.append(clip_name)

    # কনক্যাটেনেশন (Concatenation) তালিকা তৈরি
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

    # ব্যাকগ্রাউন্ড অডিও মার্জ করা
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
    return final_output

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
    vid_file = process_multi_image_video()
    try:
        upload_to_youtube(vid_file)
    finally:
        if os.path.exists(vid_file):
            os.remove(vid_file)
