from fastapi import HTTPException

class URLNotFoundError(HTTPException):
    """當找不到URL時拋出的異常"""
    def __init__(self, detail: str):
        super().__init__(status_code=404, detail=detail)

class URLValidationError(HTTPException):
    """當URL驗證失敗時拋出的異常"""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

class URLServiceError(HTTPException):
    """當URL服務發生錯誤時拋出的異常"""
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=detail) 