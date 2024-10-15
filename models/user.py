import datetime

from fastapi import Depends
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Session

from db.database import Base, get_db
from schemas.user import CreateUser


class User(Base):
    __tablename__ = "user"

    id = Column(String(50), primary_key=True, index=True)
    given_name = Column(String(200), index=True, nullable=False)
    family_name = Column(String(200), index=True, nullable=False)
    username = Column(String(200), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        index=True,
        default=datetime.datetime.now(),
        nullable=False,
    )


def save_user(new_user: CreateUser, db: Session = Depends(get_db)):
    """
    Save a new user in the database.

    :param new_user: User object to save.
    :param db: Database session.
    :return: User object saved.
    """
    db_user = User(
        id=new_user.id,
        given_name=new_user.given_name,
        family_name=new_user.family_name,
        username=new_user.username,
        email=new_user.email,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
