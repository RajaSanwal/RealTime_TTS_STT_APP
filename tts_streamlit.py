
import os, io  # Standard library module for interacting with the operating system
from dotenv import load_dotenv  # For loading environment variables from a .env file
from fastapi import FastAPI, status, HTTPException, Body, UploadFile, File # FastAPI components
from fastapi.middleware.cors import CORSMiddleware  # Middleware for handling CORS
# import uvicorn  # ASGI server for running FastAPI applications
import logging  # Standard library module for logging
# from gppod_re_utils import *  # Custom module 
from openai import OpenAI
from fastapi.responses import JSONResponse  # Response classes for FastAPI
from google.cloud import texttospeech  # Google Cloud Text-to-Speech API client
# import random  # Standard library module for generating random numbers
import base64  # Standard library module for encoding/decoding base64
from fastapi.responses import StreamingResponse, JSONResponse  # Response classes for FastAPI
import json  # Standard library module for JSON manipulation

import streamlit as st
from audiorecorder import audiorecorder
from audio_recorder_streamlit import audio_recorder
from st_audiorec import st_audiorec
from pydantic import BaseModel
import requests
import wave
import tempfile
import soundfile as sf
from pydub import AudioSegment
import speech_recognition as sr  
import pyaudio
from streamlit_mic_recorder import mic_recorder
import subprocess,sys


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s:%(funcName)s')
file_handler = logging.FileHandler('gppod_medicalGPT.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def handle_change():
    """
    set and update session state variables
    """
    if st.session_state.input_text:
        st.session_state.text = st.session_state.input_text
    if st.session_state.voice_type_choice:
        st.session_state.voice_type = st.session_state.voice_type_choice


def autoplay_audio(audio_bytes: str):
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        md = f"""
            <audio autoplay=True controls>streamlit run 
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md,unsafe_allow_html=True)
def get_temp_file(bytes):
    # Create a temporary file and write the bytes to it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(bytes)
        temp_file.seek(0)  # Go back to the start of the file
        temp_file_path = temp_file.name
        return temp_file_path

def app():
     # set the page title and style on page load
    st.set_page_config(layout="wide")

     # add information to the page
    # st.title("Text To Speech Converter")

    # Create two equal-width columns
    col1, col2 = st.columns(2)

    with col1:
        st.write(" # Text-to-Speech Converter")
        left_btm_col, mid_btm_col, right_btm_col = st.columns(3) 
        voice_options = ["en-GB-News-J (Male)", "en-GB-News-G (Female)"]
        voice_mapping = {voice: index for index, voice in enumerate(voice_options)}
        with left_btm_col:
            selected_voice_label = st.selectbox("Voice type", on_change=handle_change, options=voice_options, index=0 ,key="voice_type_choice")
            selected_voice_type = voice_mapping[selected_voice_label]
            
        text = st.text_area("Text Input:", placeholder=f"Enter text here", key="input_text")
        tts_inputs = {'text':text, 'id':selected_voice_type}
        button = st.button('Convert')

        if text:
            if button:
                result = requests.post(url='http://127.0.0.1:9595/text_to_speech', data=json.dumps(tts_inputs))
                if result:
                    try:
                        # st.audio(result.content, format='audio/mp3', auto_play=True)
                        st.success("Audio file created successfully!  You can now play or download your audio file.")
                        st.write("# Auto-playing Audio!")
                        autoplay_audio(result.content)
                        

                        # st.audio(mybytes, format='audio/ogg')
                    except Exception as ex:
                        st.error(f"Audio not generated. Pleas try again. Error: {ex}")

                elif not result:
                    st.error("Something went wrong! Could not convert the text using the Google API!")
                    st.stop()
    with col2:
        
        st.write(" # Speech-to-Text Converter")
        audio = st_audiorec()
        try:
            if audio is not None:
                logger.info(type(audio))
                temp_file_path= get_temp_file(audio)
                with open(temp_file_path, "rb") as f:
                    files = {"file": (temp_file_path, f, "audio/wav")}
                    logger.info(files)

                    result = requests.post(url='http://127.0.0.1:9595/speech_to_text', files=files)

                if result:
                    logger.info(result.json())
                    result = result.json()
                    st.text_area('Transcribed Text', value=result['response'])
        except Exception as ex:
            st.error(f"Record audio again. Note:Use Reset First")

# def run_streamlit_app():
#     subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])

if __name__ == "__main__":
    # run_streamlit_app()
    app()