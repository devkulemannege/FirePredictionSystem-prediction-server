from flask import render_template
from datetime import date
import traceback
import pandas as pd
import dotenv
import resend
import pickle
import os

from . import error_mail

# load resend-from-address from env
dotenv.load_dotenv()
RESEND_FROM_ADDRESS=os.getenv('RESEND_FROM_ADDRESS')

def start(usrEmail):
    ''' start data analysis and extraction of the point request and generate prediction.
    finally, send the generated prediction to the user through email'''

    # initialize variables and dataframes 
    destDir = 'modules/appeears_data'

    lstDf = pd.DataFrame()
    ndviDf = pd.DataFrame()
    sur_reflDf = pd.DataFrame()

    try:
        for i in os.listdir('modules/appeears_data'): # find proper csv files accordingly and assign
            iSplit = i.split('-')

            if 'MOD11A2' in iSplit and 'results.csv' in iSplit:
                lstDf = pd.read_csv(os.path.join(destDir, i))
            elif 'MOD13A2' in iSplit and 'results.csv' in iSplit:
                ndviDf = pd.read_csv(os.path.join(destDir, i))
            elif 'MOD09A1' in iSplit and 'results.csv' in iSplit:
                sur_reflDf = pd.read_csv(os.path.join(destDir, i))

        # lst, sur_refl combined calculation and ndvi value retreival 
        lstCombined = (lstDf['MOD11A2_061_LST_Day_1km'].iloc[-1] + lstDf['MOD11A2_061_LST_Day_1km'].iloc[-2]) / 2
        sur_reflCombined = (sur_reflDf['MOD09A1_061_sur_refl_b05'].iloc[-1] + sur_reflDf['MOD09A1_061_sur_refl_b05'].iloc[-2]) / 2
        ndviValue = ndviDf['MOD13A2_061__1_km_16_days_NDVI'].iloc[-1]

        sampleMonth = ndviDf['Date'].iloc[-1].split('-')[1].lstrip('0') # get month of the sample

        # get coordinates of request
        lat = ndviDf['Latitude'].iloc[-1]
        lon = ndviDf['Longitude'].iloc[-1]

        # prepare prompt sample for the model
        promptSample = pd.DataFrame(
            {
                'lst': [float(lstCombined)],
                'sur_refl': [float(sur_reflCombined)],
                'ndvi': [float(ndviValue)],
                'month': [int(sampleMonth)]
            }
        )
    except Exception as e:
        print(f'\n--An Error occurred while reading csv files for {usrEmail} | {e}--')
        traceback.print_exc() # print traceback for debugging
        error_mail.send(usrEmail) # error mail incase main process fails

        return
    
    try:
        # load and preidict
        model = pickle.load(open('model.pkl', 'rb'))
        rawPrediction = model.predict(promptSample)
    except Exception as e:
        print(f'\n--Failed to produce prediction for {usrEmail} | {e}--')
        traceback.print_exc() # print traceback for debugging
        error_mail.send(usrEmail) # error mail incase main process fails

        return

    #------------------------
    # mailing process
    #------------------------

    try:
        htmlPath = ''
        if rawPrediction[0] == 1: htmlPath = 'mailYes.html' # if prediction is 1
        else: htmlPath = 'emailNo.html' # otherwise, 2

        htmlContent = render_template(htmlPath, date=date.today(), longitude=lon, latitude=lat)

        params: resend.Emails.SendParams = {
            "from": f"Forest Fire Prediction System <{RESEND_FROM_ADDRESS}>",
            "to": [usrEmail],
            "subject": f'Fire Prediction Results for {usrEmail} on {date.today()}',
            "html": htmlContent,
        }

        resend.Emails.send(params)

    except Exception as e:
        print(f'\n--ERROR: Unable to send mail for {usrEmail}: {e}--') 
        traceback.print_exc() # print traceback for debugging
        error_mail.send(usrEmail) # error mail incase main process fails
    
    return 
