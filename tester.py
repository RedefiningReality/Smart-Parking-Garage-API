from pprint import pprint

import firebase_admin
from firebase_admin import credentials, db

creds = credentials.Certificate('creds.json')
firebase_admin.initialize_app(creds, {
    'databaseURL': 'https://smart-parking-garage-default-rtdb.firebaseio.com/'
})

pprint(db.reference('/users').get())