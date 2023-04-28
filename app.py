from flask import Flask
import UsersAPI, SpacesAPI, PoliciesAPI, ReservationsAPI

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