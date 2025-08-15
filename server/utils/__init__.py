# server/utils/py_object_id.py
from bson import ObjectId
from pydantic.functional_validators import BeforeValidator
from pydantic.json_schema import WithJsonSchema
from typing import Any
from annotated_types import Annotated

def validate_object_id(v: Any) -> str:
    """
    Validates and converts an ObjectId to a string.
    """
    if isinstance(v, ObjectId):
        return str(v)
    if not ObjectId.is_valid(v):
        raise ValueError("Invalid ObjectId")
    return str(ObjectId(v))

PyObjectId = Annotated[
    str,
    BeforeValidator(validate_object_id),
    WithJsonSchema({"type": "string", "example": "60ddc9732f8fb814c8fddf45"})
]
