import logging
import os
import azure.functions as func
import azure.cognitiveservices.speech as speechsdk
import tempfile
import subprocess

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

    # Convert the video file to audio using ffmpeg (ensure ffmpeg is installed)
    temp_audio_path = os.path.join(tempfile.gettempdir(), "audio.wav")
    try:
        subprocess.run(["ffmpeg", "-i", temp_file_path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", temp_audio_path], check=True)
    except Exception as e:
        logging.error(f"Error while converting video to audio: {str(e)}")
        return func.HttpResponse(f"Error while converting video to audio: {str(e)}", status_code=500)

    # Initialize Azure Speech SDK
    speech_key = os.environ.get("SPEECH_KEY")
    service_region = os.environ.get("SERVICE_REGION")
    if not speech_key or not service_region:
        return func.HttpResponse("SPEECH_KEY and SERVICE_REGION environment variables are not set.", status_code=500)

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    audio_config = speechsdk.AudioConfig(filename=temp_audio_path)

    # Set up the speech recognizer for continuous recognition
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Collect the full transcript
    all_transcripts = []

    def handle_recognized(evt):
        all_transcripts.append(evt.result.text)

    # Connect the event handler
    speech_recognizer.recognized.connect(handle_recognized)

    # Start continuous recognition
    speech_recognizer.start_continuous_recognition()
    logging.info("Recognition started. Waiting for completion...")

    # Wait until recognition is done
    speech_recognizer.recognize_once_async().get()

    # Stop recognition
    speech_recognizer.stop()
