import logging
import os
import azure.functions as func
import azure.cognitiveservices.speech as speechsdk
import tempfile
import subprocess
import sys
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

    # Check if ffmpeg has Nvidia GPU hardware acceleration support
    try:
        result = subprocess.run(
            ["ffmpeg", "-codecs"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        # Check if 'h264_nvenc' is in the output
        ffmpeg_supports_cuda = "h264_nvenc" in result.stdout
    except Exception as e:
        logging.error(f"Error while checking ffmpeg codecs: {str(e)}")
        ffmpeg_supports_cuda = False

    # Convert the video file to audio using ffmpeg with GPU acceleration if available
    temp_audio_path = os.path.join(tempfile.gettempdir(), "audio.wav")
    try:
        start_time = time.time()
        if ffmpeg_supports_cuda:
            logging.info("Using Nvidia GPU hardware acceleration for ffmpeg.")
            subprocess.run([
                "ffmpeg", "-hwaccel", "cuda", "-i", temp_file_path, "-vn",
                "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", temp_audio_path
            ], check=True)
        else:
            logging.info("Nvidia GPU hardware acceleration not available. Using CPU for ffmpeg.")
            subprocess.run([
                "ffmpeg", "-i", temp_file_path, "-vn",
                "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", temp_audio_path
            ], check=True)
        logging.info(f"Audio extraction completed in {time.time() - start_time:.2f} seconds.")
    except Exception as e:
        logging.error(f"Error while converting video to audio: {str(e)}")
        return func.HttpResponse(f"Error while converting video to audio: {str(e)}", status_code=500)

    # Split the audio file into chunks using ffmpeg
    chunk_dir = tempfile.mkdtemp()  # Create a temporary directory for chunks
    chunk_prefix = os.path.join(chunk_dir, "chunk")
    try:
        start_time = time.time()
        subprocess.run([
            "ffmpeg", "-i", temp_audio_path, "-f", "segment", "-segment_time", "60", "-c", "copy", f"{chunk_prefix}%03d.wav"
        ], check=True)
        logging.info(f"Audio splitting completed in {time.time() - start_time:.2f} seconds.")
    except Exception as e:
        logging.error(f"Error while splitting audio into chunks: {str(e)}")
        return func.HttpResponse(f"Error while splitting audio into chunks: {str(e)}", status_code=500)

    # Initialize Azure Speech SDK
    speech_key = os.environ.get("SPEECH_KEY")
    service_region = os.environ.get("SERVICE_REGION")
    if not speech_key or not service_region:
        return func.HttpResponse("SPEECH_KEY and SERVICE_REGION environment variables are not set.", status_code=500)

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    all_transcripts = []

    # Transcribe each audio chunk with progress logging
    chunk_files = sorted(os.listdir(chunk_dir))
    total_chunks = len(chunk_files)
    chunk_progress = [0] * total_chunks  # Track progress for each chunk

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

    # Process and transcribe each chunk
    for index, chunk_file in enumerate(chunk_files):
        chunk_path = os.path.join(chunk_dir, chunk_file)
        audio_config = speechsdk.AudioConfig(filename=chunk_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Update and display progress
        logging.info(f"Processing chunk {index + 1}/{total_chunks}: {chunk_file}")
        start_time = time.time()
        result = speech_recognizer.recognize_once()
        processing_time = time.time() - start_time
        logging.info(f"Chunk {index + 1}/{total_chunks} processed in {processing_time:.2f} seconds.")

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            all_transcripts.append(result.text)
            chunk_progress[index] = 100  # Mark this chunk as complete
        else:
            logging.warning(f"No speech recognized in chunk {index + 1}/{total_chunks} or an error occurred.")
            chunk_progress[index] = 100  # Still mark as complete for progress

        # Calculate and update the total progress
        update_progress_table()

    # Combine all transcripts into one
    full_transcript = " ".join(all_transcripts)
    logging.info("Transcription process complete.")
    return func.HttpResponse(full_transcript, status_code=200)
