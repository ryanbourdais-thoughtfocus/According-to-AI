import os
import json
from data_preprocessing import identify_speakers_in_transcript, save_labeled_transcript_with_topic
from analysis import generate_analysis_report

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_folder = os.path.join(project_root, "data")
cleaned_text_folder = os.path.join(project_root, "cleaned_text")
analysis_report_folder = os.path.join(project_root, "analysis_report")

os.makedirs(cleaned_text_folder, exist_ok=True)
os.makedirs(analysis_report_folder, exist_ok=True)

for filename in os.listdir(data_folder):
    if filename.endswith(".txt"):  
        print(f"\nProcessing raw transcript: {filename}")
        
        raw_transcript_path = os.path.join(data_folder, filename)
        try:
            with open(raw_transcript_path, "r", encoding="utf-8") as file:
                raw_text = file.read()
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue
        
        try:
            labeled_transcript = identify_speakers_in_transcript(raw_text)
            save_labeled_transcript_with_topic(labeled_transcript, raw_text, folder=cleaned_text_folder)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

for filename in os.listdir(cleaned_text_folder):
    if filename.endswith(".json"):
        print(f"\nAnalyzing processed transcript: {filename}")
        
        cleaned_text_path = os.path.join(cleaned_text_folder, filename)
        try:
            with open(cleaned_text_path, "r", encoding="utf-8") as file:
                conversation = json.load(file)
        except Exception as e:
            print(f"Error reading labeled transcript {filename}: {e}")
            continue
        
        try:
            report = generate_analysis_report(conversation)
            
            report_filename = f"{os.path.splitext(filename)[0]}_report.json"
            report_file_path = os.path.join(analysis_report_folder, report_filename)
            with open(report_file_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4, ensure_ascii=False)
            print(f"Analysis report saved to {report_file_path}")
        except Exception as e:
            print(f"Error generating analysis report for {filename}: {e}")
            continue
