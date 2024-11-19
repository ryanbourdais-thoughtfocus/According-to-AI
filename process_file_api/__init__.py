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
    except Exception as e:
        logging.error(f"Error while converting video to audio: {str(e)}")
        return func.HttpResponse(f"Error while converting video to audio: {str(e)}", status_code=500)

    # Split the audio file into chunks using ffmpeg
    chunk_dir = tempfile.mkdtemp()  # Create a temporary directory for chunks
    chunk_prefix = os.path.join(chunk_dir, "chunk")
    try:
        subprocess.run([
            "ffmpeg", "-i", temp_audio_path, "-f", "segment", "-segment_time", "60", "-c", "copy", f"{chunk_prefix}%03d.wav"
        ], check=True)
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

    # Transcribe each audio chunk
    for chunk_file in sorted(os.listdir(chunk_dir)):
        chunk_path = os.path.join(chunk_dir, chunk_file)
        audio_config = speechsdk.AudioConfig(filename=chunk_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Perform the transcription for each chunk
        result = speech_recognizer.recognize_once()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            all_transcripts.append(result.text)
        else:
            logging.warning(f"No speech recognized in {chunk_file} or an error occurred.")

    # Combine all transcripts into one
    full_transcript = " ".join(all_transcripts)
    return func.HttpResponse(full_transcript, status_code=200)
