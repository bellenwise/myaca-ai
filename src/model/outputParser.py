from typing import Dict
from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """
    학생 제출물 중 문제 풀이
    """
    analysis : str = Field(description="Submission Explanation Result")


class ReasonResult(BaseModel):
    """
    범주화된 틀린 이유
    - "개념 부족"
    - "적용 오류"
    - "문제 해석 오류"
    - "정보 누락/오독"
    - "계산 실수"
    - "논리적 오류"
    - "선택지 오해"
    - "추론 실패"
    - "오타"
    """
    reason : str = Field(description="Reason Categorize Result")


class ChatResult(BaseModel):
    """
    학생 LLM Response
    """
    chat : str = Field(description="Question Response")


class GenerateResult(BaseModel):
    """
    비슷한 문제 생성 결과물
    """
    category: str = Field(description="Category of the problem")
    name: str = Field(description="Name or title of the problem")
    choices: list[str] = Field(description="List of choices for a multiple-choice problem")
    answers: str = Field(description="The correct answer to the problem")
    question: str = Field(description="The problem statement or question")
    tags: list[str] = Field(description="List of tags related to the problem")
    type: str = Field(description="List of problem types (e.g., 'select', 'multi', 'subjective')")
    imageURL: str = Field(description="URL to an image related to the problem")
    solution: str = Field(description="Detailed solution for the problem")
    problemId: str = Field(description="ID of the problem")


class TitleResult(BaseModel):
    """
    비슷한 문제 생성 제목 추천
    """
    title : str = Field(description="Title Response")


class ModifyResult(BaseModel):
    """
    image2text raw text 수정 결과
    """
    text: str = Field(description="validated_text")


class ValidResult(BaseModel):
    """
    학생 문제 풀이 텍스트 변환 결과 유효성 판단
    """
    validity: bool = Field(description="True or False")

      
class AssignmentAnalysisResult(BaseModel):
    """
    과제 분석 결과
    """
    analysis : str = Field(description="Assignment Analysis Result")

