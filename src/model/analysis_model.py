from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    acaId: str
    assignmentUuid: str
    problemId: str
