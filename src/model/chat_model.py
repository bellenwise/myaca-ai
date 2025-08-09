from pydantic import BaseModel


class ChatRequest(BaseModel):
    acaID: str
    assignmentUuid: str
    problemId: str
    question: str
