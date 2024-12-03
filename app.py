from flask import Flask, request, render_template, redirect, url_for, send_file,jsonify
import os
import MailHandling
import pdfGen
import json
import interactionReviewWithGpt
import time
import dotenv
from datetime import datetime 
import requests
import logging

app = Flask(__name__)

dotenv.load_dotenv()
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions
ALLOWED_EXTENSIONS = {'txt', 'mp4', 'avi', 'mov', 'mkv'}

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():

    return render_template('index.html')


@app.route('/getText')
def txt():
    return send_file("storedPDF/20241121-0008.pdf", as_attachment = True)


@app.route('/upload', methods=['POST'])
def upload_file():
    logging.info("Received a file upload request.")

    if 'file' not in request.files:
        logging.error("No file part in the request.")
        return "No file part in the request", 400
    

    file = request.files['file'] 
    recipients = request.form.get('recipients', '').split(',')

    # Trim whitespace from recipient emails
    recipients = [email.strip() for email in recipients if email.strip()]

    if not recipients:
        logging.error("No recipient email addresses provided.")
        return "No recipient email addresses provided", 400



    if file.filename == '':
        logging.error("No selected file.")
        return "No selected file", 400

    if file and allowed_file(file.filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        logging.info(f"File saved to {file_path}.")

        # Send the file as part of a POST request
        try:
            with open(file_path, 'rb') as f:
                response = requests.post(
                    'http://localhost:7071/api/process_file_api',
                    files={'file': f}
                )
            logging.info(f"File sent to API. Status code: {response.status_code}")

            if response.status_code == 200:
                logging.info("File processed successfully.")
                
                # Get the entire response JSON
                response_data = response.json()
                if isinstance(response_data, list):
                    json_data = response_data[0]  # Pick the first element if it's a list
                else:
                    json_data = response_data


                # Write the response JSON to conversation.json
                with open('conversation.json', 'w') as json_file:
                    json.dump(response_data, json_file, indent=4)

                logging.info("Response JSON stored in conversation.json.")

                # Execute the following code only on successful POST
                logging.info("Fetching conversation...")
                logging.info("Analysing the conversation...")
                printTime()
                json_data = interactionReviewWithGpt.main()
                
                printTime()
                
                logging.info("Got response.")
                printTime()
                logging.info("Generating PDF...")
                name = generatePDF(json_data)

                logging.info("Sending mail with PDF...")
                printTime()

                MailHandling.process_and_send_email(recipients,json_data, pdf_path=r'storedPDF/'+name)
                #logging.info(f"File uploaded and processed successfully: {file.filename}")
                return jsonify({
                    "status": "success",
                    "message": "File uploaded and email sent successfully.",
                    "file": file.filename,
                    "recipients": recipients
                }), 200

            else:
                logging.error("Failed to process file.")
                return "Error processing file", 500
        except Exception as e:
            logging.exception("An error occurred while sending the file to the API.")

    logging.warning("File type not allowed.")
    return "File type not allowed", 400

def generatePDF(json_body = None) :  
    return pdfGen.create_pdf_report(json_body)

def printTime():
    timestamp = time.time()
    current_time = datetime.fromtimestamp(timestamp)
    formatted_time = current_time.strftime("%H:%M:%S")
    print(f"Current Time: {formatted_time}")


if __name__ == "__main__":
    app.run(debug=True)
