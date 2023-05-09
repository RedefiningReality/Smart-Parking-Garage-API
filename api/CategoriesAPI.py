from flask import Blueprint, request
from firebase import Firebase as db
from api import SpacesAPI

api = Blueprint('categories', __name__)

@api.get('/api/categories')
def get_categories():
    categories = db.reference('/categories').get()
    if categories:
        return list(categories.keys())
    else:
        return []

@api.post('/api/categories')
def create_category():
    if request.is_json:
        data = request.get_json()
        name = data.get('name')

        spaces = data.get('spaces')
        price = data.get('price')
        drivein = data.get('drive_in')

        if spaces is None or len(spaces) == 0:
            return 'Must specify at least one space for this category', 400
        elif not isinstance(spaces, list) or not all(isinstance(elem, int) for elem in spaces):
            return 'spaces must be a list of space ids (integers)', 400
        elif len(spaces) != len(set(spaces)):
            return 'spaces must not contain any duplicate values', 400
        if drivein is not None and not isinstance(drivein, bool):
            return 'drive_in must be a boolean (true or false)', 400
        if price is not None and not isinstance(price, float):
            return 'price must be a valid float', 400

        if name:
            data = {
                'spaces': spaces,
                'price': price,
                'drive_in': drivein
            }

            ref = db.reference('/categories')
            categories = ref.get()
            if categories:
                category_names = list(categories.keys())
                if name in category_names:
                    return f'Category {name} already exists', 409
                ref.update({ name: data })
            else:
                db.reference('/').update({ 'categories': { name: data } })

            for s in spaces:
                SpacesAPI.update_category(s, name)
            return '', 204
        else:
            return 'Must specify category name', 400

    return 'Request must be in JSON format', 415

@api.delete('/api/categories')
def remove_all_categories():
    db.reference('/categories').set({})
    for i in range(len(db.reference('/spaces').get())):
        db.reference(f'/spaces/{i}/category').delete()
    return '', 204

@api.put('/api/categories/<string:name>')
def change_categoryname(name):
    categories = db.reference(f'/categories')
    category = categories.child(name)
    category_data = category.get()
    if category_data:
        if request.is_json:
            data = request.get_json()

            new = data.get('name')
            if new and new != name:
                if categories.child(new).get():
                    return f'Category {new} already exists', 409
                else:
                    category.set({})
                    categories.update({ new: category_data })

                    if category_data.get('spaces') is not None:
                        for space in category_data['spaces']:
                            SpacesAPI.update_category(space, new)
                    return '', 204
            else:
                return 'Must specify a new category name with key name', 400
        else:
            return 'Request must be in JSON format', 415
    else:
        return 'The specified category does not exist', 404

@api.delete('/api/categories/<string:name>')
def remove_category(name):
    category = db.reference(f'/categories/{name}')
    category_data = category.get()
    if category_data:
        category.set({})

        if category_data.get('spaces'):
            for space in category_data['spaces']:
                db.reference(f'/spaces/{space}/category').delete()
        return '', 204
    else:
        return 'The specified category does not exist', 404

@api.get('/api/categories/<string:name>/spaces')
def category_spaces(name):
    sids = db.reference(f'/categories/{name}/spaces').get()
    if sids:
        spaces = []
        for sid in sids:
            spaces.append(SpacesAPI.get_space(sid))
        return spaces
    else:
        return 'The requested category does not exist', 404

# full update
@api.put('/api/categories/<string:name>/spaces')
def set_spaces(name):
    category = db.reference(f'/categories/{name}').get()
    if category:
        if request.is_json:
            data = request.get_json()
            spaces = data.get('spaces')

            if spaces is None:
                return 'Must specify spaces', 400
            elif not isinstance(spaces, list) or not all(isinstance(elem, int) for elem in spaces):
                return 'spaces must be a list of space ids (integers)', 400
            elif len(spaces) != len(set(spaces)):
                return 'spaces must not contain any duplicate values', 400

            ref = db.reference(f'/categories/{name}/spaces')
            old = ref.get()
            ref.set(spaces)
            
            if old:
                for s in old:
                    db.reference(f'/spaces/{s}/category').delete()
            for s in spaces:
                SpacesAPI.update_category(s, name)
            return '', 204
        else:
            return 'Request must be in JSON format', 415
    else:
        return 'The specified category does not exist', 404

# add space
@api.patch('/api/categories/<string:name>/spaces')
def add_space(name):
    category = db.reference(f'/categories/{name}').get()
    if category:
        if request.is_json:
            data = request.get_json()
            space = data.get('space')
            spaces = data.get('spaces')

            if space is not None and not isinstance(space, int):
                return 'space must be a valid space id (integer)', 400

            if spaces is None:
                if space is None:
                    return 'Must specify space or spaces', 400
                else:
                    spaces = []
                    spaces.append(space)
            else:
                if not isinstance(spaces, list) or not all(isinstance(elem, int) for elem in spaces):
                    return 'spaces must be a list of space ids (integers)', 400
                elif len(spaces) != len(set(spaces)):
                    return 'spaces must not contain any duplicate values', 400

                if space is not None:
                    spaces.append(space)
            
            ref = db.reference(f'/categories/{name}/spaces')
            current = ref.get()
            idx = len(current)
            spaces_dict = {}
            for s in spaces:
                if s not in current:
                    spaces_dict[idx] = s
                    idx += 1
            
            if len(spaces_dict) > 0:
                ref.update(spaces_dict)
            for s in spaces:
                SpacesAPI.update_category(s, name)
            return '', 204
        else:
            return 'Request must be in JSON format', 415
    else:
        return 'The specified category does not exist', 404

# remove space
@api.delete('/api/categories/<string:name>/spaces')
def delete_space(name):
    category = db.reference(f'/categories/{name}').get()
    if category:
        if request.is_json:
            data = request.get_json()
            space = data.get('space')
            spaces = data.get('spaces')

            if space is not None and not isinstance(space, int):
                return 'space must be a valid space id (integer)', 400

            if spaces is None:
                if space is None:
                    return 'Must specify space or spaces', 400
                else:
                    spaces = []
                    spaces.append(space)
            else:
                if not isinstance(spaces, list) or not all(isinstance(elem, int) for elem in spaces):
                    return 'spaces must be a list of space ids (integers)', 400
                if space is not None:
                    spaces.append(space)
            
            if category.get('spaces') is not None:
                for s in spaces:
                    if s in category['spaces']:
                        category['spaces'].remove(s)

            db.reference(f'/categories/{name}/spaces').set(category['spaces'])
            for s in spaces:
                db.reference(f'/spaces/{s}/category').delete()
            return '', 204
        else:
            return 'Request must be in JSON format', 415
    else:
        return 'The specified category does not exist', 404

@api.get('/api/categories/<string:name>/properties')
def get_category(name):
    response = db.reference(f'/categories/{name}').get()
    if response:
        if response.get('spaces'):
            del response['spaces']
        return response
    else:
        return 'The requested category does not exist', 404

@api.put('/api/categories/<string:name>/properties')
def update_category(name):
    category = db.reference(f'/categories/{name}')
    if category.get():
        if request.is_json:
            data = request.get_json()
            
            price = data.get('price')
            drivein = data.get('drive_in')

            new = {}
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
            
            category.update(new)
            return '', 204
        else:
            'Request must be in JSON format', 415
    else:
        return 'The specified category does not exist', 404