import pytest
from unittest.mock import patch
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.mysql import MySqlContainer
from fastapi import HTTPException
from db.database import get_db
from main import app
from models.user import User, save_user
from repositories.userRepo import get_user_by_username, get_user, new_user
from schemas.user import CreateUser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

my_sql_container = MySqlContainer(
    "mysql:8.0",
    root_password="test_root_password",
    dbname="test_db",
    username="test_username",
    password="test_password",
)


@pytest.fixture(name="session", scope="module")
def setup():
    # Start the MySQL container
    my_sql_container.start()
    connection_url = my_sql_container.get_connection_url()
    print(connection_url)
    engine = create_engine(connection_url, connect_args={})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    User.metadata.create_all(engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    logger.info("running setup")
    yield SessionLocal
    logger.info("ending setup")
    my_sql_container.stop()


@pytest.fixture(name="test_db", scope="module")
def create_test_db(session):
    db = session()
    logger.info("creating test db")
    yield db
    logger.info("closing test db")
    db.close()


@pytest.fixture(name="test_user", scope="function")
def create_test_user(test_db):
    test_user = User(
        id="id1",
        name="given_name1",
        username="username1",
        email="email1",
    )
    test_db.add(test_user)
    test_db.commit()
    logger.info("creating test user")
    yield test_user
    logger.info("deleting test user")
    test_db.delete(test_user)
    test_db.commit()


def test_get_user_by_username_found(test_db, test_user):
    found_user = get_user_by_username(test_user.username, test_db)
    assert found_user is not None
    assert found_user.id == "id1"


def test_get_user_by_username_not_found(test_db):
    found_user = get_user_by_username("not_exist", test_db)
    assert found_user is None


@patch("repositories.userRepo.get_user_by_username", wraps=get_user_by_username)
def test_get_user_found(get_user_by_username_function, test_db, test_user):
    found_user = get_user(test_user.username, test_db)
    get_user_by_username_function.assert_called_once_with(test_user.username, test_db)
    assert found_user is not None
    assert found_user.id == "id1"


@patch("repositories.userRepo.get_user_by_username", wraps=get_user_by_username)
def test_get_user_not_found(get_user_by_username_function, test_db):
    found_user = None
    with pytest.raises(HTTPException) as exception:
        found_user = get_user("not_exist", test_db)
    get_user_by_username_function.assert_called_once_with("not_exist", test_db)
    assert found_user is None
    assert exception.value.status_code == 404


@patch("repositories.userRepo.save_user", wraps=save_user)
def test_create_user(save_user_function, test_db):
    user_data = CreateUser(
        id="id2",
        name="given_name2",
        username="username2",
        email="email2",
    )
    user = new_user(user_data, test_db)
    assert user is not None
    assert user == test_db.query(User).filter(User.username == "username2").first()
    assert (
        user.id == "id2"
        and user.name == "given_name2"
        and user.username == "username2"
        and user.email == "email2"
    )
    save_user_function.assert_called_once_with(new_user=user_data, db=test_db)
