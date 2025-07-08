from typing import Dict, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class HttpResponse:
    status_code: int
    message: str
    body: Dict[str, Any]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "message": self.message,
            "body": self.body,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def http_response(message: str, body: Dict[str, Any], status_code: int = 200) -> (HttpResponse):
    return HttpResponse(
        status_code=status_code,
        message=message,
        body=body,
    )

def success_response(message: str = "Success", body: Optional[Dict[str, Any]] = None) -> HttpResponse:
    return http_response(message, body or {}, 200)

def error_response(message: str, error: str, status_code: int = 400, body: Optional[Dict[str, Any]] = None) -> HttpResponse:
    return http_response(message, body or {}, status_code)

def not_found_response(message: str = "Not Found", body: Optional[Dict[str, Any]] = None) -> HttpResponse:
    return http_response(message, body or {}, 404)

def server_error_response(message: str = "Internal Server Error", error: str = "Server Error", body: Optional[Dict[str, Any]] = None) -> HttpResponse:
    return http_response(message, body or {}, 500)

def unauthorized_response(message: str = "Unauthorized", body: Optional[Dict[str, Any]] = None) -> HttpResponse:
    return http_response(message, body or {}, 401)

def forbidden_response(message: str = "Forbidden", body: Optional[Dict[str, Any]] = None) -> HttpResponse:
    return http_response(message, body or {}, 403)
