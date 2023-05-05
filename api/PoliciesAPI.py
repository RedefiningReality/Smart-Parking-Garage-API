from flask import Blueprint
from firebase import Firebase as db

api = Blueprint('policies', __name__)