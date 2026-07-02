from flask_mail import Message
from flask import render_template
from datetime import date

def send(usrEmail, mail):
    ''' Error email which notifies the expecting user in case main process encounters an error '''
    try:
        msg = Message(
            subject = f'Fire Prediction Results for {usrEmail} on {date.today()}',
            recipients = [usrEmail]
        )

        # use html for email 
        msg.html = render_template('fail.html')
        mail.send(msg) # send

    except Exception as e:
        print(f'ERROR: Unable to send FAILURE MAIL for {usrEmail}: {e}') 

    return
