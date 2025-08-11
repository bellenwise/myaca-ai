from pydantic import BaseModel


class AssignmentAnalysisRequest(BaseModel):
    acaId: str
    assignmentId: str


class GetAssignmentAnalysisRequest(BaseModel):
    acaId: str
    courseId: str
    assignmentId: str