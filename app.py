import os
import re
import streamlit as st
import configparser
import src.local_llm as local_llm
from uuid import uuid4
from src.utils import convert_mp4_to_mp3, download_audio, video_title, summarize_openai_text, transcribe
from dotenv import load_dotenv


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
    summary = v_title = ""

    with col1:
        # Voice transcribe model selector
        whisper_model_select = st.selectbox("Выберите модель для распознавания аудио",
                                            ("small", "small.en", "medium", "medium.en", "large"),
                                            index=2,
                                            key='whisper_model_select')
        # Checkbox for turn off summary (transcribe only mode)
        summarize_checkbox = st.checkbox("Суммировать текст", value=True)
        if summarize_checkbox:
            # Summary method selector
            summary_method_select = st.selectbox("Выберите модель для суммаризации текста", ("OpenAI API", "Local LLM"),
                                                 key='summary_method_select')
            # Chose OpenAI API
            if summary_method_select == "OpenAI API":
                openai_model_select = st.selectbox("Выберите модель OpenAI",
                                                   ("gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"),
                                                   key='openai_model_select',
                                                   label_visibility='collapsed')
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
                if not hasattr(local_llm, 'summarize_local'):
                    st.error("Необходимо импортировать в проект локальные LLM модели, образец "
                             "находится в файле local_llm.py")
                    st.stop()

        # Paste url to youtube video
        youtube_url = st.text_input("Вставьте ссылку на видеоролик в youtube:")

        # Regex check youtube url
        if re.match(r"^https://www.youtube.com/watch\?v=[a-zA-Z0-9_-]*$", youtube_url):
            # if user chose summirize with OpenAI check for API key
            if summarize_checkbox and summary_method_select == "OpenAI API":
                if openai_api_key == '':
                    if openai_api_key_input == "":
                        st.error("Необходимо ввести ключ OpenAI API")
                        st.stop()
                    else:
                        openai_api_key = openai_api_key_input
            # Show video title
            v_title = video_title(youtube_url)

            # create 'Analyze' button
            transcribe_button = st.empty()
            progress_placeholder = st.empty()

            # Button to download audio from YouTube video
            if transcribe_button.button("Анализировать видео"):
                # Download audio
                try:
                    transcribe_button.empty()
                    # All mp4 and mp3 files will be saved in the runtimes folder
                    # each mp4 and mp3 will have a unique runtime_id name
                    # example: runtimes/cbec467e-71d9-4a3f-a3d3-406fa3438728.mp3
                    if not os.path.exists("runtimes/"):
                        os.mkdir("runtimes")
                    runtime_id = str(uuid4())
                    download_path = f"runtimes/{runtime_id}.mp4"
                    with st.spinner("Скачиваю видео..."):
                        download_audio(youtube_url, download_path=download_path)

                    convert_path = f"runtimes/{runtime_id}.mp3"
                    with st.spinner("Конвертирую в mp3..."):
                        convert_mp4_to_mp3(download_path, convert_path)
                except Exception as e:
                    print(e)
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
                    except Exception as e:
                        st.error(f"Ошибка суммаризации. Пожалуйста, попробуйте еще раз!\nТекст ошибки: {e}")
                        progress_placeholder.empty()
                        st.stop()
                progress_placeholder.empty()

    with col2:
        title_placeholder = st.empty() if v_title == "" else st.subheader(f"Название видео: {v_title}")
        summ_text = st.text_area(label="Результат", value=summary, height=500)


if __name__ == "__main__":
    main()

# https://www.youtube.com/watch?v=WGD8qvsZ1jM
