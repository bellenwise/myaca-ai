from pydantic import BaseModel


class ChatRequest(BaseModel):
    userToken: str
    assignmentUuid: str
    questionNo: str
    message: str
    context: list[str]
