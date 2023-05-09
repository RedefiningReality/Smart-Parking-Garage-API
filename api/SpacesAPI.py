from flask import Blueprint, request
from firebase import Firebase as db
from api import ReservationsAPI
from datetime import datetime

api = Blueprint('spaces', __name__)

def update_category(sid, name):
    ref = db.reference(f'/spaces/{sid}')
    if ref.get():
        ref.update({ 'category': name })

def get_price_drivein(sid, properties):
    price = -1
    drivein = None

    category_price = None
    category_drivein = None

    policy_price = None
    policy_drivein = None

    if properties.get('price') is None or properties.get('drive_in') is None:
        if properties.get('category') is not None:
            category = db.reference(f'/categories/{properties["category"]}').get()
            category_price = category.get('price')
            category_drivein = category.get('drive_in')

        policy_price = db.reference('/policies/price').get()
        policy_drivein = db.reference('/policies/drive_in').get()

    if properties.get('price') is None:
        if category_price is None:
            if policy_price is None:
                price = 0.0
            else:
                price = policy_price
        else:
            price = category_price
    else:
        price = properties['price']

    if properties.get('drive_in') is None:
        if category_drivein is None:
            if policy_drivein is None:
                drivein = True
            else:
                drivein = policy_drivein
        else:
            drivein = category_drivein
    else:
        drivein = properties['drive_in']

    return price, drivein

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
        if price is not None:
            try:
                price = float(price)
            except ValueError:
                return 'price must be a valid float', 400

        min_price = request.args.get('min_price')
        if min_price is not None:
            try:
                min_price = float(min_price)
            except ValueError:
                return 'min_price must be a valid float', 400

        max_price = request.args.get('max_price')
        if price is not None:
            try:
                max_price = float(max_price)
            except ValueError:
                return 'max_price must be a valid float', 400

        drivein = request.args.get('drive_in')
        if drivein is not None:
            if drivein == 'true' or drivein == 'True':
                drivein = True
            elif drivein == 'false' or drivein == 'False':
                drivein = False
        
        for sid, properties in enumerate(spaces):
            if properties is None:
                continue
            if occupied is not None and properties['occupied'] != occupied:
                continue

            space_price, space_drivein = get_price_drivein(sid, properties)
            if price is not None and space_price != price:
                continue
            if min_price is not None and space_price < min_price:
                continue
            if max_price is not None and space_price > max_price:
                continue
            if drivein is not None and space_drivein != drivein:
                continue

            spaces[sid]['price'] = space_price
            spaces[sid]['drive_in'] = space_drivein

            if spaces[sid].get('reservations'):
                del spaces[sid]['reservations']
            
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
    db.reference('/categories').set({})
    return '', 204

@api.get('/api/spaces/available')
def get_spaces_available():
    start_str = request.args.get('start_time')
    if start_str is None:
        return 'Must specify reservation start time with parameter start_time', 400
    else:
        try:
            start = datetime.strptime(start_str, ReservationsAPI.datetime_format)
        except ValueError:
            return 'start_time is incorrectly formatted. Correct format: YYYY/MM/DD HH:MM', 400

    end_str = request.args.get('end_time')
    if end_str is None:
        return 'Must specify reservation end time with parameter end_time', 400
    else:
        try:
            end = datetime.strptime(end_str, ReservationsAPI.datetime_format)
        except ValueError:
            return 'end_time is incorrectly formatted. Correct format: YYYY/MM/DD HH:MM', 400

    available = db.reference('/spaces').get()
    if available is None:
        available = []

    reservations = db.reference('/reservations').get()
    if reservations:
        for reservation in reservations.values():
            if available[reservation['space_id']] is None:
                continue

            r_start = datetime.strptime(reservation['start_time'], ReservationsAPI.datetime_format)
            r_end = datetime.strptime(reservation['end_time'], ReservationsAPI.datetime_format)

            if start >= r_start and start < r_end:
                available[reservation['space_id']] = None
            elif end > r_start and end <= r_end:
                available[reservation['space_id']] = None
    
    final = []
    for sid, space in enumerate(available):
        if space is not None:
            final.append(get_space(sid))
    
    return final

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
    ref = db.reference(f'/spaces/{sid}')
    space = ref.get()
    if space:
        ref.set({})

        if space.get('category'):
            name = space['category']
            print(f'Name: {name}')

            category = db.reference(f'/categories/{name}').get()
            if category.get('spaces') is not None:
                if sid in category['spaces']:
                    category['spaces'].remove(sid)

            db.reference(f'/categories/{name}/spaces').set(category['spaces'])
        return '', 204
    else:
        return 'The specified space does not exist', 404

@api.get('/api/spaces/<int:sid>/properties')
def get_space(sid):
    response = db.reference(f'/spaces/{sid}').get()
    if response:
        response['id'] = sid
        response['price'], response['drive_in'] = get_price_drivein(sid, response)

        if response.get('reservations'):
            del response['reservations']

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
            drivein = data.get('drive_in')

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
                    new['drive_in'] = drivein
                else:
                    return 'drive_in must be a boolean (true or false)', 400
            
            space.update(new)
            return '', 204
        else:
            return 'Request must be in JSON format', 415
    else:
        return 'The specified space does not exist', 404

@api.get('/api/spaces/<int:sid>/reservations')
def get_space_reservations(sid):
    response = db.reference(f'/spaces/{sid}').get()
    if response:
        reservations = []
        rids = response.get('reservations')

        if rids:
            for rid in rids:
                reservations.append(ReservationsAPI.get_reservation(rid))

        return reservations
    else:
        return 'The requested space does not exist', 404

@api.get('/api/spaces/<int:sid>/availability')
def get_space_availability(sid):
    response = db.reference(f'/spaces/{sid}').get()
    if response:
        start_str = request.args.get('start_time')
        if start_str is None:
            return 'Must specify reservation start time with parameter start_time', 400
        else:
            try:
                start = datetime.strptime(start_str, ReservationsAPI.datetime_format)
            except ValueError:
                return 'start_time is incorrectly formatted. Correct format: YYYY/MM/DD HH:MM', 400

        end_str = request.args.get('end_time')
        if end_str is None:
            return 'Must specify reservation end time with parameter end_time', 400
        else:
            try:
                end = datetime.strptime(end_str, ReservationsAPI.datetime_format)
            except ValueError:
                return 'end_time is incorrectly formatted. Correct format: YYYY/MM/DD HH:MM', 400

        rids = response.get('reservations')
        if rids:
            for rid in rids:
                if not ReservationsAPI.check_valid_reservation(rid, start, end):
                    return { 'available': False }

        return { 'available': True }
    else:
        return 'The requested space does not exist', 404