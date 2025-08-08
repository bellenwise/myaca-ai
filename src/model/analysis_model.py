from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    userToken: str
    acaID: str
    assignmentUuid: str
    questionNo: str
    message: str
    context: list[str]
