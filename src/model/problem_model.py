from typing import Union
from pydantic import BaseModel


class ProblemStatsModel(BaseModel):
    """
    문제 통계

    Args :
        - correctRate: str
        - reason: dict
    """
    correctRate: Union[int, None]
    reason: dict


class AssignmentReview(BaseModel):
    """
    과제 통계

    Args :
        - questionId: str
        - reason: Union[str, None]
        - analysis: Union[str, None]
    """
    questionId: str
    reason: Union[str, None]
    analysis: Union[str, None]
