import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from db.database import get_db

from auth.JWTBearer import JWTAuthorizationCredentials, JWTBearer
from auth.auth import jwks, get_current_user
from auth.user_auth import auth_with_code, user_info_with_token, logout_with_token
from models.user import User, save_user
from repositories.userRepo import get_user
from schemas.user import CreateUser

load_dotenv()

router = APIRouter(tags=["Authentication and Authorization"])

auth = JWTBearer(jwks)

REDIRECT_URI = os.environ.get("REDIRECT_URI")


@router.post("/auth/sign-in")
async def login(code: str, db: Session = Depends(get_db)):
    """
    Function that logs in a user.

    :param code: Authorization code obtained after user login.
    :param db: Database session.
    :return: Access token and expiration time if authentication is successful, otherwise raise an HTTPException.
    """

    # Authenticate user with the code
    token = auth_with_code(code, REDIRECT_URI)
    if token is None:
        raise HTTPException(status_code=401, detail="Error loging in...")
    else:
        # Get user info from the token
        user_info = user_info_with_token(token.get("token"))

        new_user = CreateUser(
            id=user_info["UserAttributes"][4]["Value"],
            given_name=user_info["UserAttributes"][3]["Value"],
            family_name=user_info["UserAttributes"][2]["Value"],
            username=user_info["Username"],
            email=user_info["UserAttributes"][0]["Value"],
        )

        # If the user does not exist, save it
        if not (
            db.query(User).filter(User.username == new_user.username).first()
            or db.query(User).filter(User.email == new_user.email).first()
        ):
            save_user(new_user, db)

        return JSONResponse(status_code=200, content=jsonable_encoder(token))


@router.get("/auth/me", dependencies=[Depends(auth)])
async def current_user(
    username: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Function that returns the current user.

    :param username: Username of the user to get.
    :param db: Database session.
    :return: User object if found, otherwise raise an HTTPException
    """
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(get_user(username=username, db=db)),
    )


@router.get("/auth/logout", dependencies=[Depends(auth)])
async def logout(credentials: JWTAuthorizationCredentials = Depends(auth)):
    """
    Function that logs out a user.

    :param credentials: JWTAuthorizationCredentials object.
    :return: Message if logout is successful, otherwise raise an HTTPException.
    """

    try:
        logout_with_token(credentials.jwt_token)
        return JSONResponse(status_code=200, content="Logout successful")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Error loging out...")
