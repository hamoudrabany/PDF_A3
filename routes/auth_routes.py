from flask_openapi3 import APIBlueprint, Tag
from flask import request, jsonify
from firebase_admin import auth
from schemas import (
    RegisterRequest, RegisterResponse,
    SuccessResponse, ErrorResponse
)

# Tag groups the endpoints in Swagger UI
auth_tag = Tag(name="Auth", description="User registration and management")
auth_bp  = APIBlueprint("auth", __name__, url_prefix="/auth")

# ---------------------------------------------------------
# API Endpoint 
# ---------------------------------------------------------

# Register route
@auth_bp.post(
    "/register",
    tags=[auth_tag],
    summary="Register a new user",
    responses={"201": RegisterResponse, "400": ErrorResponse, "409": ErrorResponse}
)
def register(body: RegisterRequest):
    """
    Creates a new Firebase user with email and password.
    Returns the UID assigned by Firebase.
    """
    try:
        user = auth.create_user(
            email=body.email,
            password=body.password,
            display_name=body.name or ""
        )
        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "uid":     user.uid,
            "email":   user.email
        }), 201

    except auth.EmailAlreadyExistsError:
        return jsonify({"success": False, "error": "Email already registered"}), 409

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# # Login route
# @bp.route('/login', methods=['POST'])
# def login():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')
#     db = get_db()

#     user = db.execute(
#         'SELECT * FROM user WHERE username = ?', (username,)
#     ).fetchone()

#     if user is None or not check_password_hash(user['password'], password):
#         return jsonify({"error": "Invalid username or password"}), 401
  
#     access_token = create_access_token(identity=user['id'])

#     return jsonify({
#         "message": "Login successful", 
#         "user": {"id": user['id'], "username": user['username']}, 
#         "access_token": access_token
#     }), 200

