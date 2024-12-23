import os
import re
import streamlit as st
import configparser
import src.local_llm as local_llm
from src.utils import convert_mp4_to_mp3, download_audio, summarize_openai_text, transcribe, \
    trim_video, video_info, parse_time_to_hhmmss, parse_time_to_seconds
from dotenv import load_dotenv
from urllib.error import HTTPError


# Function to save configuration to file
def save_config(config):
    with open("config.ini", "w") as configfile:
        config.write(configfile)


def main():
    # Load config
    config = configparser.ConfigParser()
    config.read("config.ini")

    # Load .env
    load_dotenv()

    # Setup streamlit
    st.set_page_config(layout="wide")
    st.title("Видео Суммаризатор")
    col1, col2 = st.columns([3, 7], gap='medium')
    summary = video_title = ""

    with col1:
        with st.expander("Настройки", False):
            # Voice transcribe model selector
            whisper_model_select = st.selectbox("Выберите модель для распознавания аудио",
                                                ("turbo", "small", "medium", "large"),
                                                index=0,
                                                key='whisper_model_select')
            # Checkbox for turn off summary (transcribe only mode) # TEXT SUMMARY
            summarize_checkbox = st.checkbox("Суммировать текст", value=False)
            if summarize_checkbox:
                # Summary method selector
                summary_method_select = st.selectbox("Выберите модель для суммаризации текста",
                                                     ("OpenAI API", "Local LLM"),
                                                     key='summary_method_select')
                # Chose OpenAI API
                if summary_method_select == "OpenAI API":
                    openai_model_select = st.selectbox("Выберите модель OpenAI",
                                                       ("gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o"),
                                                       key='openai_model_select',
                                                       label_visibility='collapsed')
                    # Load API Key from environment
                    openai_api_key = os.getenv("OPEN_AI_KEY") or ''
                    # If no API Key in .env file, create text input field and ask user to enter key there
                    if openai_api_key == '':
                        openai_api_key_input = st.text_input("Введите API-ключ для доступа к OpenAI API",
                                                             help="If you don't want to enter OpenAI API key each "
                                                                  "time, you can write it into .env "
                                                                  "file in root directory like this: "
                                                                  "OPEN_AI_KEY = 'your_key'",
                                                             key='openai_api_key_input')
                # Chose local llm
                else:
                    # If there isn't 'summarize_local' function in local_llm.py show error and stop
                    if not hasattr(local_llm, 'summarize_local'):
                        st.error("Необходимо импортировать в проект локальные LLM модели, образец "
                                 "находится в файле local_llm.py")
                        st.stop()
            use_proxy = st.checkbox("Использовать прокси", value=True)
            if use_proxy:
                proxy = os.getenv("PROXY_VS", default="")
                login = os.getenv("PROXY_VS_LOGIN", default="")
                password = os.getenv("PROXY_VS_PASSWORD", default="")
                proxy_address = st.text_input("Прокси", proxy, help="Напишите адрес прокси в формате IP:PORT, например: 127.0.0.1:8080", key="proxy_address")
                proxy_login = st.text_input("Логин", login, help="Логин для прокси (если нужно)", key="proxy_login")
                proxy_password = st.text_input("Пароль", password, help="Пароль для прокси (если нужно)", key="proxy_password", type="password")

        # Paste url to youtube video
        youtube_url = st.text_input("Вставьте ссылку на видеоролик в youtube:")

        # Regex check youtube url
        if re.match(r"^https://www.youtube.com/watch\?v=[a-zA-Z0-9_-]*$", youtube_url):
            # if user chose summarize with OpenAI check for API key
            if summarize_checkbox and summary_method_select == "OpenAI API":
                if openai_api_key == '':
                    if openai_api_key_input == "":
                        st.error("Необходимо ввести ключ OpenAI API")
                        st.stop()
                    else:
                        openai_api_key = openai_api_key_input
            # Parse proxy settings
            if use_proxy:
                if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$", proxy_address):
                    st.error("Введите корректный адрес прокси в формате IP:PORT, например 127.0.0.1:8080")
                    st.stop()
                if proxy_login and proxy_password:
                    proxy_str = f"http://{proxy_login}:{proxy_password}@{proxy_address}"
                else:
                    proxy_str = f"http://{proxy_address}"
            else:
                proxy_str = None
            # Get information about video
            try:
                file_name, video_title, video_length = video_info(youtube_url, proxy_str)
            except Exception as e:
                print(e)
                st.error(e)
                st.stop()

            # Create checkbox for clip video
            clip_video = st.checkbox("Обрезать видео")
            if clip_video:
                clip_col1, clip_col2 = st.columns(2)
                with clip_col1:
                    start_time = st.text_input("С", "00:00", help="Пример формата: 0:30, 12:03, 01:12:04")
                with clip_col2:
                    parsed_length = parse_time_to_hhmmss(video_length)
                    end_time = st.text_input("ПО", parsed_length,
                                             help="Пример формата: 0:30, 12:03, 01:12:04")
                if not re.fullmatch(r"^(\d{1,2}:)?(\d{1,2}:)(\d){1,2}$", start_time) \
                        or (not re.fullmatch(r"^(\d{1,2}:)?(\d{1,2}:)(\d){1,2}$", end_time) or end_time == ""):
                    st.error("Введите время в правильном формате, например: 0:30, 12:03, 01:12:04")
                    st.stop()
                if not parse_time_to_seconds(start_time) < parse_time_to_seconds(end_time) \
                    or parse_time_to_seconds(end_time) > video_length:
                    st.error(f"Некорректные временные отрезки для видео. Длина видео {parsed_length}")
                    st.stop()

            # create 'Analyze' button
            transcribe_button = st.empty()
            progress_placeholder = st.empty()

            # Button to download audio from YouTube video
            if transcribe_button.button("Анализировать видео"):
                # Download audio
                try:
                    transcribe_button.empty()
                    # All mp4 and mp3 files will be saved in the runtimes folder
                    # example: runtimes/XxCZC5dF8D8.mp3
                    if not os.path.exists("runtimes/"):
                        os.mkdir("runtimes")
                    convert_path = f"runtimes/{file_name}.mp3"
                    # download file if wasn't downloaded before
                    if not os.path.exists(convert_path):
                        download_path = f"runtimes/{file_name}.mp4"
                        with st.spinner("Скачиваю видео..."):
                            download_audio(youtube_url, download_path=download_path)
                        with st.spinner("Конвертирую в mp3..."):
                            convert_mp4_to_mp3(download_path, convert_path)
                    # change file name if user wants to clip video
                    if clip_video:
                        original_path = convert_path
                        convert_path = f"runtimes/{file_name}_clip.mp3"
                        timing = start_time, end_time if end_time != parsed_length or end_time != "" else ""
                        trim_video(original_path, convert_path, timing)
                except HTTPError as e:
                    print(f"Error: {e}")
                    st.error(e)
                    transcribe_button.empty()
                    progress_placeholder.empty()
                    st.stop()
                except Exception as e:
                    print(f"Error: {e}")
                    print(f"type: {type(e)}")
                    print(f"e.args: {e.args}")
                    st.error("Пожалуйста, предоставьте корректную ссылку на видео!")
                    transcribe_button.empty()
                    progress_placeholder.empty()
                    st.stop()

                # Transcribe
                try:
                    progress_placeholder.empty()
                    with st.spinner("Распознавание аудио..."):
                        summary = transcribe(convert_path, model_name=whisper_model_select)
                        print("Transcribe is done")
                except Exception as e:
                    print(e)
                    st.error("Ошибка распознавания. Пожалуйста, попробуйте еще раз!")
                    st.stop()

                if summarize_checkbox:
                    # Summarize
                    try:
                        transcribe_button.empty()
                        progress_placeholder.text("Суммаризация...")
                        if summary_method_select == "OpenAI API":
                            summary = summarize_openai_text(summary, openai_model_select, openai_api_key)
                            config.set("Settings", "openai_model", openai_model_select)
                        else:
                            summary = local_llm.summarize_local(summary)
                        # Save settings
                        config.set("Settings", "whisper", whisper_model_select)
                        config.set("Settings", "summary_method", summary_method_select)
                        save_config(config)
                        # return Analyze button
                        transcribe_button.button("Анализировать видео")
                    except Exception as e:
                        st.error(f"Ошибка суммаризации. Пожалуйста, попробуйте еще раз!\nТекст ошибки: {e}")
                        progress_placeholder.empty()
                        st.stop()
                progress_placeholder.empty()

    with col2:
        title_placeholder = st.empty() if video_title == "" else st.subheader(f"Название видео: {video_title}")
        summ_text = st.text_area(label="Результат", value=summary.strip(), height=500)


if __name__ == "__main__":
    main()
