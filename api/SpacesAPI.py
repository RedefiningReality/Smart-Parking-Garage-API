from flask import Blueprint, request
from firebase import Firebase as db

api = Blueprint('spaces', __name__)

@api.get('/api/spaces')
def get_spaces():
    spaces = db.reference('/spaces').get()
    if spaces:
        new_spaces = []

        occupied = request.args.get('occupied')
        if occupied is not None:
            if occupied == 'true' or occupied == 'True':
                occupied = True
            elif occupied == 'false' or occupied == 'False':
                occupied = False
        price = request.args.get('price')
        categories = None
        if price is not None:
            try:
                price = float(price)
            except ValueError:
                return 'price must be a valid float', 400
            policy_price = db.reference('/policy/price').get()
            categories = db.reference('/categories').get()
        drivein = request.args.get('drive_in')
        if drivein is not None:
            if drivein == 'true' or drivein == 'True':
                drivein = True
            elif drivein == 'false' or drivein == 'False':
                drivein = False
            policy_drivein = db.reference('/policy/drive_in').get()
            if categories is not None:
                categories = db.reference('/categories').get()

        # update policy_price and categories as necessary

        print(f'occupied: {occupied}\nprice: {price}\ndrivein: {drivein}')
        for sid, properties in enumerate(spaces):
            print(f'sid: {sid}, properties: {properties}')

            searched = False
            if properties is None:
                continue
            if occupied is not None and properties['occupied'] != occupied:
                continue
            if price is not None:
                if properties.get('price') is None:
                    category_price = None
                    category_drivein = None
                    if categories is not None:
                        for category_properties in categories.values():
                            if category_properties.get('spaces') and sid in category_properties['spaces']:
                                category_price = float(category_properties.get('price'))
                                category_drivein = category_properties.get('drive_in')
                                break
                    searched = True
                    if category_price is None:
                        if policy_price is None or policy_price != price:
                            continue
                    elif category_price != price:
                        continue
                elif float(properties['price']) != price:
                    continue
            if drivein is not None:
                if properties.get('drive_in') is None:
                    if not searched:
                        category_drivein = None
                        if categories is not None:
                            for category_properties in categories.value():
                                if category_properties.get('spaces') and sid in category_properties['spaces']:
                                    category_drivein = category_properties.get('drive_in')
                                    break
                    if category_drivein is None:
                        if policy_drivein is None:
                            if drivein:
                                continue
                        elif policy_drivein != drivein:
                            continue
                    elif category_drivein != drivein:
                        continue
                elif properties['drive_in'] != drivein:
                    continue
            
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
        price = data.get('price')
        drivein = data.get('drive_in')
        
        if occupied is None:
            occupied = False
        elif not isinstance(occupied, bool):
            return 'occupied must be a boolean (true or false)', 400
        if drivein is not None and not isinstance(drivein, bool):
            return 'drive_in must be a boolean (true or false)', 400
        if price is not None and not isinstance(price, float):
            return 'price must be a valid float', 400
        
        data = {
            'occupied': occupied,
            'price': price,
            'drive_in': drivein
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
                elif not isinstance(sid, int):
                    return 'id must be a valid integer', 400
                
                if sid < len(spaces) and spaces[sid]:
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
    space = db.reference(f'/spaces/{sid}')
    space_data = space.get()
    if space_data:
        if request.is_json:
            data = request.get_json()

            new = data.get('id')

            if type(new) is str:
                try:
                    new = int(new)
                except ValueError:
                    return 'id must be a valid integer', 400
            elif not isinstance(new, int):
                return 'id must be a valid integer', 400

            if new == sid:
                return 'Must specify a new id', 400
            else:
                if db.reference(f'/spaces/{new}').get():
                    return f'Space with id {new} already exists', 409
                else:
                    space.set({})
                    db.reference('/spaces').update({ new: space_data })
                    return '', 204
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
            print(f'data: {data}')

            occupied = data.get('occupied')
            price = data.get('price')
            drivein = data.get('drive_in')
            print(f'drivein initial: {drivein}')

            new = {}
            if occupied is not None:
                if isinstance(occupied, bool):
                    new['occupied'] = occupied
                else:
                    return 'occupied must be a boolean (true or false)', 400
            if price is not None:
                if isinstance(price, float):
                    new['price'] = price
                else:
                    return 'price must be a valid float', 400
            if drivein is not None:
                if isinstance(drivein, bool):
                    print(f'drivein in if: {drivein}')
                    new['drive_in'] = drivein
                else:
                    return 'drive_in must be a boolean (true or false)', 400

            print(f'new: {new}')
            space.update(new)
            return '', 204
        else:
            'Request must be in JSON format', 415
    else:
        return 'The requested space does not exist', 404