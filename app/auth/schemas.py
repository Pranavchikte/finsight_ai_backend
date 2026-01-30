from pydantic import BaseModel, EmailStr, Field, field_validator
import re # ADDED: For password validation

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    # ADDED: Password strength validation (FIX #26)
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        
        return v
    
class LoginSchema(BaseModel):
    email: EmailStr
    password: str