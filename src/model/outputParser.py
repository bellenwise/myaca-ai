from typing import Dict
from pydantic import BaseModel, Field, conlist

class AnalysisResult(BaseModel):
    analysis : str = Field(description="Submission Explanation Result")


class ReasonResult(BaseModel):
    reason : str = Field(description="Reason Categorize Result")


class ChatResult(BaseModel):
    chat : str = Field(description="Question Response")


class GenerateResult(BaseModel):
    category: str = Field(description="Category of the problem")
    name: str = Field(description="Name or title of the problem")
    choices: conlist(str, min_length=1) = Field(description="List of choices for a multiple-choice problem")
    answers: str = Field(description="The correct answer to the problem")
    question: str = Field(description="The problem statement or question")
    tags: conlist(str) = Field(description="List of tags related to the problem")
    type: conlist(str, min_length=1) = Field(description="List of problem types (e.g., 'select', 'multi')")
    imageURL: str = Field(description="URL to an image related to the problem")
    solution: str = Field(description="Detailed solution for the problem")
    problemId: str = Field(description="ID of the problem")


class TitleResult(BaseModel):
    title : str = Field(description="Title Response")


class AssignmentAnalysisResult(BaseModel):
    analysis : str = Field(description="Assignment Analysis Result")
    incorrect_count: int = Field(description="Number of incorrect answers")
    incorrect_reasons: Dict[str, int] = Field(description="IncorrectReason Total Count Map")
    score_avg : float = Field(description="Submission Score Average")
    total_count : int = Field(description="Submission Total Count")