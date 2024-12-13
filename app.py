from flask import Flask, request, jsonify
from flask_cors import CORS
from recordWithvb import  GoogleMeetBot
import gc

app = Flask(__name__)
CORS(app)
runTimebots = {}

gc.enable()
gc.collect()

@app.route('/')
def home():
    return "Welcome to your Flask appsddd!"

@app.route('/joinBot', methods =['post'])
def hello():

    data = request.get_json()
    print("reached inside")
    meeting_url = data.get('meeting_url')
    bot = GoogleMeetBot(email=, password=)
    runTimebots[0] = bot
    message = bot.run_bot(meeting_url)
    response_message = f"{message}:{meeting_url}"

    return jsonify({"message": response_message})

@app.route('/api', methods = ['get']) 
def Text():
    return jsonify({"message": len(runTimebots)})

@app.route('/exitMeeting', methods = ['get'])
def exitmeeting():
    response = runTimebots[0].exit_meeting()
    print("ok")
    return jsonify({"exited" : response})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug= True)