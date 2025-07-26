import streamlit as st
import requests
from utils.common import get_env_or_secret
from utils.translations import translations

st.set_page_config(
    page_title="OMEGA AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configuration
FASTAPI_URL = get_env_or_secret("FASTAPI_URL")
FASTAPI_URL = "http://localhost:8000/chat/streamcompletions"
# Select language before using any translated strings

with st.sidebar:
    lang = st.selectbox(
        "🌐 Language / Idioma", options=list(translations.keys()), index=0
    )
    t = translations[lang]


def is_valid_url(url):
    return isinstance(url, str) and (
        url.startswith("http://") or url.startswith("https://")
    )


if not FASTAPI_URL or not is_valid_url(FASTAPI_URL):
    st.error(t["fastapi_error"])
    st.stop()


st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        color: #FF5733;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .error-message {
        background-color: #ffebee;
        color: #c62828;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #c62828;
        margin: 1rem 0;
    }
    .success-message {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2e7d32;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    if "success_message" not in st.session_state:
        st.session_state.success_message = None


def clear_messages():
    st.session_state.messages = []
    st.session_state.error_message = None
    st.session_state.success_message = None


def format_messages_for_api(messages: list) -> str:
    formatted_prompt = ""
    for message in messages:
        role = message["role"]
        content = message["content"]
        if role == "user":
            formatted_prompt += f"User: {content}\n"
        elif role == "assistant":
            formatted_prompt += f"Assistant: {content}\n"
    return formatted_prompt.strip()


def stream_chat_api(prompt: str, temperature: float = 0.7, max_tokens: int = 512):
    payload = {
        "prompt": prompt,
        "system_prompt_strategy": "default",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 1.0,
        "top_k": 50,
        "stop": ["\n"],
        "stream": True,
        "chat_template_kwargs": {"enable_thinking": False},
    }

    try:
        with requests.post(
            FASTAPI_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=120,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line.strip():
                    continue
                if line.startswith("data: "):
                    line = line[len("data: ") :]

                if line == "[DONE]":
                    break

                yield line
    except Exception as e:
        st.session_state.error_message = f"Streaming request failed: {str(e)}"
        yield None


def display_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def display_error_messages():
    if st.session_state.error_message:
        st.markdown(
            f"""
        <div class="error-message">
            <strong>Error:</strong> {st.session_state.error_message}
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.session_state.error_message = None


def display_success_messages():
    if st.session_state.success_message:
        st.markdown(
            f"""
        <div class="success-message">
            {st.session_state.success_message}
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.session_state.success_message = None


# Initialize session state
initialize_session_state()

st.markdown(f'<h1 class="main-header">{t["header"]}</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.header(t["config_header"])

    temperature = st.slider(
        t["temperature"],
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
    )

    max_tokens = st.slider(
        t["max_tokens"],
        min_value=100,
        max_value=2000,
        value=2000,
        step=50,
    )

    if st.button(t["clear_chat"], type="secondary"):
        clear_messages()
        st.rerun()

display_error_messages()
display_success_messages()
display_messages()



prompt = st.chat_input(t["chat_input"])

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    full_prompt = format_messages_for_api(st.session_state.messages)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        partial_content = ""

        with st.empty():
            for chunk in stream_chat_api(full_prompt, temperature, max_tokens=2000):
                if chunk is None:
                    message_placeholder.markdown(t["error_prefix"])
                    break
                partial_content += chunk
                message_placeholder.markdown(partial_content)

        if partial_content:
            st.session_state.messages.append(
                {"role": "assistant", "content": partial_content}
            )
        st.rerun()

st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666; font-size: 0.8rem;'>{t['footer']}</div>",
    unsafe_allow_html=True,
)

#----------------------------------


from audio_recorder_streamlit import audio_recorder as audiorecorder
import wave
import io
from gtts import gTTS
import tempfile

# --- session state ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "new_message_processed" not in st.session_state:
    st.session_state.new_message_processed = True

# --- نمایش تاریخچه (قدیمی بالا، جدید پایین) ---
for idx, item in enumerate(st.session_state.chat_history):
    st.markdown(f"**🔊 پیام {idx + 1}:**")
    st.audio(item["user_audio"], format="audio/wav")
    st.markdown(f"🗣️ شما: _{item['user_transcript']}_")
    st.markdown(f"🤖 پاسخ: _{item['bot_text']}_")
    st.audio(item["bot_audio"], format="audio/mp3")
    st.markdown("---")

# --- استایل دکمه ضبط ---
st.markdown("""
<style>
.small-recorder > div[data-testid="stButton"] button {
    background-color: #ff4b4b;
    color: white;
    font-size: 0.1rem;
    padding: 0.1em 0.2em;
    border-radius: 0.5em;
    border: none;
    cursor: pointer;
}
.small-recorder > div[data-testid="stButton"] button:hover {
    background-color: #ff1c1c;
}
</style>
""", unsafe_allow_html=True)

# --- چیدمان دکمه در سمت راست ---
cols = st.columns([6,1])  # ستون اول پهن، ستون دوم باریک
with cols[1]:
    with st.container():
        st.markdown('<div class="small-recorder">', unsafe_allow_html=True)
        audio = audiorecorder("🎤 Talk with me!!!", "🔴 ضبط فعال")
        st.markdown('</div>', unsafe_allow_html=True)

# --- پردازش صوت ---
if audio is not None and len(audio) > 0 and st.session_state.new_message_processed:
    # WAV in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(audio)

    wav_bytes = wav_buffer.getvalue()

    # شبیه‌سازی STT
    transcript = "Hello, this is a test."

    # پاسخ
    response_text = "Everything is OK. This is my response."

    # پاسخ به MP3
    tts = gTTS(response_text, lang='en')
    temp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_mp3.name)

    # اضافه به تاریخچه
    st.session_state.chat_history.append({
        "user_audio": wav_bytes,
        "user_transcript": transcript,
        "bot_text": response_text,
        "bot_audio": temp_mp3.name
    })

    st.session_state.new_message_processed = False
    st.rerun()

if not st.session_state.new_message_processed:
    st.session_state.new_message_processed = True
