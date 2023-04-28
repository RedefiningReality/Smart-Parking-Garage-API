from flask import Blueprint, request
import Firebase as db

api = Blueprint('users', __name__)

@api.get('/users')
def get_users():
    users = db.reference('/users').get()
    if users:
        return list(users.keys())
    else:
        return []

@api.post('/users')
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

@api.delete('/users')
def remove_all():
    db.reference('/users').set({})
    return '', 204

@api.delete('/users/<string:username>')
def remove_user(username):
    user = db.reference(f'/users/{username}')
    if user.get():
        user.set({})
        return '', 204
    else:
        return 'The specified user does not exist', 404

@api.get('/users/<string:username>/info')
def get_user(username):
    response = db.reference(f'/users/{username}').get()
    if response:
        return response
    else:
        return 'The requested user does not exist', 404

'''
if request.is_json:
    return 'Request must be in JSON format', 415
'''