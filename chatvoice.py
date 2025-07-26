import streamlit as st
import requests
import io
import wave
import tempfile
from gtts import gTTS
from audio_recorder_streamlit import audio_recorder as audiorecorder
from utils.common import get_env_or_secret
from utils.translations import translations

st.set_page_config(
    page_title="OMEGA AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


with st.sidebar:
    lang = st.selectbox("🌐 Language / Idioma", options=list(translations.keys()), index=0)
    t = translations[lang]


FASTAPI_URL = get_env_or_secret("FASTAPI_URL")
FASTAPI_URL = "http://localhost:8000/chat/streamcompletions"

def is_valid_url(url):
    return isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))

if not FASTAPI_URL or not is_valid_url(FASTAPI_URL):
    st.error(t["fastapi_error"])
    st.stop()


st.markdown("""
<style>
    .main-header { text-align: center; color: #FF5733; font-size: 3rem; font-weight: bold; margin-bottom: 2rem; }
    .error-message { background-color: #ffebee; color: #c62828; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #c62828; margin: 1rem 0; }
    .success-message { background-color: #e8f5e8; color: #2e7d32; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #2e7d32; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "new_message_processed" not in st.session_state:
    st.session_state.new_message_processed = True


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
        with requests.post(FASTAPI_URL, json=payload, headers={"Content-Type": "application/json"}, stream=True, timeout=120) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line.strip():
                    continue
                if line.startswith("data: "):
                    line = line[len("data: "):]
                if line == "[DONE]":
                    break
                yield line
    except Exception as e:
        yield f"\n**{t['error_prefix']}** {str(e)}"


def display_chat_history():
    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            if item.get("text"):
                st.markdown(item["text"])
            if item.get("audio"):
                if isinstance(item["audio"], str):
                    st.audio(item["audio"], format="audio/mp3")
                else:
                    st.audio(item["audio"], format="audio/wav")

st.markdown(f'<h1 class="main-header">{t["header"]}</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.header(t["config_header"])
    temperature = st.slider(t["temperature"], 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider(t["max_tokens"], 100, 2000, 2000, 50)
    if st.button(t["clear_chat"], type="secondary"):
        st.session_state.chat_history = []
        st.session_state.new_message_processed = True
        st.rerun()


display_chat_history()


prompt = st.chat_input(t["chat_input"])


if prompt and st.session_state.new_message_processed:
    st.session_state.chat_history.append({
        "role": "user",
        "text": prompt,
        "audio": None
    })
    st.session_state.new_message_processed = False
    st.rerun()


if not st.session_state.new_message_processed:
    full_prompt = "\n".join(
        f"{'User' if m['role']=='user' else 'Assistant'}: {m['text']}"
        for m in st.session_state.chat_history if m.get("text")
    )

    partial_content = ""
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        for chunk in stream_chat_api(full_prompt, temperature, max_tokens):
            partial_content += chunk
            message_placeholder.markdown(partial_content)

    st.session_state.chat_history.append({
        "role": "assistant",
        "text": partial_content,
        "audio": None
    })

    st.session_state.new_message_processed = True
    st.rerun()


st.markdown("""
<style>
.small-recorder > div[data-testid="stButton"] button {
    background-color: #ff4b4b; color: white; font-size: 0.1rem; padding: 0.1em 0.2em;
    border-radius: 0.5em; border: none; cursor: pointer;
}
.small-recorder > div[data-testid="stButton"] button:hover {
    background-color: #ff1c1c;
}
</style>
""", unsafe_allow_html=True)

cols = st.columns([6, 1])
with cols[1]:
    with st.container():
        st.markdown('<div class="small-recorder">', unsafe_allow_html=True)
        audio = audiorecorder("🎤 Talk with me!!!", "🔴 ضبط فعال")
        st.markdown('</div>', unsafe_allow_html=True)

if audio is not None and len(audio) > 0 and st.session_state.new_message_processed:
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(audio)
    wav_bytes = wav_buffer.getvalue()

    files = {"file": ("audio.wav", wav_buffer, "audio/wav")}
    upload_response = requests.post("http://localhost:8000/upload_audio/", files=files, timeout=60)



    transcript = "Hello, this is a test."


    st.session_state.chat_history.append({"role": "user", "text": transcript, "audio": wav_bytes})

    full_prompt = "\n".join(
        f"{'User' if m['role']=='user' else 'Assistant'}: {m['text']}"
        for m in st.session_state.chat_history if m.get("text")
    )


    response_text = "Everything is OK. This is my response."


    tts = gTTS(response_text, lang='en')
    temp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_mp3.name)


    st.session_state.chat_history.append({"role": "assistant", "text": response_text, "audio": temp_mp3.name})

    st.session_state.new_message_processed = False
    st.rerun()

if not st.session_state.new_message_processed:
    st.session_state.new_message_processed = True


st.markdown("---")
st.markdown(f"<div style='text-align: center; color: #666; font-size: 0.8rem;'>{t['footer']}</div>", unsafe_allow_html=True)
