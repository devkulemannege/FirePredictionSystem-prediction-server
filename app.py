from flask import Flask, jsonify, request
import dotenv
import base64
import os

# load env variables
dotenv.load_dotenv()

API_USR = os.getenv('API_USR')
API_PSW = os.getenv('API_PSW')

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'operational_status':'ok'})

@app.route('/transfer', methods=['POST'])
def transfer():
    ''' Handle the transmission of prediction request data while authenticating credentials '''
    authValue = request.authorization

    if authValue:
        if API_USR == authValue.username and API_PSW == authValue.password:
            payload = request.json
            # TODO: continue functionality 

            return jsonify({'status':'success'}), 200
        else:
            return jsonify({'status':'unauthorized'}), 401
    else:
        return jsonify({'status':'missing_authorization'}), 401

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=False)