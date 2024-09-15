from functools import wraps
from flask import request, jsonify, make_response,Blueprint
from API.services.rabbit_mq import verify_token
auth_blueprint = Blueprint('auth', __name__)




def token_required(f):
    @wraps(f)  # Ajoutez @wraps ici
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return make_response(jsonify({"error": "Unauthorized"}), 401)

        received_token = token.split('Bearer ')[1]
        authenticated, role = verify_token(received_token)

        if not authenticated:
            return make_response(jsonify({"error": "Unauthorized"}), 401)

        request.role = role
        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    @wraps(f)  # Ajoutez @wraps ici
    def decorated_function(*args, **kwargs):
        if request.role != "admin":
            return make_response(jsonify({"error": "Forbidden"}), 403)
        return f(*args, **kwargs)

    return decorated_function

