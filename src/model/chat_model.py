from pydantic import BaseModel


class ChatRequest(BaseModel):
    acaId: str
    assignmentUuid: str
    problemId: str
    question: str
