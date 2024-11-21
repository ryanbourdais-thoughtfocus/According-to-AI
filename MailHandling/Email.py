import smtplib
import json
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Gmail SMTP setup
smtp_server = "smtp.gmail.com"
port = 587
sender_email = "violahencel2002@gmail.com" 
password = "rogc peyn utgr oeww "  #app-specific password

# Function to dynamically build the email content from JSON data
def build_email_content(json_data):
    # Extract main fields from JSON
    customer_sentiment = json_data.get("Customer Sentiment", "No sentiment provided")
    score = float(json_data.get("Sales Pitch Rating", {}).get("overall", {}).get("score", "0").split("/")[0])
    call_purpose = json_data.get("Call Purpose", "Not specified")
    
    # Greeting and call purpose
    greeting = "<p>Hello Team,</p><br>"
    score_info = f"<p>{call_purpose}</p>"
    score_info += f"<p><b>The call has been rated with a score of {score}/10</b>.</p>"

    # Feedback based on score ranges
    if score > 7:
        feedback = "<p>The call was received positively and indicates strong interest from the customer.</p><br>"
        closing_message = "<p>This is a great opportunity to maintain positive momentum. Keep up the excellent work!</p><br><p>Best Regards,<br>Your Team</p>"
    elif 4 <= score <= 7:
        feedback = "<p>The call received an average score, indicating that while there was interest, there may be areas to improve.</p><br>"
        closing_message = "<p>Consider reviewing the interaction report below to identify any opportunities for further engagement.</p><br><p>Best Regards,<br>Your Team</p>"
    else:
        feedback = "<p>The call received a low score, which may suggest dissatisfaction or unresolved concerns.</p><br>"
        closing_message = "<p>Please prioritize a follow-up with the client to address any potential issues.</p><br><p>Best Regards,<br>Your Team</p>"

    # Add additional details if available
    additional_details = ""
    if "Customer Interest" in json_data or "Missed Opportunity" in json_data or ("Negative Sentiment" in json_data and score <= 7):
        additional_details = "<p><b>Additional Details:</b></p><ul>"
        if "Customer Interest" in json_data:
            additional_details += f"<li><u>Customer Interest:</u> {json_data['Customer Interest']}</li>"
        if "Missed Opportunity" in json_data:
            additional_details += f"<li><u>Missed Opportunity</u>: {json_data['Missed Opportunity']}</li>"
        if "Negative Sentiment" in json_data and score <= 7:  # Only include if score is 7 or below
            additional_details += f"<li><u>Negative Sentiment</u>: {json_data['Negative Sentiment']}</li>"
        additional_details += "</ul><br>"

    # Construct the full email body with HTML and additional line breaks
    body = greeting + score_info + feedback + additional_details + closing_message
    return f"Customer Interaction Report - Score: {score}", body
# Function to dynamically assign recipients based on score and sentiment
def determine_recipients(json_data, score):
    sentiment = json_data.get("Customer Sentiment", "").lower()
    if score > 7 or "positive" in sentiment:
        # Positive: Send to manager
        return ["soorajc01@gmail.com", "ekeshkumar48@gmail.com"]
    elif score <= 4 or "negative" in sentiment:
        # Negative: Send to salesperson
        return ["ryan.bourdais@thoughtfocus.com","ekesh.nagaraja@thoughtfocus.com"]
    else:
        # Average: Send to both salesperson and manager
        return ["soorajc01@gmail.com",  "ekeshkumar48@gmail.com", "mohammad.shishakly@thoughtfocus.com"]
# Function to send email with an optional PDF attachment using Gmail SMTP
def send_email(recipients, subject, body, pdf_path=None):
    # Set up the MIME structure for the email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject

    # Attach the email body with HTML content type
    message.attach(MIMEText(body, "html"))
    
    # Add PDF attachment if provided
    if pdf_path:
        with open(pdf_path, "rb") as pdf_file:
            pdf_attachment = MIMEBase("application", "octet-stream")
            pdf_attachment.set_payload(pdf_file.read())
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header("Content-Disposition", f"attachment; filename={pdf_path.split('/')[-1]}")
            message.attach(pdf_attachment)
    
    try:
        # Connect to the Gmail server and send the email
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, password)  # Log in to the server
            print("login successfull")
            server.sendmail(sender_email, recipients, message.as_string())  # Send the email
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")

# Main function to handle the JSON and trigger the email
def process_and_send_email(json_data, pdf_path=None):
    
    score = float(json_data.get("Sales Pitch Rating", {}).get("overall", {}).get("score", "0").split("/")[0])
    # Build the email content from JSON data
    
    # List of recipients - can also come from JSON if needed
    recipients = determine_recipients(json_data, score)
    subject, body = build_email_content(json_data)
    
    # Send email with optional PDF attachment
    send_email(recipients, subject, body, pdf_path)


