import asyncio
import logging
import os
import re
import sys

from tgbot.tgbot import dp, bot
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.enums import ContentType
from aiogram import html

from src.utils import convert_mp4_to_mp3, download_audio, is_youtube_url, summarize_openai_text, transcribe, video_info
from dotenv import load_dotenv


load_dotenv()
proxy = "http://byhxfRmZ:FgeEz1jk@45.128.73.203:63362"
ydl_opts = {
    'proxy' : proxy,
}
openai_api_key = os.getenv("OPEN_AI_KEY")

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}! Paste Youtube link to get video summary")

@dp.message()
async def message_handler(message: Message) -> None:
    """
    Message handler which process messages
    """
    if message.content_type != ContentType.TEXT:
        await message.answer("You should send me a correct Youtube link")
        return
    try:
        youtube_url = message.text
        if is_youtube_url(youtube_url):
            print("passed")
            file_name, video_title, video_length = video_info(youtube_url, proxy=proxy)
            print("info received")
            await message.answer(f"Video ID: {file_name}\nVideo title: {video_title}\nVideo length: {video_length}")
            # All mp4 and mp3 files will be saved in the runtimes folder
            # example: runtimes/XxCZC5dF8D8.mp3
            if not os.path.exists("runtimes/"):
                os.mkdir("runtimes")
            convert_path = f"runtimes/{file_name}.mp3"
            # download file if wasn't downloaded before
            if not os.path.exists(convert_path):
                download_path = f"runtimes/{file_name}.mp4"
                download_audio(youtube_url, download_path=download_path)
                convert_mp4_to_mp3(download_path, convert_path)
            # Transcribe
            summary = transcribe(convert_path, model_name="turbo")
            summary = summarize_openai_text(summary, "gpt-4o", openai_api_key)
            await message.answer(f"Video summary:\n{summary}")
        else:
            await message.answer("You should send me a correct Youtube link")
    except Exception as e:
        # But not all the types is supported to be copied so need to handle it
        await message.answer(f"Error happened!\n {e}")


async def main() -> None:
    """Основная функция для запуска бота и поиска вакансий."""
    try:
        # the run events dispatching
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f'Ошибка функции main(): {e}', exc_info=True)


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        asyncio.run(main())
    except Exception as e:
        logging.error(f'Ошибка запуска бота: {e}', exc_info=True)