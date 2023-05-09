from ssl import OP_SINGLE_ECDH_USE
from flask import Blueprint, request
from firebase import Firebase as db
from api import SpacesAPI
from datetime import datetime, timedelta

api = Blueprint('reservations', __name__)

datetime_format = '%Y/%m/%d %H:%M'

def check_valid_space(sid, start, end, omit=''):
    rids = db.reference(f'/spaces/{sid}/reservations').get()
    if rids:
        for rid in rids:
            if rid != omit and not check_valid_reservation(rid, start, end):
                return False
    
    return True

def check_valid_reservation(rid, start, end):
    if end is not None and start >= end:
        return False

    reservation = get_reservation(rid)
    print(reservation)
    print(reservation['start_time'])
    r_start = datetime.strptime(reservation['start_time'], datetime_format)
    
    if reservation.get('end_time') is None or reservation['end_time'] == '':
        return False
    r_end = datetime.strptime(reservation['end_time'], datetime_format)

    if start >= r_start and start < r_end:
        return False

    if end is not None:
        return end <= r_start or end > r_end

    return True

@api.get('/api/reservations')
def get_reservations():
    reservations = db.reference('/reservations').get()
    if reservations:
        return list(reservations.keys())
    else:
        return []

@api.post('/api/reservations')
def make_reservation():
    if request.is_json:
        data = request.get_json()

        user = data.get('username')
        if user:
            user_data = db.reference(f'/users/{user}').get()
            if not user_data:
                return 'The specified username does not exist', 404

        plate = data.get('license_plate')
        if not plate:
            return 'Must specify license plate with key license_plate', 400

        if data.get('space_id') is None:
            return 'Must specify space id with key space_id', 400
        else:
            sid = data['space_id']
            if not isinstance(sid, int):
                return 'space_id must be a valid space id (integer)', 400
        space_data = db.reference(f'/spaces/{sid}').get()
        if not space_data:
            return 'The specified space_id does not exist', 404

        if data.get('start_time') is None:
            return 'Must specify reservation start time with key start_time', 400
        else:
            try:
                start = datetime.strptime(data['start_time'], datetime_format)
            except ValueError:
                return 'start_time is incorrectly formatted. Correct format: YYYY/MM/DD HH:MM', 400
            start_str = data['start_time']

        end_str = ''
        end = None
        if data.get('end_time') and data['end_time'] != '':
            try:
                end = datetime.strptime(data['end_time'], datetime_format)
            except ValueError:
                return 'end_time is incorrectly formatted. Correct format: YYYY/MM/DD HH:MM', 400
            end_str = data['end_time']

        data = {
            'username': user,
            'space_id': sid,
            'license_plate': plate,
            'start_time': start_str,
            'end_time': end_str
        }

        to_return = {}
        
        hourly_price, drivein = SpacesAPI.get_price_drivein(sid, db.reference(f'/spaces/{sid}').get())
        if end_str != '':
            diff = end - start
            hours = diff.total_seconds() / 3600
            price = hourly_price * hours
            to_return['price'] = price

        if user is None and not drivein:
            return 'This space is not available for unregistered users', 400

        if check_valid_space(sid, start, end):
            new = db.reference('/reservations').push(data)

            if user:
                current = user_data.get('reservations')
                if current:
                    idx = len(current)
                    db.reference(f'/users/{user}/reservations').update({ idx: new.key })
                else:
                    db.reference(f'/users/{user}').update({ 'reservations': { 0: new.key } })

            current = space_data.get('reservations')
            if current:
                idx = len(current)
                db.reference(f'/spaces/{sid}/reservations').update({ idx: new.key })
            else:
                db.reference(f'/spaces/{sid}').update({ 'reservations': { 0: new.key } })

            to_return['reservation_id'] = new.key
            return to_return
        else:
            return 'The desired space is not available at the provided time', 409

    return 'Request must be in JSON format', 415

@api.delete('/api/reservations')
def cancel_all_reservations():
    db.reference('/reservations').set({})
    # todo: finish implementation -> remove reservations in spaces and in users
    return '', 204

@api.get('/api/reservations/lookup')
def lookup_reservation():
    plate = request.args.get('license_plate')
    if plate is None:
        return 'Must specify license plate to look up', 400

    all_reservations = request.args.get('all')
    get_all = all_reservations and (all_reservations == 'true' or all_reservations == 'True')

    reservations = db.reference('/reservations').get()
    results = []
    if reservations:
        for rid, reservation in reservations.items():
            if reservation['license_plate'] == plate:
                if get_all:
                    results.append(rid)
                else:
                    now = datetime.now()
                    if now >= datetime.strptime(reservation['start_time'], datetime_format):
                        if reservation['end_time'] == '':
                            continue
                        elif now < datetime.strptime(reservation['end_time'], datetime_format):
                            results.append(rid)

    return results

@api.get('/api/reservations/<string:rid>')
def get_reservation(rid):
    response = db.reference(f'/reservations/{rid}').get()
    if response:
        return response
    else:
        return 'The requested reservation does not exist', 404

