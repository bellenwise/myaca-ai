from pydantic import BaseModel


class ImageProcessRequest(BaseModel):
    acaId: str
    assignmentUuid: str
    problemId: str
