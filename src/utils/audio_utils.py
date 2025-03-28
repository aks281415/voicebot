import wave
import audioop
import pyaudio
import logging
import streamlit as st
import pygame
import asyncio
from edge_tts import Communicate
from tempfile import NamedTemporaryFile
from src.constants import (
    FORMAT,
    CHANNELS,
    RATE,
    CHUNK,
    CHUNK_DURATION_SEC,
    MAX_DURATION,
    SILENCE_THRESHOLD,
    SPEECH_THRESHOLD
)


# Mic setup
p = pyaudio.PyAudio()


def is_speech(frames):
    rms = audioop.rms(b''.join(frames), 2)
    return rms > SPEECH_THRESHOLD


def record_chunk():
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []
    for _ in range(0, int(RATE / CHUNK * CHUNK_DURATION_SEC)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()

    return frames


def save_wav(frames, filename="temp_chunk.wav"):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    
def smart_record():
    collected_frames = []
    silence_counter = 0
    total_seconds = 0

    logging.info("🎙️ Smart recording started...")

    while total_seconds < MAX_DURATION:
        chunk = record_chunk()
        total_seconds += 1

        if is_speech(chunk):
            collected_frames.extend(chunk)
            silence_counter = 0
            logging.info(f"Speech detected (t={total_seconds}s), total frames so far: {len(collected_frames)}")
        else:
            silence_counter += 1
            logging.info(f"Silence detected ({silence_counter}/{SILENCE_THRESHOLD})")

            if silence_counter >= SILENCE_THRESHOLD:
                logging.info("Silence threshold reached. Ending smart_record.")
                break

    return collected_frames


async def async_speak_text(text: str, voice="en-US-GuyNeural", rate="+20%"):
    if "bot_speaking" not in st.session_state:
        st.session_state.bot_speaking = False

    st.session_state.bot_speaking = True

    try:
        if not text or len(text.strip()) < 3:
            logging.warning("Text too short or empty for TTS. Skipping.")
            return

        communicate = Communicate(text=text, voice=voice, rate=rate)
        mp3_data = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_data += chunk["data"]

        # Save MP3 data to temp file
        temp_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.write(mp3_data)
        temp_file.close()
        mp3_path = temp_file.name

        # Play using pygame
        pygame.mixer.init()
        pygame.mixer.music.load(mp3_path)
        pygame.mixer.music.play()

        # Wait until playback finishes
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

    except Exception as e:
        logging.error(f"NoAudioReceived: {e}. Text: '{text}'")
    finally:
        st.session_state.bot_speaking = False


def stop_audio_playback():
    try:
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
    except Exception as e:
        logging.warning(f"Error stopping audio playback: {e}")





