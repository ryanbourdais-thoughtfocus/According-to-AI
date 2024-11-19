import logging
import os
import azure.functions as func
import azure.cognitiveservices.speech as speechsdk
import tempfile
import subprocess
import json
import uuid
import time

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

    # Log the full ffmpeg command
    logging.info(f"Full ffmpeg command: {' '.join(ffmpeg_command)}")

    try:
        start_time = time.time()
        logging.info("Starting ffmpeg command...")
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        logging.info(f"Audio track converted to WAV format in {time.time() - start_time:.2f} seconds.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error while converting video to audio: {e.stderr}")
        return func.HttpResponse(f"Error while converting video to audio: {e.stderr}", status_code=500)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(f"Unexpected error: {str(e)}", status_code=500)

    # Initialize Azure Speech SDK
    speech_key = os.environ.get("SPEECH_KEY")
    service_region = os.environ.get("SERVICE_REGION")
    if not speech_key or not service_region:
        return func.HttpResponse("SPEECH_KEY and SERVICE_REGION environment variables are not set.", status_code=500)

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "en-US"  # Set your desired language
    audio_config = speechsdk.AudioConfig(filename=temp_audio_path)

    # Perform the transcription using recognize_once_async
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    logging.info("Starting single recognition...")
    result = speech_recognizer.recognize_once_async().get()

    # Check if the result contains recognized speech
    transcription_results = []
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        transcription_results.append({"text": result.text})
        logging.info(f"Recognized: {result.text}")
    else:
        logging.warning("No speech recognized or an error occurred.")

    # Return the results as a JSON response
    response_data = {
        "transcription": transcription_results
    }
    return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")
