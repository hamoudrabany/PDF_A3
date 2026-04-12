from flask_openapi3 import APIBlueprint, Tag
from flask import request, jsonify
from firebase_admin import auth
from schemas import (
    RegisterRequest, RegisterResponse,
    ErrorResponse, LoginRequest, LoginResponse
)
import requests as http_requests
import os
from dotenv import load_dotenv

load_dotenv()

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
    
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

@auth_bp.post(
    "/token",
    tags=[auth_tag],
    summary="Get Firebase ID token (for Swagger testing only)",
    description="Use only for API testing. In production, authenticate via the client SDK.",
    responses={"200": LoginResponse, "400": ErrorResponse, "401": ErrorResponse}
)
def get_token(body: LoginRequest):
    """
    Calls Firebase REST API to exchange email/password for an ID token.
    Use the returned `id_token` as: Bearer <id_token> in the Authorize button.
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"

    resp = http_requests.post(url, json={
        "email": body.email,
        "password": body.password,
        "returnSecureToken": True
    })

    data = resp.json()

    if "error" in data:
        status = 401 if "INVALID" in data["error"].get("message", "") else 400
        return jsonify({"success": False, "error": data["error"]["message"]}), status

    return jsonify({
        "success":       True,
        "id_token":      data["idToken"],       # use this as Bearer token
        "refresh_token": data["refreshToken"],
        "expires_in":    data["expiresIn"]
    }), 200

