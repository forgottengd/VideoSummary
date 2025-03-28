import os
import torch.cuda
import whisper
from typing import Tuple
from openai import OpenAI
from moviepy import AudioFileClip
from pytube import YouTube
from pytube.request import stream


def is_youtube_url(url: str) -> bool:
    if url.startswith("https://www.youtube.com/watch?v=") or \
        url.startswith("https://www.youtube.com/shorts/") or \
        url.startswith("www.youtube.com/watch?v=") or \
        url.startswith("https://youtube.com/watch?v=") or \
        url.startswith("https://youtu.be/"):
        return True
    return False

def parse_time_to_hhmmss(time: int) -> str:
    hours = time // 3600
    time -= 3600 * hours
    minutes = time // 60
    seconds = time - 60 * minutes
    if hours == 0:
        if minutes == 0:
            return f"00:{seconds:02}"
        return f"{minutes:02}:{seconds:02}"
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def parse_time_to_seconds(time: str) -> int:
    time_parts = time.split(":")
    if len(time_parts) == 3:
        return int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
    return int(time_parts[0]) * 60 + int(time_parts[1])


def video_info(youtube_url: str, proxy=None) -> Tuple:
    """
    Retrieve information of a YouTube video.

    Examples
    --------
    videoId, videoTitle, videoLength = video_info("https://www.youtube.com/watch?v=XxCZC5dF8D8")
    """
    if proxy:
        yt = YouTube(youtube_url, proxies={"http": proxy, "https": proxy})
    else:
        yt = YouTube(youtube_url)
    return yt.video_id, yt.title, yt.length


def trim_video(path_to_file: str, path_to_trimmed: str, timing: Tuple[str, str]) -> None:
    file = AudioFileClip(path_to_file)
    start_time, end_time = timing
    if end_time == "":
        v = file.subclipped(start_time)
    else:
        v = file.subclipped(start_time, end_time)
    v.write_audiofile(path_to_trimmed, codec='mp3')


def download_audio(youtube_url: str, download_path: str, proxy=None) -> None:
    """
    Download the audio from a YouTube video.

    Examples
    --------
    download_audio("https://www.youtube.com/watch?v=XxCZC5dF8D8", "audio.mp4")
    """
    if proxy:
        yt = YouTube(youtube_url, proxies={"http": proxy, "https": proxy})
    else:
        yt = YouTube(youtube_url)
    path, filename = os.path.split(download_path)
    yt.streams.filter(only_audio=True, mime_type='audio/mp4').first().download(path, filename)


def convert_mp4_to_mp3(input_path: str, output_path: str) -> None:
    """
    Convert an audio file from mp4 format to mp3.

    Examples
    --------
    convert_mp4_to_mp3("audio.mp4", "audio.mp3")
    """
    with AudioFileClip(input_path) as audio:
        audio.write_audiofile(output_path, codec='mp3')

    os.remove(input_path)


def transcribe(file_path: str, model_name="medium") -> str:
    """
    Transcribe input audio file.

    Examples
    --------
    text = transcribe(".../audio.mp3")
    print(text)
    'This text explains...'
    """
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"Transcribe using device {device}")
    model = whisper.load_model(model_name, device=device)
    result = model.transcribe(file_path)
    return result['text']


def summary_prompt(input_text: str) -> str:
    """
    Build prompt using input text of the video.
    """
    prompt = f"""
    Твоя задача сгенерировать короткое саммари для расшифровки видео с YouTube.
    Сделай суммаризацию для текста ниже, заключенного в тройные квадратные скобки.
    Сфокусируйся на главных аспектах о чем говорится в видео.

    Текст для суммаризации ```{input_text}```
    """
    return prompt


def summarize_openai_text(input_text: str, model: str = "gpt-3.5-turbo", api_key: str = None) -> str:
    """
    Summarize input text of the video.

    Examples
    --------
    summary = summarize_text(video_text)
    print(summary)
    'This video explains...'
    """
    # Send request to OpenAI
    openai = OpenAI(api_key=api_key)
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": summary_prompt(input_text),
            }
        ],
        temperature=0.6,  # Уровень случайности вывода модели

    )
    # Return response
    return response.choices[0].message.content
