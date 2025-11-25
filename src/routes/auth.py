from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.crud import create_user, activate_user, resend_activation_email
from src.database import get_db
from src.schemas import UserRegistrationResponseSchema, UserRegistrationRequestSchema, MessageResponseSchema, \
    PasswordRequestSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/", response_model=UserRegistrationResponseSchema, summary="User registration", status_code=status.HTTP_201_CREATED)
async def register_user_endpoint(user_data: UserRegistrationRequestSchema, db: AsyncSession = Depends(get_db)):
    return await create_user(user_data, db)

@router.post("/activate/", response_model=MessageResponseSchema)
async def activate_user_endpoint(token: str, db: AsyncSession = Depends(get_db)):
    await activate_user(token, db)
    return {"message": "User successfully activated."}

@router.post("/resend-activation", response_model=MessageResponseSchema)
async def resend_activation_endpoint(request: PasswordRequestSchema, db: AsyncSession = Depends(get_db)):
    return await resend_activation_email(request.email, db)