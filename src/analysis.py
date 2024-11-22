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


def preprocess_conversation(conversation):
    """Preprocess conversation for better LLM analysis."""
    normalized = []
    for entry in conversation:
        entry["Speaker"] = entry["Speaker"].strip().lower()
        entry["Statement"] = entry["Statement"].strip()
        normalized.append(entry)
    return normalized


def calculate_dynamic_chunk_size(conversation, max_tokens=300, avg_tokens_per_entry=40):
    """Adjust chunk size based on average entry size and token limits."""
    return max(1, min(len(conversation), max_tokens // avg_tokens_per_entry))


def chunk_conversation(conversation, chunk_size, overlap=2):
    """Break down a conversation into manageable chunks with overlap."""
    chunks = []
    for i in range(0, len(conversation), chunk_size - overlap):
        chunks.append(conversation[i:i + chunk_size])
    return chunks


def analyze_conversation(question, conversation_chunk):
    """Analyze a specific chunk of conversation with refined prompts."""
    prompt = f"""
    You are an expert in business communication analysis. Below is a portion of a meeting transcript between employees and clients.
    Please analyze the conversation and answer the question in a structured and concise manner:

    Conversation: {conversation_chunk}

    Question: {question}

    Guidelines:
    - Provide actionable insights.
    - Highlight key moments.
    - Structure your response logically.

    Answer:
    """
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
        "Customer Pain Points": "What pain points or concerns did the customer express?",
        "Salesperson Pitch/Sales Quality Rating": "Evaluate the salesperson's pitch quality. Was it clear, engaging, and persuasive? Provide specific strengths and areas for improvement."
    }
    responses = {}
    for section, question in sections.items():
        responses[section] = analyze_conversation(question, conversation)
    return responses


def rate_call(detailed_analysis):
    """
    Rate the call based on clarity, relevance, persuasiveness, responsiveness, customer sentiment, and customer interest.
    """
    try:
        # Extract and validate properties
        pitch_quality = detailed_analysis.get("Salesperson Pitch/Sales Quality Rating", "").lower()
        customer_sentiment = detailed_analysis.get("Customer Sentiment", "").lower()
        customer_interest_raw = detailed_analysis.get("Customer Interest", "0")

        # Validate Customer Interest
        try:
            customer_interest = int(customer_interest_raw)
        except ValueError:
            print(f"Warning: Unable to parse Customer Interest '{customer_interest_raw}'. Defaulting to 0.")
            customer_interest = 0

        # Assign scores based on extracted properties
        scores = {
            "Clarity": 8 if "clear" in pitch_quality else 6,
            "Relevance": 8 if "relevant" in customer_sentiment else 5,
            "Persuasiveness": 9 if "persuasive" in pitch_quality else 6,
            "Responsiveness": 7 if "responsive" in customer_sentiment else 5,
            "Customer Interest": customer_interest
        }

        # Compute weighted overall score
        overall_score = round(
            (scores["Clarity"] * 0.25) +
            (scores["Relevance"] * 0.2) +
            (scores["Persuasiveness"] * 0.25) +
            (scores["Responsiveness"] * 0.2) +
            (scores["Customer Interest"] * 0.1)
        )

        # Generate explanation
        explanation = (
            f"The call scored {overall_score}/10 based on clarity, relevance, "
            f"persuasiveness, responsiveness, and customer interest."
        )

        return {
            "Scores": scores,
            "Overall Score": f"{overall_score}/10",
            "Explanation": explanation
        }

    except Exception as e:
        print(f"Error in rating call: {e}")
        return {"error": "Failed to rate the call"}


def generate_analysis_report(conversation):
    """Generate a comprehensive analysis report."""
    try:
        conversation = preprocess_conversation(conversation)

        # Generate detailed questions analysis
        detailed_analysis = detailed_questions(conversation)

        # Rate the call
        call_rating = rate_call(detailed_analysis)

        # Compile full report
        return {
            "Overall Meeting Summary": overall_meeting_summary(conversation),
            "Speaker Contributions": analyze_speaker_contributions(conversation),
            "Speaker Interactions": speaker_interactions(conversation),
            **detailed_analysis,
            "Call Rating": call_rating
        }
    except Exception as e:
        print(f"Error generating analysis report: {e}")
        return {"error": "Failed to generate report"}
