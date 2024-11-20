from flask import Flask, request, render_template, redirect, url_for, send_file
import os
import MailHandling
import pdfGen
import json
import interactionReviewWithGpt
import time
import dotenv
from datetime import datetime 

app = Flask(__name__)

dotenv.load_dotenv()
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions
ALLOWED_EXTENSIONS = {'txt', 'mp4', 'avi', 'mov', 'mkv'}


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
    if 'file' not in request.files:
        return "No file part in the request", 400

    file = request.files['file']  

    if file.filename == '':
        return "No selected file", 400

    if file and allowed_file(file.filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # we will make api call from here,
        # get the transcript
        # save it as conversation.json

        print("fetching converstaion......")
        print("Analysing the conversation....")
        printTime()
        json_data = interactionReviewWithGpt.main();
        
        printTime()
        
        print("got response ....")
        printTime()
        print("generating pdf .....")
        name = generatePDF(json_data)

        print("sending mail with pdf....")
        printTime()

        MailHandling.process_and_send_email(json_data, pdf_path=r'storedPDF/'+name)
        return f"File uploaded successfully: {file.filename}", 200
    
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
