from flask import Blueprint, jsonify
from API.services.rabbit_mq import verify_token
from API.decorators import token_required  # Import the decorator here

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/', methods=['GET'])
def index():
    return jsonify({"msg": "Welcome to the PRODUCT's API. The service is up and running!"}), 200


