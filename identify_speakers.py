import os
import subprocess
from pyannote.audio import Pipeline
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pyannote.core import Annotation

def initialize_pipeline(hugging_face_access_token):
    """
    Initialize the speaker diarization pipeline.
    """
    try:
        print("Loading the speaker diarization pipeline...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hugging_face_access_token
        )
        print("Pipeline loaded successfully!")
        return pipeline
    except Exception as e:
        print(f"Error loading pipeline: {e}")
        return None

def preprocess_audio(input_path, output_path):
    """
    Preprocess audio using FFmpeg: convert to mono, resample to 16kHz,
    apply highpass and lowpass filters.
    """
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            "-af", "loudnorm, highpass=f=200, lowpass=f=3000",
            "-y",
            output_path
        ]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"Preprocessed {input_path} to {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error preprocessing {input_path}: {e}")
        return False

def refine_diarization(diarization):
    """
    Refine diarization by merging short segments and assigning consistent labels.
    """
    refined_diarization = Annotation()
    speaker_mapping = {}
    speaker_count = 0

    for segment, _, label in diarization.itertracks(yield_label=True):
        if segment.duration < 0.25:  # Ignore very short segments (0.25 best result)
            continue

        if label not in speaker_mapping:
            speaker_mapping[label] = f"SPEAKER_{speaker_count:02d}"
            speaker_count += 1

        refined_diarization[segment] = speaker_mapping[label]

    return refined_diarization

def plot_diarization(diarization, title, output_path):
    """
    Plot speaker diarization results with consistent labels and colors, save to a file.
    """
    if diarization is None:
        print("No diarization data to plot.")
        return

    plt.figure(figsize=(12, 8))

    speakers = sorted(set(label for _, _, label in diarization.itertracks(yield_label=True)))
    colors = {speaker: plt.cm.tab10(idx % 10) for idx, speaker in enumerate(speakers)}

    for segment, _, label in diarization.itertracks(yield_label=True):
        plt.plot(
            [segment.start, segment.end],
            [label, label],
            linewidth=8,
            color=colors[label],
            solid_capstyle="butt"
        )
        plt.plot(segment.start, label, "o", color=colors[label])
        plt.plot(segment.end, label, "o", color=colors[label])

    legend_patches = [Patch(color=colors[speaker], label=speaker) for speaker in speakers]
    plt.legend(handles=legend_patches, loc="upper left", fontsize=12)

    plt.title(title, fontsize=16)
    plt.xlabel("Time (s)", fontsize=14)
    plt.ylabel("Speakers", fontsize=14)
    plt.yticks(range(len(speakers)), speakers, fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()

    plt.savefig(output_path)
    print(f"Graph saved to: {output_path}")

    plt.close()
