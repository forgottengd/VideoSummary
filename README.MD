[Русский](README_ru.MD)

If you don't want to enter OpenAI API key each time, you need add new line into .env
file in root directory like this:

OPEN_AI_KEY = 'your_key'

###
Whisper page: https://github.com/openai/whisper

To solve transcribe's problem "file not found" on Windows:
1. download archive with last ffmpeg version from official site
2. extract to **C:\ffmpeg\\**
3. run **setx /m PATH "C:\ffmpeg\bin;%PATH%"** (with admin rights)
4. reboot PC
5. check in cmd **ffmpeg -version** (should show version)

For using local LLM you need to write function 'summarize_local' for using your 
model in src/local_llm.py. This file contains examples

To run telegram bot you need add new line into .env:

BOT_TOKEN = 'token'

and run next command:

python main.py
