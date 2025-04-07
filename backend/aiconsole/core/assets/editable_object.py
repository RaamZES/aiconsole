from pydantic import BaseModel


class EditableObject(BaseModel):
    id: str
    name: str
    last_modified: str 