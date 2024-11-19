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
        all_text = " ".join(segment["text"] for segment in segments)
        dialog = []

        # Meeting details
        meeting_title = "Sales Pitch for AI Solution"
        meeting_date = "2024-11-19"
        meeting_time = "2:00 PM"
        meeting_location = "Client's Office / Video Call"
        participants = ["Salesperson: Alex Johnson", "Client: Jordan Smith"]

        # Load a pre-trained sentiment analysis model from Hugging Face
        sentiment_analyzer = pipeline("sentiment-analysis")

        # AI-based speaker identification using whole-text analysis
        # For now, we'll use a simple rule-based method based on the full text
        salesperson_keywords = ["solution", "implement", "ROI", "benefit", "efficiency", "support"]
        client_keywords = ["budget", "concern", "timeline", "fit", "issues", "challenge"]

        # Heuristic analysis: determine the dominant speaker
        salesperson_count = sum(all_text.lower().count(word) for word in salesperson_keywords)
        client_count = sum(all_text.lower().count(word) for word in client_keywords)
        dominant_speaker = "Salesperson" if salesperson_count >= client_count else "Client"

        # Assign speakers based on the dominant speaker and conversation flow
        current_speaker = "Salesperson" if dominant_speaker == "Salesperson" else "Client"
        switch_speaker = lambda speaker: "Client" if speaker == "Salesperson" else "Salesperson"

        # Process each segment to build the dialog
        for index, segment in enumerate(segments):
            text = segment["text"]
            start_time = segment["start"]
            end_time = segment["end"]

            # Switch speakers periodically for a more natural flow
            if index % 2 == 1:
                current_speaker = switch_speaker(current_speaker)

            # Analyze sentiment using the pre-trained model
            sentiment_result = sentiment_analyzer(text)[0]
            sentiment = sentiment_result["label"]

            dialog.append({
                "Speaker": current_speaker,
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
