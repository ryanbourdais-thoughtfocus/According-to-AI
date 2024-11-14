import os
import json
from analysis import generate_analysis_report
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Set the project root to the parent directory of src
project_root = os.path.dirname(os.path.abspath(__file__ + "/.."))

# Define paths for folders
cleaned_text_folder = os.path.join(project_root, "cleaned_text")
analysis_report_folder = os.path.join(project_root, "analysis_report")

# Debug prints to confirm paths
print(f"Project Root: {project_root}")
print(f"Cleaned Text Folder: {cleaned_text_folder}")
print(f"Analysis Report Folder: {analysis_report_folder}")

# Ensure the analysis_report folder exists
os.makedirs(analysis_report_folder, exist_ok=True)

# Step 1: Find the latest modified JSON transcript in the cleaned_text folder
try:
    # List all JSON files in the cleaned_text directory
    labeled_files = [f for f in os.listdir(cleaned_text_folder) if f.endswith(".json")]
    
    # Debug print to show found files
    print(f"JSON Files Found: {labeled_files}")

    # Sort files by modification time, with the latest file first
    labeled_files.sort(key=lambda x: os.path.getmtime(os.path.join(cleaned_text_folder, x)), reverse=True)
    
    # Get the latest modified file
    latest_labeled_file = labeled_files[0] if labeled_files else None
except IndexError:
    print("No JSON transcripts found in the cleaned_text folder.")
    exit(1)

# Step 2: Analyze the latest labeled file
if latest_labeled_file:
    print(f"Analyzing the latest processed transcript: {latest_labeled_file}")

    # Load the labeled conversation from the JSON file
    cleaned_text_path = os.path.join(cleaned_text_folder, latest_labeled_file)
    with open(cleaned_text_path, "r", encoding="utf-8") as file:
        conversation = json.load(file)

    # Generate analysis report for the loaded JSON file
    report = generate_analysis_report(conversation)

    # Save the analysis report in the analysis_report folder with "_report" appended to filename
    report_filename = f"{os.path.splitext(latest_labeled_file)[0]}_report.json"
    report_file_path = os.path.join(analysis_report_folder, report_filename)
    with open(report_file_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    print(f"Analysis report saved to {report_file_path}")
else:
    print("No labeled transcript file found to analyze.")
