from pydantic import BaseModel
from typing import Generic, TypeVar

# 제네릭 타입을 정의하여 다양한 데이터 타입을 수용할 수 있게 합니다.
T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """
    Args:
        status_code : 응답 코드
        message : 응답 메시지
        data: 반환 시에 담아 보낼 임의의 데이터
    """
    status_code: int
    message: str
    data: T = None


class SuccessResponse(BaseResponse, Generic[T]):
    status_code: int = 200
    message: str = "Success"


class BadRequestResponse(BaseResponse, Generic[T]):
    status_code: int = 400
    message: str = "Bad Request"


class UnauthorizedResponse(BaseResponse, Generic[T]):
    """401 Unauthorized: 인증 정보 누락 또는 유효하지 않음"""
    status_code: int = 401
    message: str = "Unauthorized"


class ForbiddenResponse(BaseResponse, Generic[T]):
    """403 Forbidden: 접근 권한 없음"""
    status_code: int = 403
    message: str = "Forbidden"


class NotFoundResponse(BaseResponse, Generic[T]):
    """404 Not Found: 요청한 리소스가 존재하지 않음"""
    status_code: int = 404
    message: str = "Not Found"


class ConflictResponse(BaseResponse, Generic[T]):
    """409 Conflict: 리소스 충돌 (예: 중복된 아이디)"""
    status_code: int = 409
    message: str = "Conflict"


class InternalServerErrorResponse(BaseResponse, Generic[T]):
    """500 Internal Server Error: 서버 내부 오류"""
    status_code: int = 500
    message: str = "Internal Server Error"
