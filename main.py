import streamlit as st
import os
import time
import asyncio
import logging
from src.services.chatbot_service import chatbot
from src.services.whisper_model import load_model
from src.utils.audio_utils import is_speech, save_wav, async_speak_text, smart_record, stop_audio_playback
from src.utils.streamlit_utils import async_type_response

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

# Initialize Whisper model
model = load_model()

# Session state initialization
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_thread' not in st.session_state:
    st.session_state.current_thread = []
if 'streaming' not in st.session_state:
    st.session_state.streaming = ""
if 'bot_speaking' not in st.session_state:
    st.session_state.bot_speaking = False
if 'stop_flag' not in st.session_state:
    st.session_state.stop_flag = False
if 'running_tasks' not in st.session_state:
    st.session_state.running_tasks = []

st.sidebar.title("📜 Conversation History")

if st.sidebar.button("➕ Click Here to Save Current Conversation"):
    if st.session_state.current_thread:
        logger.info("Saving current conversation to history.")
        st.session_state.history.append(st.session_state.current_thread[:])
        st.session_state.history = st.session_state.history[-10:]
    st.session_state.current_thread = []
    logger.info("Conversation cleared for new thread.")

for idx, convo in enumerate(st.session_state.history):
    with st.sidebar.expander(f"Conversation {idx+1}"):
        st.json(convo)

st.title("🤖 Voice Chat with AI Candidate")

start_conv = st.button("🎙️ Click here to start Conversation")

if start_conv:
    logger.info("Voice conversation started.")

    # Cancel leftover tasks
    for task in st.session_state.running_tasks:
        if not task.done():
            task.cancel()
            logger.info("Cancelled leftover task from previous session.")
    st.session_state.running_tasks.clear()

    # 🔇 Stop audio if still playing
    stop_audio_playback()

    st.session_state.stop_flag = False
    st.session_state.bot_speaking = False
    st.markdown("**🟢 Voice mode activated!** &nbsp;&nbsp;&nbsp; 🗣 *Speak naturally. Say 'bye' to stop.*")


    stop_conv = st.button("🛑 Stop Conversation")
    if stop_conv:
        st.session_state.stop_flag = True
        logger.info("Stop button pressed by user.")

        # Cancel async tasks
        for task in st.session_state.running_tasks:
            if not task.done():
                task.cancel()
                logger.info("Cancelled a running task.")
        st.session_state.running_tasks.clear()

        # 🔇 Stop audio if still playing
        stop_audio_playback()

    blink_placeholder = st.empty()
    placeholder = st.empty()

    while True:
        # 🧹 Cleanup finished tasks
        st.session_state.running_tasks = [
            t for t in st.session_state.running_tasks if not t.done()
        ]

        while st.session_state.get("bot_speaking", False):
            logger.info("Bot is speaking. Waiting before recording next chunk.")
            st.info("🤖 Bot is speaking, please wait...")
            time.sleep(0.5)

        if st.session_state.stop_flag:
            logger.info("Stop flag detected. Exiting conversation loop.")
            break

        time.sleep(0.5)
        blink_placeholder.markdown("##### 🎤 Listening...")
        frames = smart_record()
        logger.info(f"Recorded {len(frames)} frames.")

        if not is_speech(frames):
            st.warning("🤫 Ignored: silence or background noise.")
            logger.info("Silence/background noise detected. Skipping this chunk.")
            time.sleep(1)
            continue

        save_wav(frames)
        chunk_file = "temp_chunk.wav"

        segments, _ = model.transcribe(chunk_file, beam_size=1, vad_filter=True)
        if segments is None:
            st.warning("🤫 Ignored: silence or background noise.")
            logger.info("Silence/background noise detected. Skipping this chunk.")
            time.sleep(1)
            continue
        logger.info(f"Saved audio chunk to {chunk_file}")
        os.remove(chunk_file)

        exit_flag = False

        for segment in segments:
            user_text = segment.text.strip()
            logger.info(f"User said: {user_text}")

            if not user_text or len(user_text.split()) < 2:
                st.warning("🤫 Ignored: too short or incomplete sentence.")
                logger.info("Short/incomplete text. Skipping response generation.")
                continue

            st.session_state.streaming = f"🤞 Processing: {user_text}..."
            placeholder.markdown(st.session_state.streaming)

            st.session_state.current_thread.append({"user": user_text})
            bot_reply = chatbot(user_text)
            st.session_state.current_thread[-1]["bot"] = bot_reply
            logger.info(f"Bot replied: {bot_reply}")
            time.sleep(0.5)

            response_text = f"🤞 **You:** {user_text}\n\n🤖 **Bot:** {bot_reply}"

            async def run_typing_and_speaking():
                task1 = asyncio.ensure_future(async_type_response(placeholder, response_text))
                task2 = asyncio.ensure_future(async_speak_text(bot_reply))
                st.session_state.running_tasks.extend([task1, task2])
                try:
                    await asyncio.gather(task1, task2)
                except asyncio.CancelledError:
                    logger.info("Typing or TTS task was cancelled.")

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                task = asyncio.ensure_future(run_typing_and_speaking())
                st.session_state.running_tasks.append(task)
            else:
                try:
                    loop.run_until_complete(run_typing_and_speaking())
                except Exception as e:
                    logger.error(f"TTS failed: {e}")
                    st.warning("⚠️ Couldn't play the voice, but here's the response:")

            if "bye" in user_text.lower() or st.session_state.stop_flag:
                logger.info("User said 'bye' or stop flag detected. Exiting conversation loop.")
                exit_flag = True
                break

        if exit_flag:
            if st.session_state.current_thread:
                st.session_state.history.append(st.session_state.current_thread[:])
                st.session_state.history = st.session_state.history[-10:]
                st.session_state.current_thread = []
            st.success("✅ Conversation saved!")
            logger.info("Exiting and rerunning Streamlit app.")
            st.rerun()
            break
