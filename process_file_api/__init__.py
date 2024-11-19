import logging
import os
import azure.functions as func
import azure.cognitiveservices.speech as speechsdk
import tempfile
import subprocess
import json
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

    # Convert the video file to compressed mono WAV using ffmpeg
    temp_audio_path = os.path.join(tempfile.gettempdir(), "audio.wav")
    ffmpeg_command = [
        "ffmpeg", "-i", temp_file_path, "-vn",
        "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1", temp_audio_path
    ]

    # Log the full ffmpeg command
    logging.info(f"Full ffmpeg command: {' '.join(ffmpeg_command)}")

    try:
        start_time = time.time()
        logging.info("Starting ffmpeg command...")

        # Use subprocess.run to execute ffmpeg
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
    audio_config = speechsdk.AudioConfig(filename=temp_audio_path)

    # Enable continuous recognition and speaker diarization if supported
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # List to store transcription results with speaker information
    transcription_results = []

    def handle_recognized(evt):
        transcription_results.append({
            "text": evt.result.text,
            "speaker": evt.result.properties.get(
                speechsdk.PropertyId.SpeechServiceResponse_SpeakerId, "Unknown"
            )
        })
        logging.info(f"Recognized: {evt.result.text}")

    # Connect the event handler
    speech_recognizer.recognized.connect(handle_recognized)

    # Start continuous recognition
    logging.info("Starting continuous recognition...")
    speech_recognizer.start_continuous_recognition()

    # Wait until the recognition is done (you might want to set a timeout)
    time.sleep(10)  # Adjust the sleep time if needed for your use case

    # Stop recognition
    speech_recognizer.stop_continuous_recognition()
    logging.info("Continuous recognition stopped.")

    # Return the results as a JSON response
    response_data = {
        "transcription": transcription_results
    }
    return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")
