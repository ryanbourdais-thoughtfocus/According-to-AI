import os
from pyannote.core import Annotation, Segment
from pyannote.metrics.diarization import DiarizationErrorRate
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pyannote.metrics")


def load_rttm_as_annotation(rttm_file):
    """
    Load an RTTM file and convert it to a pyannote.core.Annotation object.
    """
    annotation = Annotation()
    try:
        with open(rttm_file, 'r') as file:
            for line in file:
                if not line.startswith("SPEAKER"):
                    continue
                parts = line.strip().split()
                start_time = float(parts[3])
                duration = float(parts[4])
                speaker = parts[7]
                segment = Segment(start_time, start_time + duration)
                annotation[segment] = speaker
        return annotation
    except Exception as e:
        print(f"Error reading RTTM file {rttm_file}: {e}")
        return None

def calculate_der_and_jer(reference_folder, hypothesis_folder):
    """
    Calculate Diarization Error Rate (DER) and Jaccard Error Rate (JER) for all files.
    """
    der_metric = DiarizationErrorRate()

    for ref_file in os.listdir(reference_folder):
        if not ref_file.endswith(".rttm"):
            continue

        ref_path = os.path.join(reference_folder, ref_file)
        hyp_path = os.path.join(hypothesis_folder, ref_file)

        if not os.path.isfile(hyp_path):
            print(f"Missing hypothesis file for: {ref_file}")
            continue

        # Load reference and hypothesis annotations
        reference_annotation = load_rttm_as_annotation(ref_path)
        hypothesis_annotation = load_rttm_as_annotation(hyp_path)

        if reference_annotation is None or hypothesis_annotation is None:
            print(f"Skipping {ref_file}: Unable to load annotations.")
            continue

        # Calculate DER
        der = der_metric(reference_annotation, hypothesis_annotation)

        # Calculate JER manually
        ref_timeline = reference_annotation.get_timeline().support()
        hyp_timeline = hypothesis_annotation.get_timeline().support()

        # Manually calculate intersection and union
        intersection = ref_timeline.crop(hyp_timeline)
        union = ref_timeline.union(hyp_timeline)

        jaccard_index = intersection.duration() / union.duration() if union.duration() > 0 else 0
        jer = 1 - jaccard_index

        print(f"File: {ref_file}")
        print(f"  Diarization Error Rate (DER): {der * 100:.2f}%")
        print(f"  Jaccard Error Rate (JER): {jer * 100:.2f}%")
        print("-" * 50)

if __name__ == "__main__":
    # Folder paths
    reference_folder = "./data/reference"
    hypothesis_folder = "./data/rttm"

    # Check if folders exist
    if not os.path.exists(reference_folder):
        print(f"Reference folder '{reference_folder}' does not exist. Exiting.")
        exit(1)
    if not os.path.exists(hypothesis_folder):
        print(f"Hypothesis folder '{hypothesis_folder}' does not exist. Exiting.")
        exit(1)

    print("Calculating metrics...")
    calculate_der_and_jer(reference_folder, hypothesis_folder)
    print("Metrics calculation complete.")
