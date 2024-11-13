import os
import json
import dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
dotenv.load_dotenv()

# Initialize ChatOpenAI model with environment variable for API key
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name="gpt-3.5-turbo", max_tokens=500)

# Function to generate the refined prompt for speaker identification
def generate_prompt(transcript_chunk, previous_speakers):
    prev_speakers_text = ", ".join(previous_speakers)
    return f"""You are analyzing a conversation transcript with multiple participants. Identify each speaker as "employee" or "client" with unique identifiers (e.g., "employee 1," "client 2") consistently across the transcript.

Guidelines:
- Use unique identifiers for each speaker across the conversation.
- Known speakers so far: {prev_speakers_text}.
- Format strictly as:
[
    {{"speaker": "client 1", "text": "Question about the product."}},
    {{"speaker": "employee 1", "text": "Answer regarding the product."}}
]

Transcript:
{transcript_chunk}

Provide the labeled conversation as JSON:
"""

# Function to split the transcript into chunks
def split_transcript(transcript, max_length=800):
    """Splits the transcript into chunks without overlapping text."""
    lines = transcript.split("\n")
    chunks = []
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk.strip())
            current_chunk = line
        else:
            current_chunk += "\n" + line
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

# Track known speakers across chunks
known_speakers = {}

def label_speakers_consistently(chunk_result):
    """Ensure consistent speaker labeling by mapping generic labels to known speakers."""
    for entry in chunk_result:
        speaker = entry['speaker']
        if speaker not in known_speakers and speaker not in ["client", "employee"]:
            # New unique speaker found, add to known speakers
            known_speakers[speaker] = speaker
        elif speaker in ["client", "employee"]:
            # Map generic "client"/"employee" to a known speaker
            entry['speaker'] = list(known_speakers.keys())[0] if known_speakers else speaker

    return chunk_result

# Function to identify speakers in the transcript with consistent labeling
def identify_speakers_in_transcript(transcript):
    """Processes the transcript in chunks and aggregates results with unique speaker labels."""
    transcript_chunks = split_transcript(transcript)
    labeled_transcript = []
    context = ""  # Start with an empty context

    for chunk in transcript_chunks:
        # Generate the prompt with the current chunk and context
        formatted_prompt = generate_prompt(chunk, known_speakers)
        
        # Run the prompt through the model
        response = llm.invoke(formatted_prompt)
        response_text = response.content
        
        # Debug: print the response to ensure correct format
        print("Model Response for Chunk:", response_text)  # Debug output to inspect model output
        
        # Try to parse the response as JSON and add to the labeled transcript
        try:
            chunk_result = json.loads(response_text)
            chunk_result = label_speakers_consistently(chunk_result)
            labeled_transcript.extend(chunk_result)
            
            # Update context with the last few lines of the current chunk
            context = "\n".join([entry["text"] for entry in chunk_result[-3:]])  # Last 3 lines as context
        except json.JSONDecodeError:
            print("Error: Could not parse model response as JSON for this chunk.")
    
    # Remove duplicates from labeled_transcript
    unique_transcript = []
    seen_texts = set()
    for entry in labeled_transcript:
        if entry["text"] not in seen_texts:
            seen_texts.add(entry["text"])
            unique_transcript.append(entry)
    
    return unique_transcript

# Function to extract main topic for filename
def extract_main_topic(transcript):
    """Uses the model to identify the main topic of the conversation."""
    prompt = f"Identify the main topic of the following conversation in a single word or short phrase:\n\n{transcript}\n\nTopic:"
    response = llm.invoke(prompt)
    main_topic = response.content.strip().lower().replace(" ", "_")
    sanitized_topic = main_topic.replace("/", "_").replace("\\", "_")
    return sanitized_topic or "general_topic"

# Function to save labeled transcript with topic-based filename
def save_labeled_transcript_with_topic(labeled_transcript, raw_transcript, folder="cleaned_text"):
    """Saves the labeled transcript to a JSON file in cleaned_text folder, named by main topic."""
    # Determine main topic for filename
    main_topic = extract_main_topic(raw_transcript)
    filename = f"{main_topic}_labeled_transcript.json"
    
    # Ensure the folder exists
    os.makedirs(folder, exist_ok=True)
    
    # Define the full file path
    file_path = os.path.join(folder, filename)
    
    # Write the transcript to the JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(labeled_transcript, f, indent=4, ensure_ascii=False)
    
    print(f"Labeled transcript saved to {file_path}")
