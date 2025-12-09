from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.crud import create_user, activate_user, resend_activation_email, login_user, get_refresh_token, reset_password, \
    request_password_reset_token, change_password, get_current_user
from src.database import get_db
from src.schemas import UserRegistrationResponseSchema, UserRegistrationRequestSchema, MessageResponseSchema, \
    PasswordRequestSchema, TokenRefreshResponseSchema, UserLoginResponseSchema, UserLoginRequestSchema, \
    TokenRefreshRequestSchema, PasswordResetCompleteRequestSchema, ChangePasswordRequestSchema
from src.security.token_manager import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/", response_model=UserRegistrationResponseSchema, summary="User registration",
             status_code=status.HTTP_201_CREATED)
async def register_user_endpoint(user_data: UserRegistrationRequestSchema, db: AsyncSession = Depends(get_db)):
    return await create_user(user_data, db)


@router.post("/activate/", response_model=MessageResponseSchema)
async def activate_user_endpoint(token: str, db: AsyncSession = Depends(get_db)):
    await activate_user(token, db)
    return {"message": "User successfully activated."}


@router.post("/resend-activation/", response_model=MessageResponseSchema)
async def resend_activation_endpoint(request: PasswordRequestSchema, db: AsyncSession = Depends(get_db)):
    return await resend_activation_email(request.email, db)


@router.post("/login/", response_model=UserLoginResponseSchema)
async def login_endpoint(login_data: UserLoginRequestSchema, db: AsyncSession = Depends(get_db)):
    result = await login_user(db, login_data.email, login_data.password)

    return result


@router.post("/refresh/", response_model=TokenRefreshResponseSchema)
async def refresh_token_endpoint(data: TokenRefreshRequestSchema, db: AsyncSession = Depends(get_db)):
    refresh_record = await get_refresh_token(db, data.refresh_token)
    if not refresh_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found.")

    user = refresh_record.user
    new_access = create_access_token({"sub": str(user.id)})

    return TokenRefreshResponseSchema(access_token=new_access)


@router.post("/logout/")
async def logout_endpoint(token: str, db: AsyncSession = Depends(get_db)):
    token_record = await get_refresh_token(db, token)
    if not token_record:
        raise HTTPException(
            status_code=401,
            detail="Invalid token."
        )

    await db.delete(token_record)
    await db.commit()

    return {"detail": "Logged out successfully."}


@router.post("/reset-password/request/", response_model=MessageResponseSchema)
async def request_password_reset_endpoint(data: PasswordRequestSchema, db: AsyncSession = Depends(get_db)):
    await request_password_reset_token(db, data.email)
    return MessageResponseSchema(
        message="If you are registered, you will receive an email with instructions."
    )


@router.post("/reset-password/complete", response_model=MessageResponseSchema)
async def complete_password_reset(
        data: PasswordResetCompleteRequestSchema,
        db: AsyncSession = Depends(get_db)
):
    ok = await reset_password(db, data.email, data.token, data.password)

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or token."
        )

    return MessageResponseSchema(message="Password reset successfully.")


@router.post("/change-password/", response_model=MessageResponseSchema)
async def change_password_endpoint(
        data: ChangePasswordRequestSchema,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)
):
    await change_password(db, current_user, data.old_password, data.new_password)
    return {"message": "Password changed successfully."}
