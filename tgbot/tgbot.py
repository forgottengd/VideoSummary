import os

from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

if TOKEN is None:
    raise ValueError('BOT_TOKEN is not set in .env')

dp = Dispatcher()
bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
