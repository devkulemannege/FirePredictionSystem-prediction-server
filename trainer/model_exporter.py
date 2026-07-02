import pickle
import pandas as pd
from sklearn.linear_model import LogisticRegression

df = pd.read_csv('trainer/training_dataset.csv')

xFeature = df[['lst','sur_refl','ndvi','month']] # extract all rows under feature cols as x
yPredicted = df['fire'] # extract all rows with "fire" col for x

model = LogisticRegression()
model.fit(xFeature, yPredicted)

pickle.dump(model, open('model.pkl','wb')) # export
