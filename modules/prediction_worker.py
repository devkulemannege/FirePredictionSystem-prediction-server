import pandas as pd
import pickle
import flask_mail
import os

# initialize variables and dataframes 
destDir = 'modules/appeears_data'

lstDf = pd.DataFrame()
ndviDf = pd.DataFrame()
sur_reflDf = pd.DataFrame()

for i in os.listdir('modules/appeears_data'): # find proper csv files accordingly and assign
    iSplit = i.split('-')

    if 'MOD11A2' in iSplit and 'results.csv' in iSplit:
        lstDf = pd.read_csv(os.path.join(destDir, i))
    elif 'MOD13A2' in iSplit and 'results.csv' in iSplit:
        ndviDf = pd.read_csv(os.path.join(destDir, i))
    elif 'MOD09A1' in iSplit and 'results.csv' in iSplit:
        sur_reflDf = pd.read_csv(os.path.join(destDir, i))

# lst, sur_refl combined calculation and ndvi value retreival
lstCombined = (lstDf['MOD11A2_061_LST_Day_1km'].iloc[-1] + lstDf['MOD11A2_061_LST_Day_1km'].iloc[-1]) / 2
sur_reflCombined = (sur_reflDf['MOD09A1_061_sur_refl_b05'].iloc[-1] + sur_reflDf['MOD09A1_061_sur_refl_b05'].iloc[-2]) / 2
ndviValue = ndviDf['MOD13A2_061__1_km_16_days_NDVI'].iloc[-1]

sampleMonth = ndviDf['Date'].iloc[-1].split('-')[1].lstrip('0') # get month of the sample

# prepare prompt sample for the model
promptSample = pd.DataFrame(
    {
        'lst': [float(lstCombined)],
        'sur_refl': [float(sur_reflCombined)],
        'ndvi': [float(ndviValue)],
        'month': [int(sampleMonth)]
    }
)
 
# load and preidict
model = pickle.load(open('model.pkl', 'rb'))
prediction = model.predict(promptSample)



