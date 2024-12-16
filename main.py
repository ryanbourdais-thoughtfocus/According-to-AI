import os
import dotenv
from identify_speakers import initialize_pipeline, preprocess_audio, refine_diarization, plot_diarization
#from transcript import process_transcript
from pyannote.core import Annotation

dotenv.load_dotenv()

HUGGING_FACE_ACCESS_TOKEN = os.environ.get("HUGGING_FACE_ACCESS_TOKEN")

DATA_FOLDER = "./data/audio"
PROCESSED_FOLDER = "./data/processed"
GRAPH_FOLDER = "./data/graph"
TRANSCRIPT_FOLDER = "./transcript"
RTTM_FOLDER = "./data/rttm"

for folder in [DATA_FOLDER, PROCESSED_FOLDER, GRAPH_FOLDER, TRANSCRIPT_FOLDER, RTTM_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def save_rttm(refined_diarization, base_name):
    """
    Save diarization results to an RTTM file.
    """
    rttm_path = os.path.join(RTTM_FOLDER, f"{base_name}.rttm")
    try:
        with open(rttm_path, "w") as rttm_file:
            refined_diarization.write_rttm(rttm_file)
        print(f"RTTM file saved to {rttm_path}")
    except Exception as e:
        print(f"Error saving RTTM file for {base_name}: {e}")

def process_file(input_file, pipeline, title, participants, location="Video Call"):
    """
    Process an audio file to perform diarization, plot results, and generate a transcript.
    """
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    processed_file = os.path.join(PROCESSED_FOLDER, f"{base_name}.wav")

    if not preprocess_audio(input_file, processed_file):
        print(f"Skipping {input_file} due to preprocessing errors.")
        return

    try:
        print(f"Processing file: {processed_file}")

        diarization = pipeline(processed_file)

        refined_diarization = refine_diarization(diarization)

        save_rttm(refined_diarization, base_name)

        graph_path = os.path.join(GRAPH_FOLDER, f"{base_name}.png")
        plot_diarization(refined_diarization, title=f"Speaker Diarization - {base_name}", output_path=graph_path)

        transcript_path = os.path.join(TRANSCRIPT_FOLDER, f"{base_name}.json")
        process_transcript(base_name, refined_diarization, processed_file, title, participants, transcript_path, location)

        print(f"Finished processing {processed_file}. Graph saved to {graph_path}, transcript saved to transcript_path, RTTM saved to {RTTM_FOLDER}.\n")

    except Exception as e:
        print(f"Error processing {processed_file}: {e}")

if __name__ == "__main__":
    print("Initializing the pipeline...")
    pipeline = initialize_pipeline(HUGGING_FACE_ACCESS_TOKEN)

    if pipeline is None:
        print("Failed to initialize the pipeline. Exiting.")
        exit(1)

    MEETING_TITLE = "Sales Pitch for AI Solution"
    PARTICIPANTS = ["Salesperson", "Client"]

    print(f"Looking for .wav files in folder: {DATA_FOLDER}")

    for file_name in os.listdir(DATA_FOLDER):
        if file_name.endswith(".wav"):
            input_path = os.path.join(DATA_FOLDER, file_name)
            process_file(input_path, pipeline, MEETING_TITLE, PARTICIPANTS)

    print("Processing complete.")
