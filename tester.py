from pprint import pprint

import firebase_admin
from firebase_admin import credentials, db

creds = credentials.Certificate('firebase/creds.json')
firebase_admin.initialize_app(creds, {
    'databaseURL': 'https://smart-parking-garage-default-rtdb.firebaseio.com/'
})

pprint(db.reference('/spaces/1/occupied').get())