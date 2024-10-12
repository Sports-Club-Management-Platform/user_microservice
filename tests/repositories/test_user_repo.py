import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.mysql import MySqlContainer

from db.database import get_db
from main import app
from models.user import User
from repositories.userRepo import get_user_by_username

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
    yield SessionLocal
    my_sql_container.stop()


def test_get_user(session):
    # Use the session to add a test user (if needed)
    db = session()
    test_user = User(username="Username1", password="testpassword")
    db.add(test_user)
    db.commit()

    # Use the repository function to get the user by username
    result = get_user_by_username("Username1", db)

    # Assert that the user was found and is correct
    assert result is not None
    assert result.username == "Username1"
