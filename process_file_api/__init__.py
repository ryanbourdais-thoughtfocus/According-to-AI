import logging
import os
import azure.functions as func
import tempfile
import subprocess
import json
import uuid
import whisper
import torch

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
    if not torch.cuda.is_available():
        logging.warning("CUDA is not available. Using CPU instead.")
    else:
        logging.info(f"Using CUDA: {torch.cuda.get_device_name(0)}")

    # Load the Whisper model with CUDA
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("large", device="cpu")  # Load on CPU first
    if device == "cuda":
        model = model.to("cuda")  # Move the model to the GPU explicitly

    # Transcribe the full audio file with adjusted parameters
    try:
        logging.info("Starting transcription with Whisper on CUDA...")
        result = model.transcribe(
            temp_audio_path,
            no_speech_threshold=0.1,
            logprob_threshold=-1.0,
            condition_on_previous_text=True
        )

        segments = result.get("segments", [])
        transcription_results = []

        # Process each segment to structure transcription
        for segment in segments:
            transcription_results.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"]
            })
        
        logging.info("Transcription completed.")
    except Exception as e:
        logging.error(f"Error during transcription: {str(e)}")
        return func.HttpResponse(f"Error during transcription: {str(e)}", status_code=500)

    # Return the transcription as a JSON response
    response_data = {
        "transcription": transcription_results
    }
    return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")
