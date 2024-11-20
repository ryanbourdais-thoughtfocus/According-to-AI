from langchain_openai import ChatOpenAI
import json
import time
import os
import dotenv

dotenv.load_dotenv()

# Initialize the ChatOpenAI model
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name="gpt-3.5-turbo", max_tokens=300, request_timeout=30)


def retry_api_call(prompt, retries=3, delay=5):
    """Retry wrapper for API calls to handle timeouts and failures."""
    for attempt in range(retries):
        try:
            response = llm.invoke(prompt)
            return response
        except Exception as e:
            print(f"API call failed on attempt {attempt + 1}: {e}")
            time.sleep(delay)
    return {"error": "API call failed after retries"}


def calculate_dynamic_chunk_size(conversation, max_tokens=300):
    """Calculate an optimal chunk size based on the model's token limits."""
    avg_tokens_per_entry = 50  # Approximate token size per dialog entry
    return max(1, min(len(conversation), max_tokens // avg_tokens_per_entry))


def chunk_conversation(conversation, chunk_size):
    """Break down a conversation into manageable chunks."""
    return [conversation[i:i + chunk_size] for i in range(0, len(conversation), chunk_size)]


def analyze_conversation(question, conversation_chunk):
    """Analyze a specific chunk of conversation."""
    prompt = f"""
    You are analyzing a customer service conversation. Below is a portion of the transcript. Please answer the question based on the conversation provided:

    Conversation: {conversation_chunk}

    Question: {question}

    Answer:"""
    response = retry_api_call(prompt)
    if "error" in response:
        return response
    return response.content.strip()


def overall_meeting_summary(conversation):
    """Generate a high-level summary of the meeting."""
    chunk_size = calculate_dynamic_chunk_size(conversation)
    chunks = chunk_conversation(conversation, chunk_size)
    summaries = [
        analyze_conversation("Summarize this portion of the conversation.", chunk)
        for chunk in chunks
    ]
    return " ".join(summaries)


def analyze_speaker_contributions(conversation):
    """Analyze contributions by each speaker."""
    speakers = {entry["Speaker"] for entry in conversation}
    contributions = {}
    for speaker in speakers:
        speaker_statements = [entry["Statement"] for entry in conversation if entry["Speaker"] == speaker]
        contributions[speaker] = analyze_conversation(f"Analyze the contributions made by {speaker}.", speaker_statements)
    return contributions


def speaker_interactions(conversation):
    """Analyze interactions between speakers."""
    return analyze_conversation("Describe interactions between participants (e.g., agreements, disagreements, responses).", conversation)


def detailed_questions(conversation):
    """Ask detailed questions and return answers."""
    sections = {
        "Call Structure": "How was the call structured?",
        "Pitch or Sell": "Was a product or service pitched or sold? If so, provide details.",
        "Call Purpose": "What was the main purpose of the call?",
        "Customer Feedback": "What specific feedback did the customer provide during the call?",
        "Our Response": "How did we respond to the customer's feedback?",
        "Action Items": "What are the next steps or action items resulting from the call?",
        "Missed Opportunities": "Were there any missed opportunities during the call? If so, provide details.",
        "Customer Sentiment": "What was the overall sentiment of the customer during the conversation?",
        "Negative Sentiment": "What factors contributed to any negative sentiment during the call?",
        "Pitched and Received": "What was pitched to the customer, and how was it received?",
        "CRM/Deal Updates": "What CRM or deal-relevant updates can be extracted from this conversation?",
        "Customer Interest": "On a scale of 1 to 10, how interested was the customer in the product or service?",
        "Language Barrier": "Were there any language barriers during the call?",
        "Sales Challenges": "What challenges did the sales representative face during the call?",
        "Customer Pain Points": "What pain points or concerns did the customer express?"
    }
    responses = {}
    for section, question in sections.items():
        responses[section] = analyze_conversation(question, conversation)
    return responses


def rate_sales_pitch(conversation):
    """Rate the sales pitch based on clarity, relevance, persuasiveness, and responsiveness."""
    prompt = f"""
    Rate the sales pitch in the conversation based on:
    - Clarity
    - Relevance
    - Persuasiveness
    - Responsiveness

    Provide the ratings in JSON format, with a score out of 10 and a brief explanation for each criterion:
    {{
        "clarity": {{"score": "<score>/10", "explanation": "<explanation>"}},
        "relevance": {{"score": "<score>/10", "explanation": "<explanation>"}},
        "persuasiveness": {{"score": "<score>/10", "explanation": "<explanation>"}},
        "responsiveness": {{"score": "<score>/10", "explanation": "<explanation>"}},
        "overall": {{"score": "<score>/10", "explanation": "<explanation>"}}
    }}
    """
    response = retry_api_call(prompt)
    if "error" in response:
        return response
    try:
        return json.loads(response.content.strip())
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return {"error": "Failed to parse sales pitch rating"}


def generate_analysis_report(conversation):
    """Generate a comprehensive analysis report."""
    try:
        return {
            "Overall Meeting Summary": overall_meeting_summary(conversation),
            "Speaker Contributions": analyze_speaker_contributions(conversation),
            "Speaker Interactions": speaker_interactions(conversation),
            **detailed_questions(conversation),
            "Sales Pitch Rating": rate_sales_pitch(conversation),
        }
    except Exception as e:
        print(f"Error generating analysis report: {e}")
        return {"error": "Failed to generate report"}
