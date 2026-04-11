from functools import wraps
from flask import request, jsonify, g
from firebase_admin import auth


def verify_token(f):
    """
    Decorator to verify Firebase ID token on protected routes.
    Attaches decoded token data to Flask's `g` object.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "error": "Authorization header missing or malformed. Use: Bearer <token>"
            }), 401

        id_token = auth_header.split("Bearer ")[1].strip()

        try:
            # Verify the token with Firebase
            decoded_token = auth.verify_id_token(id_token)
            g.user = decoded_token          # e.g. g.user["uid"], g.user["email"]
            g.uid  = decoded_token["uid"]

        except auth.ExpiredIdTokenError:
            return jsonify({"success": False, "error": "Token has expired. Please log in again."}), 401

        except auth.InvalidIdTokenError:
            return jsonify({"success": False, "error": "Invalid token. Authentication failed."}), 401

        except Exception as e:
            return jsonify({"success": False, "error": f"Authentication error: {str(e)}"}), 401

        return f(*args, **kwargs)
    return decorated_function


def verify_admin(f):
    """
    Decorator to verify the user is an admin (has custom claim).
    Must be used AFTER @verify_token.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, "user", None)
        if not user or not user.get("admin"):
            return jsonify({"success": False, "error": "Admin privileges required."}), 403
        return f(*args, **kwargs)
    return decorated_function