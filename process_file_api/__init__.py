import logging
import os
import azure.functions as func
import azure.cognitiveservices.speech as speechsdk
import tempfile
import subprocess
import json
import uuid
import sys
import time
import threading

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

    # Split the audio file into chunks using ffmpeg
    chunk_dir = tempfile.mkdtemp()  # Directory to store audio chunks
    chunk_prefix = os.path.join(chunk_dir, "chunk")
    try:
        start_time = time.time()
        subprocess.run([
            "ffmpeg", "-i", temp_audio_path, "-f", "segment", "-segment_time", "60",
            "-c", "copy", f"{chunk_prefix}%03d.wav"
        ], check=True)
        logging.info(f"Audio split into chunks in {time.time() - start_time:.2f} seconds.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error while splitting audio into chunks: {e.stderr}")
        return func.HttpResponse(f"Error while splitting audio into chunks: {e.stderr}", status_code=500)

    # Initialize Azure Speech SDK
    speech_key = os.environ.get("SPEECH_KEY")
    service_region = os.environ.get("SERVICE_REGION")
    if not speech_key or not service_region:
        return func.HttpResponse("SPEECH_KEY and SERVICE_REGION environment variables are not set.", status_code=500)

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "en-US"

    # List to store transcription results and progress tracking
    transcription_results = []
    chunk_files = sorted(os.listdir(chunk_dir))
    total_chunks = len(chunk_files)
    chunk_progress = [0] * total_chunks  # Initialize progress for each chunk

    # Function to update the progress table
    def update_progress_table():
        sys.stdout.write("\033[H\033[J")  # Clear the console
        sys.stdout.write("|chunk|progress|\n")
        for i, progress in enumerate(chunk_progress):
            sys.stdout.write(f"|{i + 1:>5}|{progress:>8}%|\n")
        sys.stdout.write("|--------------|\n")
        total_progress = sum(chunk_progress) / total_chunks
        sys.stdout.write(f"|Total:   {total_progress:.1f}%|\n")
        sys.stdout.flush()

    # Process each chunk
    for index, chunk_file in enumerate(chunk_files):
        chunk_path = os.path.join(chunk_dir, chunk_file)
        audio_config = speechsdk.AudioConfig(filename=chunk_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Handle recognized speech
        def handle_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                transcription_results.append({"text": evt.result.text})
                logging.info(f"Recognized: {evt.result.text}")
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                logging.warning("No speech recognized.")

        # Connect event handler
        speech_recognizer.recognized.connect(handle_recognized)

        # Recognize speech in the chunk
        logging.info(f"Processing chunk {index + 1}/{total_chunks}: {chunk_file}")
        start_time = time.time()
        speech_recognizer.start_continuous_recognition()

        # Wait for a reasonable amount of time to ensure the chunk is processed
        time.sleep(60)  # Adjust the sleep time as needed
        speech_recognizer.stop_continuous_recognition()

        processing_time = time.time() - start_time
        logging.info(f"Chunk {index + 1} processed in {processing_time:.2f} seconds.")

        # Update progress
        chunk_progress[index] = 100  # Mark this chunk as complete
        update_progress_table()  # Display the updated progress table

    # Return the results as a JSON response
    response_data = {
        "transcription": transcription_results
    }
    return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")
