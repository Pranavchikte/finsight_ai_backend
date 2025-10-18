from pydantic import BaseModel, EmailStr, Field

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    
class LoginSchema(BaseModel):
    email: EmailStr
    password: str