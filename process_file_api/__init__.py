import warnings
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
from concurrent.futures import ThreadPoolExecutor

# Suppress specific FutureWarning from torch
warnings.filterwarnings("ignore", category=FutureWarning, module="whisper")

# Set your OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

def transcribe_audio_with_whisper(model, audio_path):
    try:
        logging.info("Starting transcription with Whisper...")
        result = model.transcribe(
            audio_path,
            no_speech_threshold=0.1,
            logprob_threshold=-1.0,
            condition_on_previous_text=True
        )
        full_text = result.get("text", "")
        logging.info("Transcription completed.")
        return full_text
    except Exception as e:
        logging.error(f"Error during transcription: {str(e)}")
        raise

def analyze_text_with_openai(full_text):
    try:
        logging.info("Sending transcription to OpenAI for analysis...")
        client = OpenAI(api_key = openai.api_key)

                # Refined prompt with examples
        prompt = (
            "Analyze the following meeting transcript. Assign each statement to either the 'Salesperson' or the 'Client' "
            "based on the content of the statement. The salesperson typically discusses solutions, asks questions, "
            "and drives the conversation forward, while the client describes problems, asks for clarification, "
            "or reacts to the salesperson. Provide the analysis in JSON format with each statement including 'Speaker', "
            "'Statement', and 'Sentiment'.\n\n"
            f"Transcript:\n{full_text}"
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user","content": prompt},
            ],
        )
        response_message = response.choices[0].message.content.strip()
        logging.info("OpenAI analysis completed.")
        return response_message
    except Exception as e:
        logging.error(f"Error during OpenAI analysis: {str(e)}")
        raise

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
        subprocess.run(ffmpeg_command, check=True, capture_output=True)
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

    # Run transcription and OpenAI analysis concurrently
    try:
        with ThreadPoolExecutor() as executor:
            future_transcription = executor.submit(transcribe_audio_with_whisper, model, temp_audio_path)
            full_text = future_transcription.result()

            future_analysis = executor.submit(analyze_text_with_openai, full_text)
            analysis = future_analysis.result()

        logging.info("Transcription and analysis completed.")

        # Validate the analysis response
        try:
            # Assuming the analysis response is a JSON string with the "Analysis" key
            analysis_data = json.loads(analysis)
            dialog = analysis_data
        except json.JSONDecodeError as e:
            logging.error(f"JSONDecodeError: {str(e)}. Analysis response: {analysis}")
            return func.HttpResponse("Error: Invalid JSON format returned by OpenAI.", status_code=500)

    except Exception as e:
        return func.HttpResponse(f"Error during processing: {str(e)}", status_code=500)

    # Construct the final JSON structure
    response_data = {
        "Meeting": {
            "Title": "Sales Pitch for AI Solution",
            "Date": "",
            "Time": "",
            "Location": "Video Call",
            "Participants": ["Salesperson", "Client"],
            "Dialog": dialog,
            "ClosingNote": "The meeting concludes. Details may need to be followed up.",
            "PerformanceSummary": {
                "OverallPerformance": "",
                "Strengths": [],
                "AreasForImprovement": [],
                "ClientResponse": ""
            }
        }
    }

    return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")
