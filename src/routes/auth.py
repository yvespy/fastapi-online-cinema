from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from src.config.dependencies import get_email_sender
from src.database import get_db

from src.models import User, UserGroup, UserGroupEnum, ActivationToken, RefreshToken, PasswordResetToken
from src.notifications.interface import EmailSenderInterface
from src.schemas import (
    UserRegistrationResponseSchema,
    UserRegistrationRequestSchema,
    MessageResponseSchema,
    PasswordRequestSchema,
    TokenRefreshResponseSchema,
    UserLoginResponseSchema,
    UserLoginRequestSchema,
    TokenRefreshRequestSchema,
    PasswordResetCompleteRequestSchema,
    ChangePasswordRequestSchema
)
from src.security.passwords import verify_password, hash_password, validate_password_strength
from src.security.token_manager import create_access_token, decode_token
from src.utils import generate_secure_token

router = APIRouter(prefix="/auth", tags=["auth"])

security = HTTPBearer()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    summary="User Registration",
    description="Register a new user with an email and password.",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "Conflict - User with this email already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A user with this email test@example.com already exists."
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred during user creation.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred during user creation."
                    }
                }
            },
        },
    }
)
async def register_user_endpoint(user_data: UserRegistrationRequestSchema, db: AsyncSession = Depends(get_db),
                                 email_sender: EmailSenderInterface = Depends(get_email_sender)):
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"A user with this email {user_data.email} already exists.")

    stmt = select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
    result = await db.execute(stmt)
    user_group = result.scalars().first()
    if not user_group:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User group not found.")

    try:
        validate_password_strength(user_data.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    try:
        hashed = hash_password(user_data.password)
        new_user = User(email=str(user_data.email), hashed_password=hashed, group_id=user_group.id, is_active=False)
        db.add(new_user)
        await db.flush()

        activation_token = ActivationToken(user_id=new_user.id)
        db.add(activation_token)

        await db.commit()
        await db.refresh(new_user)
        await db.refresh(activation_token)

        activation_link = f"http://127.0.0.1:8000/auth/activate/?token={activation_token.token}"
        await email_sender.send_activation_email(email=new_user.email, activation_link=activation_link)

        return UserRegistrationResponseSchema.model_validate(new_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An error occured while creating user.") from e


@router.post(
    "/activate/",
    response_model=MessageResponseSchema,
    summary="Activate User Account",
    description="Activate a user's account using their email and activation token.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The activation token is invalid or expired, "
                           "or the user account is already active.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid Token",
                            "value": {
                                "detail": "Invalid or expired activation token."
                            }
                        },
                        "already_active": {
                            "summary": "Account Already Active",
                            "value": {
                                "detail": "User account is already active."
                            }
                        },
                    }
                }
            },
        },
    },
)
async def activate_user_endpoint(token: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ActivationToken).where(ActivationToken.token == token)
    result = await db.execute(stmt)
    activation_token = result.scalars().first()

    if not activation_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired activation token.")

    if activation_token.expires_at < datetime.utcnow():
        await db.delete(activation_token)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired activation token.")

    stmt = select(User).where(User.id == activation_token.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.is_active = True
    await db.delete(activation_token)
    await db.commit()

    return MessageResponseSchema(message="User successfully activated.")


@router.post(
    "/resend-activation/",
    response_model=MessageResponseSchema,
    summary="Resend Activation Email",
    description="Resend activation email if the user is not yet active.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Bad Request - Token still valid or user already active.",
              "content": {"application/json": {"example": {"detail": "Token is still valid. Check your email."}}}},
    },
)
async def resend_activation_endpoint(request: PasswordRequestSchema, db: AsyncSession = Depends(get_db),
                                     email_sender: EmailSenderInterface = Depends(get_email_sender)):
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already activated.")

    stmt = select(ActivationToken).where(ActivationToken.user_id == user.id)
    result = await db.execute(stmt)
    token_obj = result.scalars().first()

    now = datetime.utcnow()
    if token_obj and token_obj.expires_at > now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token is still valid. Check your email.")

    if token_obj:
        await db.delete(token_obj)
        await db.commit()

    new_token = ActivationToken(user_id=user.id, token=generate_secure_token())
    db.add(new_token)
    await db.commit()

    activation_link = f"http://127.0.0.1:8000/auth/activate/?token={new_token.token}"
    await email_sender.send_activation_email(email=user.email, activation_link=activation_link)

    return MessageResponseSchema(message="Activation link has been sent.")


