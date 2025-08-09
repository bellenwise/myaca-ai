from pydantic import BaseModel
from typing import Union


class ChatRequest(BaseModel):
    acaSubdomain: str
    assignmentUuid: str
    problemId: str
    message: str
    context: Union[list[str], None] = None


class ChatResponse(BaseModel):
    message: str
