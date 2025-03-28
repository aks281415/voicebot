from faster_whisper import WhisperModel
import streamlit as st
@st.cache_resource
def load_model():
    return WhisperModel("base", device="cpu", compute_type="int8")