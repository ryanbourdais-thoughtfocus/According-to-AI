import os
import json
from data_preprocessing import identify_speakers_in_transcript, save_labeled_transcript_with_topic
from analysis import generate_analysis_report
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Define paths for folders and specific input file
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_folder = os.path.join(project_root, "data")
cleaned_text_folder = os.path.join(project_root, "cleaned_text")
analysis_report_folder = os.path.join(project_root, "analysis_report")
transcript_file = os.path.join(data_folder, "transcript.txt")

# Ensure output directories exist
os.makedirs(cleaned_text_folder, exist_ok=True)
os.makedirs(analysis_report_folder, exist_ok=True)

# Step 1: Process the specific raw transcript file
if os.path.exists(transcript_file):  # Check if 'transcript.txt' exists
    print(f"Processing raw transcript: transcript.txt")
    
    # Read the raw transcript
    with open(transcript_file, "r", encoding="utf-8") as file:
        raw_text = file.read()
    
    # Process the transcript to identify speakers and label the conversation
    labeled_transcript = identify_speakers_in_transcript(raw_text)
    
    # Save the labeled transcript with a topic-based filename in cleaned_text and capture the filename
    labeled_filename = save_labeled_transcript_with_topic(labeled_transcript, raw_text, folder=cleaned_text_folder)
else:
    print("No transcript.txt found in the data folder.")
    exit(1)  # Exit if the required file is not found

# Step 2: Generate analysis report for the newly saved JSON file only
print(f"Analyzing processed transcript: {labeled_filename}")
        
# Load the labeled conversation from the JSON file
cleaned_text_path = os.path.join(cleaned_text_folder, labeled_filename)
with open(cleaned_text_path, "r", encoding="utf-8") as file:
    conversation = json.load(file)

# Generate analysis report
report = generate_analysis_report(conversation)

# Save the analysis report in the analysis_report folder with "_report" appended to filename
report_filename = f"{os.path.splitext(labeled_filename)[0]}_report.json"
report_file_path = os.path.join(analysis_report_folder, report_filename)
with open(report_file_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=4, ensure_ascii=False)

print(f"Analysis report saved to {report_file_path}")
