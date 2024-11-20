import logging
import os
import azure.functions as func
import tempfile
import subprocess
import json
import uuid
import whisper
import torch
import openai
from openai import OpenAI

# Set your OpenAI API key
openai_api_key = os.environ.get("OPENAI_API_KEY")

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

        # Get the entire transcribed text
        full_text = result.get("text", "")
        logging.info("Transcription completed.")
    except Exception as e:
        logging.error(f"Error during transcription: {str(e)}")
        return func.HttpResponse(f"Error during transcription: {str(e)}", status_code=500)

    # Use OpenAI to analyze the transcribed text
    try:
        logging.info("Sending transcription to OpenAI for analysis...")
        client = OpenAI(api_key = openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": (
                                "Analyze the following meeting transcript. Identify the speakers as either 'Salesperson' or 'Client' and "
                                "determine the sentiment of each statement. Provide the analysis in JSON format with each statement "
                                "including 'Speaker', 'Statement', and 'Sentiment'.\n\n"
                                f"Transcript:\n{full_text}"
                            ),
                },
            ],
        )

        response_message = response.choices[0].message.content
        print(response_message)
        
        analysis = response_message
        logging.info("OpenAI analysis completed.")
    except Exception as e:
        logging.error(f"Error during OpenAI analysis: {str(e)}")
        return func.HttpResponse(f"Error during OpenAI analysis: {str(e)}", status_code=500)

    # Construct the final JSON structure
    response_data = {
        "Meeting": {
            "Title": "Sales Pitch for AI Solution",
            "Date": "2024-11-19",
            "Time": "2:00 PM",
            "Location": "Client's Office / Video Call",
            "Participants": ["Salesperson: Alex Johnson", "Client: Jordan Smith"],
            "Dialog": json.loads(analysis),
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
