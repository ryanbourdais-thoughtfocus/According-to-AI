import os
import json
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), model_name="gpt-3.5-turbo", max_tokens=300)

def analyze_conversation(question, conversation):
    prompt = f"""
    You are analyzing a customer service call conversation. Below is the conversation in JSON format. Based on this, please answer the following question:

    Conversation: {conversation}

    Question: {question}

    Answer:"""
    response = llm.invoke(prompt)
    return response.content.strip()

def call_structure(conversation):
    return analyze_conversation("How was the call structured?", conversation)

def call_pitch(conversation):
    return analyze_conversation("Did we have to pitch or sell? If so, what did we say?", conversation)

def call_summary(conversation):
    return analyze_conversation("How would you summarize the call's purpose?", conversation)

def customer_feedback(conversation):
    return analyze_conversation("What did the customer tell us on this call?", conversation)

def our_response(conversation):
    return analyze_conversation("How did we respond to the customer?", conversation)

def pitched_response(conversation):
    return analyze_conversation("What was pitched and how was it received?", conversation)

def customer_sentiment(conversation):
    return analyze_conversation("What was the general customer sentiment?", conversation)

def negative_sentiment(conversation):
    return analyze_conversation("If there is negative customer sentiment, what caused it?", conversation)

def action_items(conversation):
    return analyze_conversation("What are action items, next steps, and results from the call?", conversation)

def missed_opportunities(conversation):
    return analyze_conversation("Did we miss opportunities to sell, move faster, or service the customer better?", conversation)

def language_barrier(conversation):
    return analyze_conversation("Was there any language barrier?", conversation)

def crm_updates(conversation):
    return analyze_conversation("What are CRM/deal relevant updates?", conversation)

def cust_interest(conversation):
    return analyze_conversation("On a scale of 1 to 10 how interested in the product?", conversation)

def rate_sales_pitch(conversation):
    """Rates the employee's sales pitch on a scale of 1 to 10 based on clarity, relevance, persuasiveness, and responsiveness."""
    
    prompt = f"""
    You are analyzing a customer service call in which an employee pitched a product to a client. Based on the conversation below, rate the employee's sales pitch on a scale of 1 to 10 for each of the following criteria, and provide a brief explanation for each score. Respond strictly in JSON format.

    Criteria:
    1. Clarity: How clearly did the employee explain the product and its benefits?
    2. Relevance: How relevant was the pitch to the customer's needs and concerns?
    3. Persuasiveness: How effectively did the employee communicate the value of the product?
    4. Responsiveness: How well did the employee handle the customer's objections or questions?

    Format your response strictly as follows, without any extra text:
    {{
        "clarity": {{"score": "<score>/10", "explanation": "<Explanation>"}},
        "relevance": {{"score": "<score>/10", "explanation": "<Explanation>"}},
        "persuasiveness": {{"score": "<score>/10", "explanation": "<Explanation>"}},
        "responsiveness": {{"score": "<score>/10", "explanation": "<Explanation>"}},
        "overall": {{"score": "<overall score>/10", "explanation": "<Explanation>"}}
    }}

    Conversation:
    {conversation}
    """
    
    response = llm.invoke(prompt)
    rating = response.content.strip()
    
    try:
        rating_data = json.loads(rating)
    except json.JSONDecodeError:
        print("Error: Could not parse model response as JSON. Fallback to manual extraction.")
        rating_data = {"error": "Failed to parse response"}
    
    return rating_data

def generate_analysis_report(conversation):
    report = {
        "Call Structure": call_structure(conversation),
        "Pitch or Sell": call_pitch(conversation),
        "Call Purpose": call_summary(conversation),
        "Customer Feedback": customer_feedback(conversation),
        "Our Response": our_response(conversation),
        "Pitched and Received": pitched_response(conversation),
        "Customer Sentiment": customer_sentiment(conversation),
        "Negative Sentiment": negative_sentiment(conversation),
        "Action Items": action_items(conversation),
        "Missed Opportunities": missed_opportunities(conversation),
        "Language Barrier": language_barrier(conversation),
        "CRM/Deal Updates": crm_updates(conversation),
        "Customer Interest": cust_interest(conversation),
        "Sales Pitch Rating": rate_sales_pitch(conversation)
    }
    return report
