from pydantic import BaseModel
from typing import Dict


class BaseResponse(BaseModel):
    """
    Args:
        status_code : 응답 코드
        message : 응답 메시지
        data: 반환 시에 담아 보낼 map
    """
    status_code: int
    message: str
    data: Dict[str, any] = None


class SuccessResponse(BaseResponse):
    """200 Success : 성공"""
    status_code: int = 200
    message: str = "Success"


class BadRequestResponse(BaseResponse):
    """400 Bad Request: 잘못된 요청 혹은 유효하지 않은 경로"""
    status_code: int = 400
    message: str = "Bad Request"


class UnauthorizedResponse(BaseResponse):
    """401 Unauthorized: 인증 정보 누락 또는 유효하지 않음"""
    status_code: int = 401
    message: str = "Unauthorized"


class ForbiddenResponse(BaseResponse):
    """403 Forbidden: 접근 권한 없음"""
    status_code: int = 403
    message: str = "Forbidden"


class NotFoundResponse(BaseResponse):
    """404 Not Found: 요청한 리소스가 존재하지 않음"""
    status_code: int = 404
    message: str = "Not Found"


class ConflictResponse(BaseResponse):
    """409 Conflict: 리소스 충돌 (예: 중복된 아이디)"""
    status_code: int = 409
    message: str = "Conflict"


class InternalServerErrorResponse(BaseResponse):
    """500 Internal Server Error: 서버 내부 오류"""
    status_code: int = 500
    message: str = "Internal Server Error"
