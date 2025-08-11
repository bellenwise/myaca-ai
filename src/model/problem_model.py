from typing import Union

from pydantic import BaseModel


class ProblemStatsModel(BaseModel):
    correctRate: str
    incorrectReason: dict


class AssignmentReview(BaseModel):
    questionId: str
    incorrectReason: Union[str, None]
    analysis: Union[str, None]
