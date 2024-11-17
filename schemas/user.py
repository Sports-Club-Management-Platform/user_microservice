from pydantic import BaseModel


class CreateUser(BaseModel):
    id: str
    name: str
    username: str
    email: str
