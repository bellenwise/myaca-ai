from pydantic import BaseModel


class SubmissionAnalysisRequest(BaseModel):
    acaId: str
    assignmentUuid: str
    problemId: str
