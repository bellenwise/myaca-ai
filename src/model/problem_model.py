from typing import Union
from pydantic import BaseModel


class ProblemStatsModel(BaseModel):
    """
    문제 통계

    Args :
        - correctRate: str
        - incorrectReason: dict
    """
    correctRate: Union[int, None]
    incorrectReason: dict


class AssignmentReview(BaseModel):
    """
    과제 통계

    Args :
        - problemID: str
        - incorrectReason: Union[str, None]
        - analysis: Union[str, None]
    """
    problemID: str
    incorrectReason: Union[str, None]
    analysis: Union[str, None]
