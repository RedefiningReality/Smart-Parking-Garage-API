from flask import Blueprint, request
from ..firebase import Firebase as db

api = Blueprint('spaces', __name__)

@api.get('/api/spaces')
def get_spaces():
    spaces = db.reference('/spaces').get()
    if spaces:
        new_spaces = []
        if request.is_json:
            data = request.get_json()
            occupied = data.get('occupied')
            price = data.get('price')
            if price:
                policy_price = db.reference('/policy/price').get()
                categories = db.reference('/categories').get()

            # update policy_price and categories as necessary

            for sid, properties in enumerate(spaces):
                if properties == None:
                    continue
                elif occupied and properties['occupied'] != occupied:
                    continue
                elif price:
                    if properties.get('price') and properties['price'] != price:
                        continue
                    else:
                        for category_properties in categories.values():
                            if category_properties.get('spaces') and sid in category_properties['spaces']:
                                category_price = category_properties.get('price')
                                break
                        if category_price and category_price != price:
                            continue
                        else:
                            if policy_price and policy_price != price:
                                continue
                
                last = len(new_spaces)
                new_spaces.append(spaces[sid])
                new_spaces[last]['id'] = sid
        else:
            for sid, properties in enumerate(spaces):
                if properties != None:
                    last = len(new_spaces)
                    new_spaces.append(spaces[sid])
                    new_spaces[last]['id'] = sid
        return new_spaces
    else:
        return []

@api.post('/api/spaces')
def create_space():
    if request.is_json:
        data = request.get_json()
        sid = data.get('id')

        occupied = data.get('occupied')
        if not occupied:
            occupied = 0
        price = data.get('price')
        
        data = {
            'occupied': occupied,
            'price': price
        }

        ref = db.reference('/spaces')
        spaces = ref.get()
        if spaces:
            if sid:
                if type(sid) is str:
                    try:
                        sid = int(sid)
                    except ValueError:
                        return 'id must be a valid integer', 400
                elif type(sid) is not int:
                    return 'id must be a valid integer', 400

                if spaces[sid]:
                    return f'Space with id {sid} already exists', 409
                else:
                    index = sid
            else:
                index = len(spaces)
            ref.update({ index: data })
        else:
            db.reference('/').update({ 'spaces': { index: data } })
        return '', 204

    return 'Request must be in JSON format', 415

@api.delete('/api/spaces')
def remove_all_spaces():
    db.reference('/spaces').set({})
    return '', 204

@api.put('/api/spaces/<int:sid>')
def change_spaceid(sid):
    spaces = db.reference(f'/spaces')
    space = spaces.child(sid)
    space_data = space.get()
    if space_data:
        if request.is_json:
            data = request.get_json()

            new = data.get('id')
            if new and new != sid:
                space.set({})
                spaces.update({ new: space_data })
            else:
                return 'Must specify a new id with key id', 400
        else:
            return 'Request must be in JSON format', 415
    else:
        return 'The specified space does not exist', 404

@api.delete('/api/spaces/<int:sid>')
def remove_space(sid):
    space = db.reference(f'/spaces/{sid}')
    if space.get():
        space.set({})
        return '', 204
    else:
        return 'The specified space does not exist', 404

@api.get('/api/spaces/<int:sid>/properties')
def get_space(sid):
    response = db.reference(f'/spaces/{sid}').get()
    if response:
        return response
    else:
        return 'The requested space does not exist', 404

@api.put('/api/spaces/<int:sid>/properties')
def update_space(sid):
    space = db.reference(f'/spaces/{sid}')
    if space.get():
        if request.is_json:
            data = request.get_json()
            occupied = data.get('occupied')
            price = data.get('price')

            new = {}
            if occupied:
                new['occupied'] = occupied
            if price:
                new['price'] = price

            space.update(data)
        else:
            'Request must be in JSON format', 415
    else:
        return 'The requested space does not exist', 404