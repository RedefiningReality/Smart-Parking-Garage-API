from flask import Blueprint, request
from firebase import Firebase as db
from api import ReservationsAPI

api = Blueprint('users', __name__)

@api.get('/api/users')
def get_users():
    users = db.reference('/users').get()
    if users:
        return list(users.keys())
    else:
        return []

@api.post('/api/users')
def create_user():
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone')

        if username and password:
            data = {
                'password': password,
                'email': email,
                'phone': phone
            }

            ref = db.reference('/users')
            users = ref.get()
            if users:
                users = list(users.keys())
                if username in users:
                    return f'User {username} already exists', 409
                ref.update({ username: data })
            else:
                db.reference('/').update({ 'users': { username: data } })
            return '', 204
        else:
            return 'Must specify username and password', 400

    return 'Request must be in JSON format', 415

@api.delete('/api/users')
def remove_all_users():
    db.reference('/users').set({})
    return '', 204

@api.put('/api/users/<string:username>')
def change_username(username):
    users = db.reference(f'/users')
    user = users.child(username)
    user_data = user.get()
    if user_data:
        if request.is_json:
            data = request.get_json()

            new = data.get('username')
            if new and new != username:
                if users.child(new).get():
                    return f'User {new} already exists', 409
                else:
                    user.set({})
                    users.update({ new: user_data })
                    return '', 204
            else:
                return 'Must specify a new username with key username', 400
        else:
            return 'Request must be in JSON format', 415
    else:
        return 'The specified user does not exist', 404

@api.delete('/api/users/<string:username>')
def remove_user(username):
    user = db.reference(f'/users/{username}')
    if user.get():
        user.set({})
        return '', 204
    else:
        return 'The specified user does not exist', 404

@api.get('/api/users/<string:username>/info')
def get_user(username):
    response = db.reference(f'/users/{username}').get()
    if response:
        if response.get('reservations'):
            del response['reservations']
        if response.get('fees'):
            del response['fees']
        return response
    else:
        return 'The requested user does not exist', 404

@api.put('/api/users/<string:username>/info')
def update_user(username):
    user = db.reference(f'/users/{username}')
    if user.get():
        if request.is_json:
            data = request.get_json()
            password = data.get('password')
            email = data.get('email')
            phone = data.get('phone')

            new = {}
            if password:
                new['password'] = password
            if email:
                new['email'] = email
            if phone:
                new['phone'] = phone

            user.update(new)
            return '', 204
        else:
            return 'Request must be in JSON format', 415
    else:
        return 'The requested user does not exist', 404

@api.get('/api/users/<string:username>/reservations')
def get_user_reservations(username):
    response = db.reference(f'/users/{username}').get()
    if response:
        reservations = []
        rids = response.get('reservations')

        if rids:
            for rid in rids:
                reservations.append(ReservationsAPI.get_reservation(rid))

        return reservations
    else:
        return 'The requested user does not exist', 404

@api.get('/api/users/<string:username>/fees')
def get_fees(username):
    response = db.reference(f'/users/{username}').get()
    if response:
        fees = 0.0
        if response.get('overstay_fees'):
            fees = response['overstay_fees']
        return { 'fees': fees }
    else:
        return 'The requested user does not exist', 404

@api.post('/api/users/<string:username>/fees')
def set_fees(username):
    user = db.reference(f'/users/{username}')
    if user.get():
        if request.is_json:
            data = request.get_json()
            fees = data.get('overstay_fees')
            if fees is None:
                return 'Must specify total fees with key overstay_fees', 400
            elif not isinstance(fees, float):
                return 'fees must be a valid price (float)', 400

            user.update({ 'overstay_fees': fees })
            return '', 204
        else:
            return 'Request must be in JSON format', 415
    else:
        return 'The requested user does not exist', 404

@api.put('/api/users/<string:username>/fees')
def add_fee(username):
    user = db.reference(f'/users/{username}')
    user_data = user.get()
    if user_data:
        if request.is_json:
            data = request.get_json()
            fees = user_data.get('overstay_fees')
            if fees is None:
                fees = 0.0

            fee = data.get('overstay_fee')
            if fee is None:
                return 'Must specify a fee with key overstay_fee', 400
            elif not isinstance(fee, float):
                return 'fee must be a valid price (float)', 400

            fees += fee
            user.update({ 'overstay_fees': fees })
            return '', 204
        else:
            return 'Request must be in JSON format', 415
    else:
        return 'The requested user does not exist', 404

'''
if request.is_json:
    return 'Request must be in JSON format', 415
'''