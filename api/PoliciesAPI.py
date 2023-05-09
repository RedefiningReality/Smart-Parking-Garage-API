from flask import Blueprint, request
from firebase import Firebase as db

api = Blueprint('policies', __name__)

@api.get('/api/policies')
def get_policies():
    policies = db.reference('/policies').get()
    if policies:
        return policies
    return 'Policies not yet defined. Please set them up with a POST request'

@api.post('/api/policies')
def set_policies():
    if request.is_json:
        data = request.get_json()
        currency = data.get('currency')
        if currency is None:
            currency = 'USD'

        grace_period = data.get('grace_period')
        if grace_period is None:
            grace_period = 15
        elif not isinstance(grace_period, float):
            return 'grace_period must be a valid time (float)', 400

        overflow = data.get('overflow_category')
        fee = data.get('overstay_fee')
        if fee and not isinstance(fee, float):
            return 'overstay_fee must be a valid price (float)', 400

        price = data.get('price')
        if price and not isinstance(price, float):
            return 'price must be a valid price (float)', 400

        drivein = data.get('drive_in')
        if drivein is not None and not isinstance(drivein, bool):
            return 'drive_in must be a valid boolean', 400

        data = {
            'currency': currency,
            'grace_period': grace_period,
            'overflow_category': overflow,
            'overstay_fee': fee,
            'price': price,
            'drive_in': drivein
        }

        ref = db.reference('/policies')
        if ref.get():
            ref.set(data)
        else:
            db.reference('/').update({ 'policies': data })
        return '', 204

    return 'Request must be in JSON format', 415

@api.put('/api/policies')
def update_policies():
    if request.is_json:
        data = request.get_json()
        result = {}

        currency = data.get('currency')
        grace_period = data.get('grace_period')
        overflow = data.get('overflow_category')
        fee = data.get('overstay_fee')
        price = data.get('price')
        drivein = data.get('drive_in')

        if fee and not isinstance(fee, float):
            return 'overstay_fee must be a valid price (float)', 400
        if price and not isinstance(price, float):
            return 'price must be a valid price (float)', 400
        if drivein is not None and not isinstance(drivein, bool):
            return 'drive_in must be a valid boolean', 400

        if currency is not None:
            result['currency'] = currency
        if grace_period is not None:
            result['grace_period'] = grace_period
        if overflow is not None:
            result['overflow_category'] = overflow
        if fee is not None:
            result['overstay_fee'] = fee
        if price is not None:
            result['price'] = price
        if drivein is not None:
            result['drive_in'] = drivein

        ref = db.reference('/policies')
        if ref.get():
            ref.update(result)
        else:
            db.reference('/').update({ 'policies': result })
        return '', 204

    return 'Request must be in JSON format', 415