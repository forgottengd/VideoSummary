Whisper page: https://github.com/openai/whisper

To solve "file not found" problem on Windows:
1. download archive with last ffmpeg version from official site
2. extract to **C:\ffmpeg\\**
3. run **setx /m PATH "C:\ffmpeg\bin;%PATH%"** (with admin rights)
4. reboot PC
5. check in cmd **ffmpeg -version** (should show version)

