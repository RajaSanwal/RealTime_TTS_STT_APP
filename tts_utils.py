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
from pydantic import BaseModel
import uvicorn
from  pydub import AudioSegment
import tempfile
import soundfile as sf
from playsound import playsound
from tempfile import NamedTemporaryFile
import wave
from scipy.io import wavfile
import speech_recognition
import numpy as np
from typing import List



# First you need to create .env file and set following variables in environment file
# 1. OPEN_API_KEY
# 2. MODEL_NAME ->> model name should be one of them ("mistral-medium-latest", "gpt-3.5-turbo", "gpt-4o")

# Load environment variables from a .env file
load_dotenv()
# Set Google Cloud credentials for Text-to-Speech API
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path_to_your_google_cloud_credentials_json_file
# model name for env
model_name = os.getenv("MODEL_NAME")



# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s:%(funcName)s')
file_handler = logging.FileHandler(path_to_your_log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# Initialize FastAPI application
app = FastAPI()

class Texttospeech(BaseModel):
    text: str
    id: int

class Speechtotext(BaseModel):
    audio_bytes : dict


def speech_To_Text(uploaded_file):
    client=OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    filename = uploaded_file.filename
    audio_data = uploaded_file.file.read()
    with io.BytesIO(audio_data) as audio_stream:
        audio_stream.name = filename
        transcribed_text = client.audio.transcriptions.create(model="whisper-1", file=audio_stream)
        audio_stream.close() 
    os.remove(filename)
    return transcribed_text.text

# API for speech to text conversion
@app.post("/text_to_speech", response_class=StreamingResponse)
def text_to_speech(data: Texttospeech = Body(...)):
    try:
        # Log info for entering text_to_speech endpoint
        logger.info("Entering text_to_speech endpoint")
        # Extract data from request body
        text = data.text
        id = data.id
        # Select voice based on ID
        voice_name = "en-GB-News-J" if id == 0 else "en-GB-News-G"
        # Initialize Google Cloud Text-to-Speech client
        client = texttospeech.TextToSpeechClient()
        # Configure synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        # Configure voice selection
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-GB",
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        # Configure audio output
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        # Synthesize speech
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        # Function to generate streaming response
        def generate():
            yield response.audio_content
            # yield base64.b64encode(response.audio_content).
        # Log info for successfully generating speech from text
        logger.info("Successfully generated speech from text")
        # Return streaming response with MP3 audio
        return StreamingResponse(generate(), media_type="audio/mp3")
    except Exception as ex:
        # Log critical error if speech generation fails
        logger.critical(f"Failed to generate speech from text: {str(ex)}")
        # Raise HTTPException for bad request with error detail
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
    finally:
        # Log info for exiting text_to_speech endpoint
        logger.info("Exiting text_to_speech endpoint")


# API for speech to text conversion
@app.post("/speech_to_text")
async def speech_to_text_endpoint(file:UploadFile=File(...)):
    try:
        # Log info for entering speech_to_text_endpoint
        logger.info("Entering speech_to_text endpoint")
        logger.info("Printing")
        # size = 712748
        # logger.info(type(file))
        if file.size < 100:
           return Exception("Record audio again.") 
        response_text = speech_To_Text(file)
        # Log info for successfully converting speech to text
        logger.info("Successfully converted speech to text")
        # Return JSON response with converted text
        return JSONResponse(content={"response": response_text}, status_code=status.HTTP_200_OK)
    except Exception as ex:
        # Log error if speech-to-text conversion fails
        logger.error(f"Failed to convert speech to text: {ex}")
        # Return error response for failed conversion
        return JSONResponse(content={"error": "Failed to convert speech to text"}, status_code=status.HTTP_400_BAD_REQUEST)
    finally:
        # Log info for exiting speech_to_text endpoint
        logger.info("Exiting speech_to_text endpoint")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9595)
