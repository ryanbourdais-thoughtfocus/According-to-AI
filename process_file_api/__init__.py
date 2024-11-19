import logging
import os
import azure.functions as func
import tempfile
import subprocess
import json
import uuid
import whisper
import torch
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # Check if the request contains a file
    try:
        file = req.files.get('file')
        if not file:
            return func.HttpResponse("No file found in the request. Please upload a video file.", status_code=400)
    except Exception as e:
        logging.error(f"Error while reading the file from request: {str(e)}")
        return func.HttpResponse(f"Error while reading the file from request: {str(e)}", status_code=500)

    # Save the uploaded file to a temporary location
    temp_file_path = os.path.join(tempfile.gettempdir(), file.filename)
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(file.read())
    logging.info("File saved to temporary location.")

    # Generate a unique file name for the audio output
    unique_id = uuid.uuid4().hex
    temp_audio_path = os.path.join(tempfile.gettempdir(), f"audio_{unique_id}.wav")

    # Convert the video file to mono WAV using ffmpeg
    ffmpeg_command = [
        "ffmpeg", "-i", temp_file_path, "-vn",
        "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", temp_audio_path
    ]
    logging.info(f"Full ffmpeg command: {' '.join(ffmpeg_command)}")

    try:
        logging.info("Starting ffmpeg command...")
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        logging.info("Audio track converted to WAV format.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error while converting video to audio: {e.stderr}")
        return func.HttpResponse(f"Error while converting video to audio: {e.stderr}", status_code=500)

    # Check CUDA availability
    if torch.cuda.is_available():
        logging.info(f"Using CUDA: {torch.cuda.get_device_name(0)}")
        device = "cuda"
    else:
        logging.warning("CUDA is not available. Using CPU instead.")
        device = "cpu"

    # Load the Whisper model with the appropriate device
    model = whisper.load_model("large", device=device)

    # Transcribe the full audio file with Whisper
    try:
        logging.info("Starting transcription with Whisper...")
        result = model.transcribe(
            temp_audio_path,
            no_speech_threshold=0.1,
            logprob_threshold=-1.0,
            condition_on_previous_text=True
        )

        segments = result.get("segments", [])
        dialog = []

        # Placeholder for meeting details
        meeting_title = ""
        meeting_date = ""
        meeting_time = ""
        meeting_location = ""
        participants = []

        # Function to run speaker identification and sentiment analysis in parallel
        def process_segment(segment):
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"]

            # Run Azure Speaker Recognition and Sentiment Analysis
            speaker = identify_speaker(temp_audio_path, start_time, end_time)
            sentiment = analyze_sentiment(temp_audio_path, start_time, end_time)

            return {
                "Speaker": speaker or "Unknown Speaker",
                "Statement": text,
                "Sentiment": sentiment or "Neutral"
            }

        # Use ThreadPoolExecutor to run processes concurrently
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_segment, segment) for segment in segments]
            for future in as_completed(futures):
                dialog.append(future.result())

        logging.info("Transcription and data extraction completed.")
    except Exception as e:
        logging.error(f"Error during transcription: {str(e)}")
        return func.HttpResponse(f"Error during transcription: {str(e)}", status_code=500)

    # Construct the final JSON structure
    response_data = {
        "Meeting": {
            "Title": meeting_title or "Unknown Title",
            "Date": meeting_date or "Unknown Date",
            "Time": meeting_time or "Unknown Time",
            "Location": meeting_location or "Unknown Location",
            "Participants": participants or ["Unknown Participants"],
            "Dialog": dialog,
            "ClosingNote": "The meeting concludes. Details may need to be followed up.",
            "PerformanceSummary": {
                "OverallPerformance": "Unknown",
                "Strengths": [],
                "AreasForImprovement": [],
                "ClientResponse": "No specific client response recorded."
            }
        }
    }

    return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")

# Function to identify speaker using Azure Speaker Recognition
def identify_speaker(audio_path, start_time, end_time):
    try:
        # Read your Azure subscription key and endpoint from environment variables
        subscription_key = os.environ.get("SPEECH_KEY")
        endpoint = os.environ.get("SPEECH_ENDPOINT")

        if not subscription_key or not endpoint:
            logging.error("Azure Speaker Recognition key or endpoint not set.")
            return "Unknown Speaker"

        # Prepare the audio file for Azure API
        audio_clip_path = extract_audio_clip(audio_path, start_time, end_time)
        with open(audio_clip_path, "rb") as audio_file:
            headers = {
                "Ocp-Apim-Subscription-Key": subscription_key,
                "Content-Type": "audio/wav"
            }
            response = requests.post(f"{endpoint}/identify", headers=headers, data=audio_file)
            if response.status_code == 200:
                speaker_data = response.json()
                return speaker_data.get("identifiedSpeaker", "Unknown Speaker")
            else:
                logging.error(f"Azure Speaker Recognition API error: {response.text}")
                return "Unknown Speaker"
    except Exception as e:
        logging.error(f"Error identifying speaker: {str(e)}")
        return "Unknown Speaker"

# Function to analyze sentiment using Azure Audio Sentiment Analysis
def analyze_sentiment(audio_path, start_time, end_time):
    try:
        # Read your Azure subscription key and endpoint from environment variables
        subscription_key = os.environ.get("SPEECH_KEY")
        endpoint = os.environ.get("SPEECH_ENDPOINT")

        if not subscription_key or not endpoint:
            logging.error("Azure Sentiment Analysis key or endpoint not set.")
            return "Neutral"

        # Prepare the audio file for Azure API
        audio_clip_path = extract_audio_clip(audio_path, start_time, end_time)
        with open(audio_clip_path, "rb") as audio_file:
            headers = {
                "Ocp-Apim-Subscription-Key": subscription_key,
                "Content-Type": "audio/wav"
            }
            response = requests.post(f"{endpoint}/analyzeSentiment", headers=headers, data=audio_file)
            if response.status_code == 200:
                sentiment_data = response.json()
                return sentiment_data.get("sentiment", "Neutral")
            else:
                logging.error(f"Azure Sentiment Analysis API error: {response.text}")
                return "Neutral"
    except Exception as e:
        logging.error(f"Error analyzing sentiment: {str(e)}")
        return "Neutral"

# Helper function to extract a specific audio clip
def extract_audio_clip(audio_path, start_time, end_time):
    clip_path = os.path.join(tempfile.gettempdir(), f"clip_{uuid.uuid4().hex}.wav")
    ffmpeg_command = [
        "ffmpeg", "-i", audio_path, "-ss", str(start_time), "-to", str(end_time),
        "-c", "copy", clip_path
    ]
    subprocess.run(ffmpeg_command, check=True)
    return clip_path
