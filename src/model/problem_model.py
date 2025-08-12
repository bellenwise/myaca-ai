from typing import Union
from pydantic import BaseModel


class ProblemStatsModel(BaseModel):
    """
    문제 통계

    Args :
        - correctRate: str
        - incorrectReason: dict
    """
    correctRate: str
    incorrectReason: dict


class AssignmentReview(BaseModel):
    """
    과제 통계

    Args :
        - questionId: str
        - incorrectReason: Union[str, None]
        - analysis: Union[str, None]
    """
    questionId: str
    incorrectReason: Union[str, None]
    analysis: Union[str, None]
