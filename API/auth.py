# API/auth.py

import secrets
from functools import wraps
from flask import request, jsonify, make_response

valid_tokens = {}

def generate_token():
    return secrets.token_urlsafe(32)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return make_response(jsonify({"error": "Unauthorized"}), 401)

        received_token = token.split('Bearer ')[1]
        user = next((u for u, t in valid_tokens.items() if t["token"] == received_token), None)

        if not user:
            return make_response(jsonify({"error": "Unauthorized"}), 401)

        request.user = user
        request.role = valid_tokens[user]['role']

        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.role != "admin":
            return make_response(jsonify({"error": "Forbidden"}), 403)
        return f(*args, **kwargs)

    return decorated_function
