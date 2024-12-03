import os
import json
from interactionReviewWithGpt.analysis import generate_analysis_report
import dotenv
 

dotenv.load_dotenv()
 
# # Set project directories
# project_root = os.path.dirname(os.path.abspath(__file__ + "/.."))
# cleaned_text_folder = os.path.join(project_root, "cleaned_text")
# analysis_report_folder = os.path.join(project_root, "analysis_report")
 
# Ensure the output folder exists
# os.makedirs(analysis_report_folder, exist_ok=True)
 
 
def load_latest_file(folder):
    """Load the latest JSON file from the specified folder."""
    try:
        files = [f for f in os.listdir(folder) if f.endswith(".json")]
        if not files:
            raise FileNotFoundError("No JSON files found in the specified folder.")
       
        # Sort files by modification time, newest first
        files.sort(key=lambda x: os.path.getmtime(os.path.join(folder, x)), reverse=True)
        return os.path.join(folder, files[0])
 
    except Exception as e:
        print(f"Error loading JSON files: {e}")
        exit(1)
 
 
def validate_json_structure(data):
    """Validate the structure of the input JSON."""
    try:
        if "Meeting" not in data or "Dialog" not in data["Meeting"]:
            raise KeyError("Required key 'Meeting.Dialog' is missing in the JSON file.")
       
        conversation = data["Meeting"]["Dialog"]
        if not isinstance(conversation, list) or not all(isinstance(entry, dict) for entry in conversation):
            raise ValueError("'Dialog' must be a list of dictionaries.")
 
        return conversation
 
    except Exception as e:
        print(f"Error validating JSON structure: {e}")
        exit(1)
 
 
def main():
    print("Loading the latest transcript...")
    
    try:
        with open("conversation.json", "r", encoding="utf-8") as file:
            data = json.load(file)
 
        conversation = validate_json_structure(data)
 
        print("Generating analysis report...")
        report = generate_analysis_report(conversation)
        return report
 
       
 
    except Exception as e:
        print(f"Error processing the file: {e}")
        exit(1)