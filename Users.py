import Firebase as db

class User:
    count = 0

    def __init__(self, uid):
        self.id = uid

        info = db.reference(f'/users/{uid}').get()
        self.username = info['username']
        self.password = info['password']
        self.email = info['email']
        self.phone = info['phone']

    def __init__(self, username, password, email='', phone=''):
        self.id = ++User.count
        self.username = username
        self.password = password
        self.email = email
        self.phone = phone