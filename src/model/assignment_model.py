from pydantic import BaseModel


class AssignmentAnalysisRequest(BaseModel):
    acaId: str
    assignmentId: str