@router.post(
    "/login/",
    response_model=UserLoginResponseSchema,
    summary="User Login",
    description="Authenticate user and return access and refresh tokens.",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Invalid email or password.",
              "content": {"application/json": {"example": {"detail": "Incorrect email or password."}}}},
        403: {"description": "Forbidden - User not activated.",
              "content": {"application/json": {"example": {"detail": "User account is not activated."}}}},
    },
)
async def login_endpoint(login_data: UserLoginRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == login_data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not activated.")

    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(minutes=30))

    stmt = select(RefreshToken).filter_by(user_id=user.id)
    result = await db.execute(stmt)
    old_token = result.scalars().first()
    if old_token:
        await db.delete(old_token)
        await db.commit()

    new_refresh_token = generate_secure_token(32)
    refresh_obj = RefreshToken(user_id=user.id, token=new_refresh_token)
    db.add(refresh_obj)
    await db.commit()

    return UserLoginResponseSchema(access_token=access_token, refresh_token=new_refresh_token)


@router.post(
    "/refresh/",
    response_model=TokenRefreshResponseSchema,
    summary="Refresh Access Token",
    description="Refresh access token using a valid refresh token.",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Refresh token not found.",
              "content": {"application/json": {"example": {"detail": "Refresh token not found."}}}},
    },
)
async def refresh_token_endpoint(data: TokenRefreshRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(RefreshToken).where(RefreshToken.token == data.refresh_token).options(selectinload(RefreshToken.user))
    result = await db.execute(stmt)
    refresh_record = result.scalars().first()
    if not refresh_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found.")

    user = refresh_record.user
    new_access = create_access_token({"sub": str(user.id)})
    return TokenRefreshResponseSchema(access_token=new_access)


@router.post(
    "/logout/",
    response_model=MessageResponseSchema,
    summary="User Logout",
    description="Invalidate refresh token to logout user.",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized - Invalid token.",
              "content": {"application/json": {"example": {"detail": "Invalid token."}}}},
    },
)
async def logout_endpoint(token: str, db: AsyncSession = Depends(get_db)):
    stmt = select(RefreshToken).where(RefreshToken.token == token)
    result = await db.execute(stmt)
    token_record = result.scalars().first()
    if not token_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    await db.delete(token_record)
    await db.commit()
    return MessageResponseSchema(message="Logged out successfully.")


@router.post(
    "/reset-password/request/",
    response_model=MessageResponseSchema,
    summary="Request Password Reset",
    description="Request a password reset link. If user exists and active, previous tokens are invalidated.",
    status_code=status.HTTP_200_OK,
)
async def request_password_reset_endpoint(data: PasswordRequestSchema, db: AsyncSession = Depends(get_db),
                                          email_sender: EmailSenderInterface = Depends(get_email_sender)):
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        return MessageResponseSchema(message="If you are registered, you will receive an email with instructions.")

    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    await db.commit()

    token = generate_secure_token(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    reset_obj = PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at)
    db.add(reset_obj)
    await db.commit()
    await db.refresh(reset_obj)

    reset_link = f"http://127.0.0.1:8000/reset-password?token={token}"
    await email_sender.send_password_reset_email(email=user.email, reset_link=reset_link)

    return MessageResponseSchema(message="If you are registered, you will receive an email with instructions.")


async def _get_user_by_email(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalars().first()


@router.post(
    "/reset-password/complete/",
    response_model=MessageResponseSchema,
    summary="Complete Password Reset",
    description="Reset a user's password using a valid token.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Bad Request - Invalid email, token, or token expired.",
              "content": {"application/json": {"example": {"detail": "Invalid email or token."}}}},
    },
)
async def reset_password_endpoint(data: PasswordResetCompleteRequestSchema, db: AsyncSession = Depends(get_db),
                                  email_sender: EmailSenderInterface = Depends(get_email_sender)):
    user = await _get_user_by_email(db, data.email)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or token.")

    stmt = select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    result = await db.execute(stmt)
    token_record = result.scalars().first()
    if not token_record or token_record.token != data.token:
        if token_record:
            await db.delete(token_record)
            await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or token.")

    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        await db.delete(token_record)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or token.")

    try:
        validate_password_strength(data.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    try:
        user.hashed_password = hash_password(data.password)
        await db.delete(token_record)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An error occurred while resetting the password.")

    login_link = "http://127.0.0.1:8000/auth/login/"
    await email_sender.send_password_reset_complete_email(email=user.email, login_link=login_link)

    return MessageResponseSchema(message="Password reset successfully.")


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return user


@router.post(
    "/change-password/",
    response_model=MessageResponseSchema,
    summary="Change Password",
    description="Change password for the currently authenticated user.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Bad Request - Incorrect old password or new password invalid.",
              "content": {"application/json": {"example": {"detail": "Incorrect old password."}}}},
    },
)
async def change_password_endpoint(
        data: ChangePasswordRequestSchema,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password.")

    try:
        validate_password_strength(data.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    current_user.hashed_password = hash_password(data.new_password)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return MessageResponseSchema(message="Password changed successfully.")
