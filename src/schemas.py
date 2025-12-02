from pydantic import BaseModel, EmailStr, field_validator


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


class UserRegistrationRequestSchema(BaseEmailPasswordSchema):
    pass


class PasswordRequestSchema(BaseModel):
    email: EmailStr


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
