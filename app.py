from flask import Flask, jsonify, request
from flask_limiter import Limiter
import dotenv
import os

from modules.request_queue import request_queue
from modules import worker

# load env variables
dotenv.load_dotenv()

API_USR = os.getenv('API_USR')
API_PSW = os.getenv('API_PSW')

app = Flask(__name__)
queue = request_queue() # create queue object 

def get_email():
    payload = request.json
    return payload['email']

limiter = Limiter(
    app=app,
    key_func=get_email,
    default_limits=['10 per day']
)

@app.route('/')
@limiter.exempt
def health_check():
    return jsonify({'status':'ok'}), 200

@app.route('/transfer', methods=['POST'])
def transfer():
    ''' Handle the transmission of prediction request data while authenticating credentials '''
    authValue = request.authorization

    if authValue:
        if API_USR == authValue.username and API_PSW == authValue.password:
            payload = request.json
            
            # enqueue request 
            queue.enqueue(payload['taskId'], payload['token'], payload['email'])
            print(f'{payload['email']} | request added to queue')
            worker.start_worker(queue, app) # send queue ref to worker function

            return jsonify({'status':'ok'}), 200
        else:
            return jsonify({'status':'unauthorized'}), 401
    else:
        return jsonify({'status':'missing_authorization'}), 401

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=False)