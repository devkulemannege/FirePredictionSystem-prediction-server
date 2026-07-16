from flask import render_template
from datetime import date
import requests as r
import dotenv
import traceback
import os

# load resend-from-address from env
dotenv.load_dotenv()
SMTP_KEY=os.getenv('SMTP_KEY')
SMTP_URL=os.getenv('SMTP_URL')

def send(usrEmail):
    ''' Error email which notifies the expecting user in case main process encounters an error '''
    try:
        payload = {
            'email': usrEmail,
            'subject': f'Fire Prediction Results for {usrEmail} on {date.today()}',
            'htmlContent': render_template('fail.html')
        }

        reply = r.post(SMTP_URL, headers={"Content-Type": "application/json"}, json=payload, auth=('.',SMTP_KEY))
        if reply.status_code != 200: print(f"Email failed for {usrEmail} | {reply.status_code}: {reply.text}")
    except Exception as e:
        print(f'\n--ERROR: Unable to send FAILURE MAIL for {usrEmail}: {e}--') 
        traceback.print_exc() # print traceback for debugging

    return
