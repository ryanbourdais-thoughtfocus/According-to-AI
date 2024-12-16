import os
import json
import whisper
import soundfile as sf
import torch
from pyannote.audio import Audio

whisper_model = whisper.load_model("base")


def preprocess_audio_segment(segment, audio_file):
    """
    Transcribe a segment of audio using the Whisper model.
    """
    audio_helper = Audio(sample_rate=16000)

    try:
        waveform, sample_rate = audio_helper.crop(audio_file, segment)
        if isinstance(waveform, torch.Tensor):
            waveform = waveform.numpy()

        if waveform.shape[1] == 0:
            print(f"Skipping empty or out-of-bound segment: {segment}")
            return ""

        temp_file = "temp_segment.wav"
        sf.write(temp_file, waveform.T, int(sample_rate), format="WAV")
        result = whisper_model.transcribe(temp_file, language="en")
        transcript = result["text"]
        os.remove(temp_file)

        return transcript.strip()
    except Exception as e:
        print(f"Error processing segment {segment}: {e}")
        return ""


def merge_consecutive_statements(dialog):
    """
    Merge consecutive statements from the same speaker to avoid duplication.
    """
    if not dialog:
        return []

    merged_dialog = [dialog[0]]
    for current in dialog[1:]:
        last = merged_dialog[-1]
        if last["Speaker"] == current["Speaker"]:
            last["Statement"] += " " + current["Statement"]
        else:
            merged_dialog.append(current)

    return merged_dialog


def generate_transcript(diarization, audio_file, title, participants, location="Video Call"):
    """
    Generate a JSON transcript from diarization and audio file.
    """
    dialog = []
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        statement = preprocess_audio_segment(segment, audio_file)
        if statement and "Error" not in statement:
            dialog.append({"Speaker": speaker, "Statement": statement})

    dialog = merge_consecutive_statements(dialog)

    transcript = {
        "Meeting": {
            "Title": title,
            "Date": "",  
            "Time": "",  
            "Location": location,
            "Participants": participants,
            "Dialog": dialog,
            "ClosingNote": "The meeting concludes. Details may need to be followed up.",
        }
    }

    return transcript


def save_transcript(transcript, output_path):
    """
    Save the transcript to a JSON file.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(transcript, f, indent=4)
        print(f"Transcript saved successfully to: {output_path}")
    except Exception as e:
        print(f"Error saving transcript: {e}")
        print(f"Transcript content: {transcript}")


def process_transcript(base_name, diarization, processed_file, title, participants, transcript_path, location="Video Call"):
    """
    Process the diarization results and generate a transcript JSON.
    """
    try:
        print(f"Generating transcript for {base_name}...")
        transcript = generate_transcript(diarization, processed_file, title, participants, location)
        save_transcript(transcript, transcript_path)
    except Exception as e:
        print(f"Error processing transcript for {base_name}: {e}")
