from pydantic import BaseModel


class ProblemStatsModel(BaseModel):
    correctRate: str
    incorrectReason: dict
