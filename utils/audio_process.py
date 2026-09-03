import yt_dlp
import subprocess
import os

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        filename = (
            filename
            .replace(".webm", ".wav")
            .replace(".m4a", ".wav")
        )

    return filename


def convert_to_wav(input_path: str) -> str:
    """Convert audio/video to 16kHz mono WAV using ffmpeg."""

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    command = [
        "ffmpeg",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        output_path,
        "-y"
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """Split WAV file into chunks using ffmpeg."""

    chunk_seconds = chunk_minutes * 60
    chunks = []

    duration_command = [
        "ffprobe",
        "-i",
        wav_path,
        "-show_entries",
        "format=duration",
        "-v",
        "quiet",
        "-of",
        "csv=p=0"
    ]

    duration = float(
        subprocess.check_output(duration_command)
    )

    start = 0
    index = 0

    while start < duration:

        chunk_path = f"{wav_path}_chunk_{index}.wav"

        command = [
            "ffmpeg",
            "-i",
            wav_path,
            "-ss",
            str(start),
            "-t",
            str(chunk_seconds),
            "-ac",
            "1",
            "-ar",
            "16000",
            chunk_path,
            "-y"
        ]

        subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        chunks.append(chunk_path)

        start += chunk_seconds
        index += 1

    return chunks


def process_input(source: str) -> list:

    if source.startswith(("http://", "https://")):
        print("Detected Youtube URL..Downloading Audio...")
        wav_path = download_youtube_audio(source)

    else:
        print("Detected local file..Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")

    chunks = chunk_audio(wav_path)

    print(f"Audio ready — {len(chunks)} chunk(s) created.")

    return chunks