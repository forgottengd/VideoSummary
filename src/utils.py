import os

from openai import OpenAI
import torch.cuda
import whisper
from moviepy.editor import AudioFileClip
from pytube import YouTube


def video_title(youtube_url: str) -> str:
    """
    Retrieve the title of a YouTube video.

    Examples
    --------
    title = video_title("https://www.youtube.com/watch?v=XxCZC5dF8D8")
    print(title)
    'Sample Video Title'
    """
    yt = YouTube(youtube_url)
    return yt.title


def download_audio(youtube_url: str, download_path: str) -> None:
    """
    Download the audio from a YouTube video.

    Examples
    --------
    download_audio("https://www.youtube.com/watch?v=XxCZC5dF8D8", "audio.mp4")
    """
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
    device = "cuda" if torch.cuda.is_available() else "cpu"
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
        temperature=0.8,  # Уровень случайности вывода модели

    )
    # Return response
    return response.choices[0].message.content
