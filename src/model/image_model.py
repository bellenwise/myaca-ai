from pydantic import BaseModel


class ImageProcessRequest(BaseModel):
    studentId: str
    assignmentUuid: str
    problemId: str
    imageURL: str


class ImageGenerationRequest(BaseModel):
    title: str
    description: str
    style: str