from pydantic import BaseModel, EmailStr, field_validator

from src.security.passwords import validate_password_strength


class FilmBase(BaseModel):
    title: str
    genre: str
    price: float


class FilmCreate(FilmBase):
    pass


class FilmUpdate(FilmBase):
    pass


class FilmRead(FilmBase):
    id: int

    class Config:
        from_attributes = True


class BaseEmailPasswordSchema(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "from_attributes": True
    }

    @field_validator("email")
    def validate_email(cls, value):
        return value.lower()

    @field_validator("password")
    def validate_password(cls, value):
        return validate_password_strength(value)


class UserRegistrationRequestSchema(BaseEmailPasswordSchema):
    pass


class PasswordRequestSchema(BaseModel):
    email: EmailStr


class ChangePasswordRequestSchema(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    def validate_password(cls, value):
        return validate_password_strength(value)


class PasswordResetCompleteRequestSchema(BaseEmailPasswordSchema):
    token: str


class UserLoginRequestSchema(BaseEmailPasswordSchema):
    pass


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRegistrationResponseSchema(BaseModel):
    id: int
    email: EmailStr

    model_config = {
        "from_attributes": True
    }


class UserActivationRequestSchema(BaseModel):
    email: EmailStr
    token: str


class MessageResponseSchema(BaseModel):
    message: str


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: str


class TokenRefreshResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
