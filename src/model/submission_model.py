from pydantic import BaseModel


class SubmissionAnalysisRequest(BaseModel):
    """
    학생 문제풀이 분석 요청

    Args :
        - acaId: str
        - assignmentUuid: str
        - problemId: str
    """
    acaId: str
    assignmentUuid: str
    problemId: str
