from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class AnalysisResult(BaseModel):
    analysis : str = Field(description="Submission Explanation Result")


class ReasonResult(BaseModel):
    reason : str = Field(description="Reason Categorize Result")


class ChatResult(BaseModel):
    chat : str = Field(description="Question Response")


class GenerateResult(BaseModel):
    generate : str = Field(description="Generate Problem Result")


class TitleResult(BaseModel):
    title : str = Field(description="Title Response")