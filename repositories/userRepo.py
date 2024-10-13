from fastapi import HTTPException

from fastapi import Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import save_user, User as UserModel
from schemas.user import CreateUser


def new_user(user: CreateUser, db: Session = Depends(get_db)):
    """
    Create a new user in the database.

    :param user: User object to create.
    :param db: Database session.
    :return: User object created.
    """
    return save_user(new_user=user, db=db)


def get_user_by_username(username: str, db: Session = Depends(get_db)):
    return db.query(UserModel).filter(UserModel.username == username).first()


def get_user(username: str, db: Session = Depends(get_db)):
    """
    Get a user by username.

    :param username: Username of the user to get.
    :param db: Database session.
    :return: User object if found, otherwise raise an HTTPException.
    """
    db_user = get_user_by_username(username, db)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
