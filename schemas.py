from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from flask_openapi3 import FileStorage


# ── Request bodies ──────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: str   = Field(..., min_length=6, example="password123")
    name: Optional[str] = Field(None, example="John Doe")

class RegisterResponse(BaseModel):
    success: bool = True
    message: str  = Field(..., example="User registered successfully")
    uid: str      = Field(..., example="abc123uid")
    email: str    = Field(..., example="user@example.com")

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., example="password123")

class LoginResponse(BaseModel):
    success: bool = Field(..., example=True)
    id_token: str = Field(..., example="id_token_example")
    refresh_token: str = Field(..., example="refresh_token_example")
    expires_in: str = Field(..., example="expires_in_example")

class GeneratePDFA3Form(BaseModel):
    pdf: FileStorage          
    xml: FileStorage        
    attachments: List[FileStorage] = []  

    model_config = {"arbitrary_types_allowed": True}
    
class DownloadPDFA3Request(BaseModel):
    content: str  # base64 encoded PDF
# ── Responses ───────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    message: str  = Field(..., example="Operation completed")

class ErrorResponse(BaseModel):
    success: bool = False
    error: str    = Field(..., example="Error message here")


class PDFA3Content(BaseModel):
    content: str = Field(..., example="JVBERi0xLjQKJcfs...")


class GeneratePDFA3Response(BaseModel):
    successful: bool = True
    pdfa3: PDFA3Content


# ── Security scheme (Bearer token) ──────────────────────────

class BearerAuth(BaseModel):
    Authorization: str = Field(
        ...,
        description="Firebase ID Token. Format: **Bearer &lt;token&gt;**",
        example="Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
