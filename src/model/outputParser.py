from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class AnalysisResult(BaseModel):
    analysis : str = Field(description="Submission Explanation Result")


class ReasonResult(BaseModel):
    reason : str = Field(description="Reason Categorize Result")


class ChatResult(BaseModel):
    chat : str = Field(description="Question Response")

