import firebase_admin
from firebase_admin import credentials, db

creds = credentials.Certificate('creds.json')
firebase_admin.initialize_app(creds, {
    'databaseURL': 'https://smart-parking-garage-default-rtdb.firebaseio.com/'
})

def init(num_spaces):
    spaces = {}
    for i in range(num_spaces):
        spaces[i] = { 'occupied': 0 }

    base = db.reference('/')
    base.set({ 'spaces': spaces })

def reference(path):
    return db.reference(path)

if not db.reference('/spaces').get():
    init(10)