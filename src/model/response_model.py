from pydantic import BaseModel
from typing import Generic, TypeVar, Optional ,Any

# 제네릭 타입을 정의하여 다양한 데이터 타입을 수용할 수 있게 합니다.
T = TypeVar('T')

class BaseResponse(BaseModel):
    """모든 API 응답의 기본 구조"""
    status_code: int
    message: str
    data: Optional[Any] = None


class SuccessResponse(BaseResponse, Generic[T]):
    status_code: int = 200
    message: str = "Success"
    data: Optional[T] = None


class BadRequestResponse(BaseResponse, Generic[T]):
    status_code: int = 400
    message: str = "Bad Request"
    data: str = "The request was malformed or invalid."


class UnauthorizedResponse(BaseResponse, Generic[T]):
    """401 Unauthorized: 인증 정보 누락 또는 유효하지 않음"""
    status_code: int = 401
    message: str = "Unauthorized"
    data: str = "Authentication credentials were not provided or are invalid."


class ForbiddenResponse(BaseResponse, Generic[T]):
    """403 Forbidden: 접근 권한 없음"""
    status_code: int = 403
    message: str = "Forbidden"
    data: str = "You do not have permission to access this resource."


class NotFoundResponse(BaseResponse, Generic[T]):
    """404 Not Found: 요청한 리소스가 존재하지 않음"""
    status_code: int = 404
    message: str = "Not Found"
    data: str = "The requested resource was not found."


class ConflictResponse(BaseResponse, Generic[T]):
    """409 Conflict: 리소스 충돌 (예: 중복된 아이디)"""
    status_code: int = 409
    message: str = "Conflict"
    data: str = "The request could not be completed due to a conflict with the current state of the resource."


class InternalServerErrorResponse(BaseResponse, Generic[T]):
    """500 Internal Server Error: 서버 내부 오류"""
    status_code: int = 500
    message: str = "Internal Server Error"
    data: str = "An unexpected error occurred on the server."
