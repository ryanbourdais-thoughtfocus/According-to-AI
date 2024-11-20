import json
import os
import json
from langchain_openai import ChatOpenAI
import dotenv

dotenv.load_dotenv()
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model_name="gpt-3.5-turbo", max_tokens=300)


 
def analyze_conversation(question, conversation):
    prompt = f"""
    You are analyzing a multi-speaker meeting transcript. Below is the conversation in JSON format. Based on this, please answer the following question:
 
    Conversation: {conversation}
 
    Question: {question}
 
    Answer:"""
    response = llm.invoke(prompt)
    return response.content.strip()
 
def analyze_speaker_contributions(conversation):
    """Analyze each speaker's contributions in the conversation."""
    speakers = {entry["speaker"] for entry in conversation}  # Identify unique speakers
    contributions = {}
    for speaker in speakers:
        speaker_convo = [entry["text"] for entry in conversation if entry["speaker"] == speaker]
        prompt = f"Analyze the contributions made by {speaker} in the following statements:\n{speaker_convo}\nProvide insights on tone, engagement, and main points covered."
        response = llm.invoke(prompt)
        contributions[speaker] = response.content.strip()
    return contributions
 
def speaker_interaction_analysis(conversation):
    """Analyze interactions between speakers, such as agreements, disagreements, or direct responses."""
    prompt = f"""
    You are analyzing the interactions in a multi-speaker conversation. Identify moments of agreement, disagreement, or direct responses between participants.
   
    Conversation: {conversation}
   
    Provide interaction insights as a JSON list where each entry has the format:
    {{
        "speaker_1": "Name",
        "speaker_2": "Name",
        "interaction": "Type of interaction (e.g., agreement, disagreement, response)",
        "context": "Brief context of interaction"
    }}
    """
    response = llm.invoke(prompt)
    try:
        interactions = json.loads(response.content.strip())
    except json.JSONDecodeError:
        print("Error: Could not parse interaction analysis as JSON.")
        interactions = []
    return interactions
 
def overall_meeting_summary(conversation):
    """Generate a high-level summary of the meeting, including main topics, outcomes, and sentiment."""
    prompt = f"""
    Provide a high-level summary of this multi-speaker meeting, focusing on the main topics, outcomes, and overall sentiment. Include whether any decisions or consensus were reached.
   
    Conversation: {conversation}
   
    Summary:
    """
    response = llm.invoke(prompt)
    return response.content.strip()
 
def generate_analysis_report(conversation):
    """Generate a comprehensive report for a multi-speaker meeting."""
    report = {
        "Overall Meeting Summary": overall_meeting_summary(conversation),
        "Speaker Contributions": analyze_speaker_contributions(conversation),
        "Speaker Interactions": speaker_interaction_analysis(conversation),
        "Call Structure": analyze_conversation("How was the call structured?", conversation),
        "Pitch or Sell": analyze_conversation("Did we have to pitch or sell? If so, what did we say?", conversation),
        "Call Purpose": analyze_conversation("How would you summarize the call?", conversation),
        "Customer Feedback": analyze_conversation("What did the customer tell us on this call?", conversation),
        "Our Response": analyze_conversation("How did we respond to the customer?", conversation),
        "Pitched and Received": analyze_conversation("What was pitched and how was it received?", conversation),
        "Customer Sentiment": analyze_conversation("What was the general customer sentiment?", conversation),
        "Negative Sentiment": analyze_conversation("If there is negative customer sentiment, what caused it?", conversation),
        "Action Items": analyze_conversation("What are action items, next steps, and results from the call?", conversation),
        "Missed Opportunities": analyze_conversation("Did we miss opportunities to sell, move faster, or service the customer better?", conversation),
        "Language Barrier": analyze_conversation("Was there any language barrier?", conversation),
        "CRM/Deal Updates": analyze_conversation("What are CRM/deal relevant updates?", conversation),
        "Customer Interest": analyze_conversation("On a scale of 1 to 10 how interested in the product?", conversation),
        "Sales Pitch Rating": rate_sales_pitch(conversation)
    }
    return report
 
def rate_sales_pitch(conversation):
    """Rates the employee's sales pitch on a scale of 1 to 10 based on clarity, relevance, persuasiveness, and responsiveness."""
   
    prompt = f"""
    Rate the sales pitch by employees on a scale of 1 to 10 based on clarity, relevance, persuasiveness, and responsiveness. Provide a JSON with scores and brief explanations.
 
    Conversation:
    {conversation}
   
    Format:
    {{
        "clarity": {{"score": "<score>/10", "explanation": "<Explanation>"}},
        "relevance": {{"score": "<score>/10", "explanation": "<Explanation>"}},
        "persuasiveness": {{"score": "<score>/10", "explanation": "<Explanation>"}},
        "responsiveness": {{"score": "<score>/10", "explanation": "<Explanation>"}},
        "overall": {{"score": "<overall score>/10", "explanation": "<Explanation>"}}
    }}
    """
   
    response = llm.invoke(prompt)
    try:
        rating_data = json.loads(response.content.strip())
    except json.JSONDecodeError:
        print("Error: Could not parse rating response as JSON.")
        rating_data = {"error": "Failed to parse response"}
   
    return rating_data 
    

def getJsonConversation() :
    with open("conversation.json", "r") as f:
            return json.load(f)
