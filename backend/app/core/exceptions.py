"""Custom exceptions and error handlers."""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception with consistent error format."""

    def __init__(self, status_code: int, code: int, message: str, detail: str = ""):
        super().__init__(status_code=status_code, detail={"code": code, "message": message, "detail": detail})
        self.app_code = code
        self.app_message = message


class UnauthorizedException(AppException):
    def __init__(self, message: str = "未登录或登录已过期"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, code=401, message=message)


class ForbiddenException(AppException):
    def __init__(self, message: str = "无权访问"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, code=403, message=message)


class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, code=404, message=message)


class BadRequestException(AppException):
    def __init__(self, message: str = "请求参数错误"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, code=400, message=message)


class TooManyRequestsException(AppException):
    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, code=429, message=message)
