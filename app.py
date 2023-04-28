from flask import Flask

import api.UsersAPI as UsersAPI
import api.SpacesAPI as SpacesAPI
import api.PoliciesAPI as PoliciesAPI
import api.ReservationsAPI as ReservationsAPI

import Firebase as db

app = Flask(__name__)
app.register_blueprint(UsersAPI.api)
app.register_blueprint(SpacesAPI.api)
app.register_blueprint(PoliciesAPI.api)
app.register_blueprint(ReservationsAPI.api)

@app.get('/')
def test():
    return "Hello world!"

if __name__ == '__main__':
    #db.init(10)
    app.run('localhost', 5000)