@api.put('/api/reservations/<string:rid>')
def modify_reservation(rid):
    ref = db.reference(f'/reservations/{rid}')
    reservation = ref.get()
    if reservation:
        if request.is_json:
            data = request.get_json()

            sid = data.get('space_id')
            if sid is None:
                sid = reservation['space_id']
            else:
                if not isinstance(sid, int):
                    return 'space_id must be a valid space id (integer)', 400

            plate = data.get('license_plate')
            if plate is None:
                plate = reservation.get('license_plate')

            new_time = False

            start_str = data.get('start_time')
            if start_str:
                new_time = True
            else:
                start_str = reservation['start_time']

            try:
                start = datetime.strptime(start_str, datetime_format)
            except ValueError:
                return 'start_time is incorrectly formatted. Correct format: YYYY/MM/DD HH:MM', 400

            end_str = data.get('end_time')
            if end_str:
                new_time = True
            else:
                end_str = reservation['end_time']

            try:
                end = datetime.strptime(end_str, datetime_format)
            except ValueError:
                return 'end_time is incorrectly formatted. Correct format: YYYY/MM/DD HH:MM', 400

            if new_time and not check_valid_space(sid, start, end, omit=rid):
                return 'The desired space is not available at the provided time', 409

            data = {
                'space_id': sid,
                'start_time': start_str,
                'end_time': end_str,
                'license_plate': plate
            }

            ref.update(data)

            if sid != reservation['space_id']:
                old_ref = db.reference(f'/spaces/{reservation["space_id"]}/reservations')
                old = old_ref.get()
                old.remove(rid)
                old_ref.set(old)

                current = db.reference(f'/spaces/{sid}/reservations').get()
                if current:
                    idx = len(current)
                    db.reference(f'/spaces/{sid}/reservations').update({ idx: rid })
                else:
                    db.reference(f'/spaces/{sid}').update({ 'reservations': { 0: rid } })

            diff = end - start
            hours = diff.total_seconds() / 3600
            hourly_price, _ = SpacesAPI.get_price_drivein(sid, db.reference(f'/spaces/{sid}').get())
            price = round(hourly_price * hours, 2)

            return { 'reservation_id': rid, 'price': price }
        else:
            return 'Request must be in JSON format', 415
    return 'The specified reservation does not exist', 404

@api.delete('/api/reservations/<string:rid>')
def cancel_reservation(rid):
    ref = db.reference(f'/reservations/{rid}')
    reservation = ref.get()
    if reservation:
        ref.set({})

        if reservation.get('username'):
            old_ref = db.reference(f'/users/{reservation["username"]}/reservations')
            old = old_ref.get()
            old.remove(rid)
            old_ref.set(old)
        if reservation.get('space_id'):
            old_ref = db.reference(f'/spaces/{reservation["space_id"]}/reservations')
            old = old_ref.get()
            old.remove(rid)
            old_ref.set(old)

        return '', 204
    else:
        return 'The requested reservation does not exist', 404

@api.post('/api/reservations/<string:rid>/checkin')
def reservation_checkin(rid):
    response = db.reference(f'/reservations/{rid}').get()
    if response:
        now = datetime.now()

        start_str = response['start_time']
        end_str = response['end_time']

        start = datetime.strptime(start_str, datetime_format)
        end = None
        if end_str != '':
            end = end_str = datetime.strptime(end_str, datetime_format)

        if now < start:
            return { 'status': 'failure', 'message': 'not yet valid' }

        grace_period = db.reference('/policies/grace_period').get()
        if grace_period:
            grace_time = start + timedelta(minutes=grace_period)
            print(grace_time.strftime(datetime_format))
            if now > grace_time:
                return { 'status': 'failure', 'message': 'reservation expired' }

        if end is not None and now > end:
            return { 'status': 'failure', 'message': 'reservation expired' }

        sid = response['space_id']
        occupied = db.reference(f'/spaces/{sid}/occupied').get()
        if occupied:
            overflow = db.reference('/policies/overflow_category')
            if overflow:
                sids = db.reference(f'/categories/{overflow}/spaces').get()
                if sids:
                    for s in sids:
                        if s is None:
                            continue
                        if not db.reference(f'/spaces/{s}/occupied').get():
                            db.reference(f'/reservations/{rid}').update({ 'space_id': s })
                            return { 'status': 'success', 'space_id': s, 'message': 'parking space changed' }

            return { 'status': 'failure', 'message': 'parking space conflict' }
        else:
            return { 'status': 'success', 'space_id': sid }
    else:
        return 'The requested reservation does not exist', 404

@api.post('/api/reservations/<string:rid>/checkout')
def reservation_checkout(rid):
    response = db.reference(f'/reservations/{rid}').get()
    if response:
        now = datetime.now()

        start_str = response['start_time']
        end_str = response['end_time']

        start = datetime.strptime(start_str, datetime_format)
        if end_str != '':
            end = datetime.strptime(end_str, datetime_format)
            
            if now > end:
                charge = db.reference('/policies/overstay_fee').get()
                if charge is not None:
                    diff = now - end
                    minutes = diff.total_seconds() / 60
                    fee = minutes * charge

                    user = response['username']
                    fees = user.get('fees')
                    if fees is None:
                        fees = 0.0
                    fees += fee

                    db.reference(f'/users/{user}').update({ 'fees': fees })
                    return { 'status': 'success', 'message': 'late fee added', 'amount': fee }

            return { 'status': 'success' }

        sid = response['space_id']
                
        diff = now - start
        hours = diff.total_seconds() / 3600
        hourly_price, _ = SpacesAPI.get_price_drivein(sid, db.reference(f'/spaces/{sid}').get())
        price = round(hourly_price * hours, 2)
        
        return { 'status': 'success', 'price': price }
    else:
        return 'The requested reservation does not exist', 404