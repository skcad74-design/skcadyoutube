import os
import sys
import random
import subprocess
import socket
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# কোড যেন কোনো কারণে না ঝুলে থাকে
socket.setdefaulttimeout(30)

IMAGE_FOLDER = "images"
AUDIO_FILE = "bg_music.mp3"

RESOLUTION = "1080x1920"
WIDTH, HEIGHT = RESOLUTION.split('x')

TITLES = [
    "360° Luxury Handcrafted Jewelry Showcase ✨ #shorts #jewelry",
    "Exquisite Gold & Diamond Jewelry Design 💎 #shorts #cad",
    "Handcrafted Luxury Pendant Showcase 🌟 #shorts #jewelry",
    "Unique Custom Jewelry CAD Design 360° ✨ #shorts #gold",
    "Premium Artisan Jewelry Collection 💍 #shorts #luxury"
]

def process_multi_image_video():
    print("--- 1. Selecting Images for Multi-Photo Video ---")
    
    if not os.path.exists(IMAGE_FOLDER):
        print(f"Error: Folder '{IMAGE_FOLDER}' not found!")
        sys.exit(1)

    images = [
        os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    
    if len(images) < 2:
        print("Error: Need at least 2 images in the folder!")
        sys.exit(1)

    select_count = random.randint(2, 4)
    num_to_select = min(select_count, len(images))
    selected_images = random.sample(images, num_to_select)

    print(f"Selected Images: {selected_images}")

    per_clip_duration = random.choice([5, 6])
    # ৩০ এফপিএস ব্যবহার করায় রেন্ডারিং ১০ গুণ দ্রুত হবে
    target_fps = 30
    frames_count = per_clip_duration * target_fps

    temp_clips = []
    for idx, img_path in enumerate(selected_images):
        clip_name = f"temp_clip_{idx}.mp4"
        
        if idx % 2 == 0:
            zoom_expr = "min(1.0+0.001*on,1.15)"
        else:
            zoom_expr = "max(1.15-0.001*on,1.0)"

        zoom_filter = (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_count}:s={RESOLUTION}:fps={target_fps}"
        )

        ffmpeg_clip_cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', img_path,
            '-vf', zoom_filter,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'stillimage',
            '-crf', '26',
            '-t', str(per_clip_duration),
            '-pix_fmt', 'yuv420p',
            clip_name
        ]
        
        res = subprocess.run(ffmpeg_clip_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"FFmpeg Clip Creation Error: {res.stderr}")
            sys.exit(1)
            
        temp_clips.append(clip_name)

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
            '-b:a', '128k',
            '-shortest',
            final_output
        ]
        res = subprocess.run(ffmpeg_final, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"FFmpeg Final Merge Error: {res.stderr}")
            sys.exit(1)
    else:
        final_output = combined_video

    for clip in temp_clips:
        if os.path.exists(clip):
            os.remove(clip)
    if os.path.exists(concat_list):
        os.remove(concat_list)
    if os.path.exists(combined_video) and combined_video != final_output:
        os.remove(combined_video)

    print("Multi-Photo HD Video Created Successfully!")
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

    selected_title = random.choice(TITLES)

    request_body = {
        "snippet": {
            "title": selected_title,
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

    video_id = response.get('id')
    print(f"Uploaded successfully! Video ID: {video_id}\n")

if __name__ == "__main__":
    vid_file, images_to_delete = process_multi_image_video()
    try:
        upload_to_youtube(vid_file)
        
        print("--- Cleaning up used images ---")
        for img_path in images_to_delete:
            if os.path.exists(img_path):
                os.remove(img_path)
                print(f"Deleted used image: {img_path}")
                
    finally:
        if os.path.exists(vid_file):
            os.remove(vid_file)
