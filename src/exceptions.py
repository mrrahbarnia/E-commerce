from fastapi import HTTPException, status


class CheckDbConnection(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.detail = "Check database connection."
