import subprocess
import re
import requests
import os
from openai import OpenAI
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from pydub import AudioSegment

YT_DLP_REPO = "yt-dlp/yt-dlp"
YT_DLP_EXE = "yt-dlp.exe"
OPENAI_API_KEY = ""
CLIENT_SECRET_PATH = "credentials.json"
API_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def import_config():
    global OPENAI_API_KEY

    try:
        with open("config.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                if "OPENAI_API_KEY" in line:
                    OPENAI_API_KEY = line.split("=").pop().strip()
    except Exception as e:
        print(f"Error importing config: {e}")

def check_for_ytdlp_update():
    apiurl = f"https://api.github.com/repos/{YT_DLP_REPO}/releases/latest"

    version = requests.get(apiurl).json()['tag_name']

    if os.path.exists("ytdlp_version.txt"):
        with open("ytdlp_version.txt", "r") as f:
            current_version = f.read()

        if version != current_version:
            return update_ytdlp()
        
    else:
        return update_ytdlp()
        
def update_ytdlp():
    print("Updating yt-dlp...")

    if os.path.exists(YT_DLP_EXE):
        os.remove(YT_DLP_EXE)
        
    try:
        response = requests.get(f"https://github.com/{YT_DLP_REPO}/releases/latest/download/{YT_DLP_EXE}")

        with open(YT_DLP_EXE, 'wb') as file:
            file.write(response.content)

        yt_dlp_version = requests.get(f"https://api.github.com/repos/{YT_DLP_REPO}/releases/latest").json()['tag_name']

        with open("ytdlp_version.txt", "w") as f:
            f.write(yt_dlp_version)
        
        print(f"yt-dlp updated to {yt_dlp_version}")

    except Exception as e:
        print(f"Error updating yt-dlp: {e}")

def download_audio(videoid):
    dlprocess = subprocess.Popen(["yt-dlp", "-x", videoid, "-o", videoid, "--audio-format", "mp3"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = dlprocess.communicate()

    if error:
        raise Exception(f"Error downloading audio: {error.decode('utf-8')}")

    pattern = re.compile(rb'\[ExtractAudio\] Destination: (.+?)\n')

    match = pattern.search(output)

    if match:
        filename = match.group(1).decode('utf-8')
        print(f"Audio file saved as {filename}")
    else:
        raise Exception("Cannot find output audio file in log")
    
    if (os.path.getsize(filename) > 25000000):
        print("Compressing audio...")
        compress_mp3(filename, filename)
        print(f"Audio file compressed to {os.path.getsize(filename) / (1024*1024)} MB")

    return filename

def compress_mp3(input_path, output_path):
    # Load the MP3 file
    audio = AudioSegment.from_mp3(input_path)

    # Target size in bytes
    target_size_bytes = 25000000  # 25 MB

    # Set the desired bitrate (adjust as needed)
    target_bitrate = 64  # You can experiment with different bitrates

    # Export the audio with the target bitrate
    audio.export(output_path, format="mp3", bitrate=f"{target_bitrate}k")

    # Check the size of the compressed file
    compressed_size_bytes = os.path.getsize(output_path)

    # Adjust the bitrate until the file size is less than or equal to the target size
    while compressed_size_bytes > target_size_bytes and target_bitrate > 8:
        target_bitrate -= 8
        audio.export(output_path, format="mp3", bitrate=f"{target_bitrate}k")
        compressed_size_bytes = os.path.getsize(output_path)

def get_transcript(audio_filename, video_id):
    client = OpenAI(api_key=OPENAI_API_KEY)
    audio_file = open(audio_filename, "rb")
    transcription = client.audio.transcriptions.create(
      model="whisper-1", 
      file=audio_file,
      response_format="srt"
    )
    subtitle_filename = f"{video_id}.srt"
    with open(subtitle_filename, "w") as f:
        f.write(transcription)
    
    print(f"Transcript saved as {subtitle_filename}")
    return subtitle_filename

def get_authenticated_service():
    credentials = None

    token_path = 'token.json'
    if os.path.exists(token_path):
        credentials = Credentials.from_authorized_user_file(token_path)
    
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_PATH, SCOPES)
            credentials = flow.run_local_server(port=53467)

        with open(token_path, 'w') as token:
            token.write(credentials.to_json())

    return googleapiclient.discovery.build(API_NAME, API_VERSION, credentials=credentials)

def upload_subs(video_id, transcript_filename):
    youtube = get_authenticated_service()

    request = youtube.captions().insert(
        part="snippet",
        body={
            "kind": "youtube#caption",
            "snippet": {
                "videoId": video_id,
                "language": "en",
                "name": "OpenAI Whisper Subs",
            },
        },
        media_body=MediaFileUpload(transcript_filename, mimetype="application/x-subrip")
    )

    response = request.execute()

    if response["snippet"]["status"] == "serving":
        print("Subtitles uploaded successfully!")
    else:
        print("Subtitles are not being served.")
        print(response)

check_for_ytdlp_update()

import_config()

video_id = input("Enter a YouTube video ID:\n")

if "/" in video_id:
    video_id = video_id.split("/").pop().split("?").pop(1)[2:]

audio_filename = download_audio(video_id)
transcript_filename = get_transcript(audio_filename, video_id)
upload_subs(video_id, transcript_filename)

os.remove(audio_filename)
os.remove(transcript_filename)

