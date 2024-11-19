import logging
import os
import azure.functions as func
import tempfile
import subprocess
import json
import uuid
import whisper
import torch
from transformers import pipeline

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
        participants = ["Salesperson", "Client"]

        # Load a pre-trained sentiment analysis model from Hugging Face
        sentiment_analyzer = pipeline("sentiment-analysis")

        # Heuristic-based speaker identification
        salesperson_clues = ["AI solution", "transform", "demo", "ROI", "strategic"]
        client_clues = ["budget", "concern", "fit", "impressive"]

        # Process each segment to build the dialog
        for segment in segments:
            text = segment["text"]
            start_time = segment["start"]
            end_time = segment["end"]

            # Use heuristic rules to identify the speaker
            if any(clue in text.lower() for clue in salesperson_clues):
                speaker = "Salesperson"
            elif any(clue in text.lower() for clue in client_clues):
                speaker = "Client"
            else:
                speaker = "Unknown Speaker"

            # Analyze sentiment using the pre-trained model
            sentiment_result = sentiment_analyzer(text)[0]
            sentiment = sentiment_result["label"]

            dialog.append({
                "Speaker": speaker,
                "Statement": text,
                "Sentiment": sentiment
            })

        logging.info("Transcription and data extraction completed.")
    except Exception as e:
        logging.error(f"Error during transcription: {str(e)}")
        return func.HttpResponse(f"Error during transcription: {str(e)}", status_code=500)

    # Construct the final JSON structure
    response_data = {
        "Meeting": {
            "Title": meeting_title,
            "Date": meeting_date,
            "Time": meeting_time,
            "Location": meeting_location,
            "Participants": participants,
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
