from pydantic import BaseModel


class ImageProcessRequest(BaseModel):
    """
    학생 제출 풀이 이미지 처리 요청

    Args :
        - studentId: str
        - assignmentUuid: str
        - problemId: str
        - imageURL: str
    """
    acaId: str
    studentId: str
    assignmentUuid: str
    problemId: str
    imageURL: str


class ImageGenerationRequest(BaseModel):
    """
    랜딩페이지 이미지 생성 요청

    Args :
        - title: str
        - description: str
        - style: str
    """
    title: str
    description: str
    style: str