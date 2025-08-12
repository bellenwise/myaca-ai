from pydantic import BaseModel


class AssignmentAnalysisRequest(BaseModel):
    """
    과제 분석 요청

    Args :
        - acaId :str
        - assignmentId: str
    """
    acaId: str
    assignmentId: str


class GetAssignmentAnalysisRequest(BaseModel):
    """
    과제 분석 조회 요청

     Args :
        - acaId: str
        - assignmentId: str
    """
    acaId: str
    assignmentId: str


class AssignmentRequest(BaseModel):
    """
    과제 분석 요청

    Args :
        - assignmentId: str
    """
    assignmentId: str