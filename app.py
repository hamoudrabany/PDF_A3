from flask_openapi3 import OpenAPI, Info
from flask import Flask
from config import initialize_firebase
from routes.auth_routes import auth_bp
from routes.pdf_a3_routes import pdf_a3
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Swagger metadata 
info = Info(
    title="PDF A-3 API",
    version="1.0.0",
    description="REST API with Firebase Authentication. "
                "Use `/auth/register` to create a user, sign in on the client to get a token, "
                "then pass it as `Authorization: Bearer <token>` on protected routes."
)

# Security scheme definition
security_schemes = {
    "BearerAuth": {
        "type":   "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Paste your Firebase ID Token here."
    }
}

def create_app():
    app = OpenAPI(
                  __name__, 
                  info=info, 
                  security_schemes=security_schemes, 
                  doc_prefix="/pdf-a3"      
                )
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    # Initialize Firebase
    initialize_firebase()

    # Register blueprints
    app.register_api(auth_bp)
    app.register_api(pdf_a3)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)