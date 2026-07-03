from flask import render_template
from datetime import date
import dotenv
import traceback
import resend 
import os

# load resend-from-address from env
dotenv.load_dotenv()
RESEND_FROM_ADDRESS=os.getenv('RESEND_FROM_ADDRESS')

def send(usrEmail):
    ''' Error email which notifies the expecting user in case main process encounters an error '''
    try:
        htmlContent = render_template('fail.html')

        params: resend.Emails.SendParams = {
            "from": f"Forest Fire Prediction System <{RESEND_FROM_ADDRESS}>",
            "to": [usrEmail],
            "subject": f'Fire Prediction Results for {usrEmail} on {date.today()}',
            "html": htmlContent,
        }

        resend.Emails.send(params)

    except Exception as e:
        print(f'\n--ERROR: Unable to send FAILURE MAIL for {usrEmail}: {e}--') 
        traceback.print_exc() # print traceback for debugging

    return
